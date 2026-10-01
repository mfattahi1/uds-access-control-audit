from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import Observation, Probe


class AuditTransport(ABC):
    """Minimal interface required by the scan runner."""

    mode_name = "unknown"

    def __enter__(self) -> "AuditTransport":
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    @abstractmethod
    def open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_phase(self, phase: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def restore_baseline(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def execute(self, probe: Probe) -> Observation:
        raise NotImplementedError


class MockTransport(AuditTransport):
    """Deterministic demo transport; requires no CAN hardware or third-party packages."""

    mode_name = "mock"

    def __init__(self) -> None:
        self.phase = "pre"
        self._opened = False

    def open(self) -> None:
        self._opened = True

    def close(self) -> None:
        self._opened = False

    def set_phase(self, phase: str) -> None:
        if phase not in {"pre", "post"}:
            raise ValueError("phase must be 'pre' or 'post'")
        self.phase = phase

    def restore_baseline(self) -> None:
        if not self._opened:
            raise RuntimeError("transport is not open")

    def execute(self, probe: Probe) -> Observation:
        if not self._opened:
            raise RuntimeError("transport is not open")

        if probe.probe_id == "dsc_default":
            return Observation(probe.probe_id, probe.label, probe.service, "POSITIVE")

        if self.phase == "pre":
            return Observation(
                probe.probe_id,
                probe.label,
                probe.service,
                "NEGATIVE",
                "SecurityAccessDenied",
            )

        return Observation(probe.probe_id, probe.label, probe.service, "POSITIVE")


class UdsoncanSocketCanTransport(AuditTransport):
    """
    Optional SocketCAN / ISO-TP transport.

    Imports are intentionally lazy so mock mode works without automotive packages.
    Only response categories are returned; raw ECU payloads are not persisted.
    """

    mode_name = "socketcan"

    def __init__(
        self,
        channel: str,
        tx_id: int,
        rx_id: int,
        *,
        can_fd: bool = True,
        request_timeout: float = 2.0,
    ) -> None:
        self.channel = channel
        self.tx_id = tx_id
        self.rx_id = rx_id
        self.can_fd = can_fd
        self.request_timeout = request_timeout
        self.phase = "pre"
        self.bus: Any = None
        self.stack: Any = None
        self.connection: Any = None
        self.client: Any = None
        self._exceptions: dict[str, type[BaseException]] = {}

    def open(self) -> None:
        try:
            import can
            import isotp
            from udsoncan.client import Client
            from udsoncan.connections import PythonIsoTpConnection
            from udsoncan.exceptions import (
                InvalidResponseException,
                NegativeResponseException,
                TimeoutException,
                UnexpectedResponseException,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Hardware mode requires optional dependencies. Install with: pip install -e '.[hardware]'"
            ) from exc

        self._exceptions = {
            "negative": NegativeResponseException,
            "invalid": InvalidResponseException,
            "unexpected": UnexpectedResponseException,
            "timeout": TimeoutException,
        }

        # The caller supplies all target identifiers. No OEM or project-specific IDs are embedded here.
        self.bus = can.Bus(
            interface="socketcan",
            channel=self.channel,
            fd=self.can_fd,
            receive_own_messages=False,
        )
        address = isotp.Address(
            isotp.AddressingMode.Normal_29bits,
            txid=self.tx_id,
            rxid=self.rx_id,
        )
        self.stack = isotp.CanStack(
            bus=self.bus,
            address=address,
            params={
                "tx_data_length": 64 if self.can_fd else 8,
                "can_fd": self.can_fd,
                "bitrate_switch": self.can_fd,
                "blocking_send": True,
                "tx_data_min_length": 8,
            },
        )
        self.connection = PythonIsoTpConnection(self.stack, name="uds-access-control-audit")
        self.client = Client(
            self.connection,
            request_timeout=self.request_timeout,
            config={
                "p2_timeout": 1.0,
                "p2_star_timeout": 5.0,
                "exception_on_negative_response": True,
            },
        )
        self.client.open()

    def close(self) -> None:
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
        if self.stack is not None:
            try:
                self.stack.stop()
            except Exception:
                pass
        if self.bus is not None:
            try:
                self.bus.shutdown()
            except Exception:
                pass

    def set_phase(self, phase: str) -> None:
        if phase not in {"pre", "post"}:
            raise ValueError("phase must be 'pre' or 'post'")
        self.phase = phase

    def restore_baseline(self) -> None:
        if self.client is None:
            raise RuntimeError("transport is not open")
        try:
            self.client.change_session(0x01)
        except Exception:
            # Baseline restore is best-effort: the probe result itself remains the evidence.
            pass

    def execute(self, probe: Probe) -> Observation:
        if self.client is None:
            raise RuntimeError("transport is not open")

        try:
            if probe.kind == "session":
                response = self.client.change_session(probe.value)
            elif probe.kind == "seed":
                response = self.client.request_seed(probe.value)
            else:
                raise ValueError(f"Unsupported probe kind: {probe.kind}")

            if response is not None and getattr(response, "positive", False):
                return Observation(probe.probe_id, probe.label, probe.service, "POSITIVE")
            detail = getattr(response, "code_name", "NegativeResponse") if response is not None else "NoResponse"
            return Observation(probe.probe_id, probe.label, probe.service, "NEGATIVE", str(detail))

        except self._exceptions["negative"] as exc:
            detail = getattr(exc.response, "code_name", "NegativeResponse")
            return Observation(probe.probe_id, probe.label, probe.service, "NEGATIVE", str(detail))
        except self._exceptions["timeout"]:
            return Observation(probe.probe_id, probe.label, probe.service, "TIMEOUT")
        except (self._exceptions["invalid"], self._exceptions["unexpected"]) as exc:
            return Observation(probe.probe_id, probe.label, probe.service, "PROTOCOL_ERROR", type(exc).__name__)
        except Exception as exc:
            return Observation(probe.probe_id, probe.label, probe.service, "ERROR", type(exc).__name__)
