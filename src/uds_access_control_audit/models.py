from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Probe:
    probe_id: str
    label: str
    service: str
    request_hex: str
    kind: str
    value: int


@dataclass(frozen=True)
class Observation:
    probe_id: str
    label: str
    service: str
    outcome: str
    detail: str = ""

    @property
    def display(self) -> str:
        return self.outcome if not self.detail else f"{self.outcome}:{self.detail}"


@dataclass
class ScanReport:
    phase: str
    mode: str
    observations: list[Observation]
    created_at: str
    schema_version: int = 1

    @classmethod
    def create(cls, phase: str, mode: str, observations: list[Observation]) -> "ScanReport":
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return cls(phase=phase, mode=mode, observations=observations, created_at=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "phase": self.phase,
            "mode": self.mode,
            "observations": [asdict(item) for item in self.observations],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanReport":
        return cls(
            phase=data["phase"],
            mode=data.get("mode", "unknown"),
            created_at=data.get("created_at", ""),
            schema_version=int(data.get("schema_version", 1)),
            observations=[Observation(**item) for item in data.get("observations", [])],
        )


@dataclass(frozen=True)
class ComparisonRow:
    probe_id: str
    label: str
    pre: str
    post: str
    change: str
