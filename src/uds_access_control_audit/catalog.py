from .models import Probe


def default_catalog() -> list[Probe]:
    """Return the intentionally small, non-destructive public probe catalog."""
    return [
        Probe(
            probe_id="dsc_default",
            label="Default Session",
            service="DiagnosticSessionControl (0x10)",
            request_hex="10 01",
            kind="session",
            value=0x01,
        ),
        Probe(
            probe_id="dsc_extended",
            label="Extended Session",
            service="DiagnosticSessionControl (0x10)",
            request_hex="10 03",
            kind="session",
            value=0x03,
        ),
        Probe(
            probe_id="security_seed_l1",
            label="SecurityAccess seed request",
            service="SecurityAccess (0x27)",
            request_hex="27 01",
            kind="seed",
            value=1,
        ),
    ]
