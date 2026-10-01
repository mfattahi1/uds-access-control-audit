from __future__ import annotations

from collections.abc import Iterable

from .models import Observation, Probe, ScanReport
from .transports import AuditTransport


def run_scan(
    transport: AuditTransport,
    probes: Iterable[Probe],
    phase: str,
    *,
    restore_before_each: bool = True,
) -> ScanReport:
    transport.set_phase(phase)
    observations: list[Observation] = []

    for probe in probes:
        if restore_before_each:
            transport.restore_baseline()
        observations.append(transport.execute(probe))

    return ScanReport.create(phase=phase, mode=transport.mode_name, observations=observations)
