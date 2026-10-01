# UDS Access Control Audit

A vendor-neutral Python portfolio project for comparing **non-destructive UDS service accessibility before and after an authorized authentication step**.

This repository is a public-safe rewrite of ideas developed during hands-on ECU security testing. It intentionally avoids OEM certificates, proprietary authentication routines, real vehicle identifiers, captured ECU payloads, brute-force logic, fuzzing, flashing, write operations, and destructive diagnostics.

## What it demonstrates

- Python CLI design and structured reporting
- UDS diagnostic service testing with `udsoncan`
- CAN / ISO-TP integration through SocketCAN
- Test isolation by restoring a baseline diagnostic session between probes
- Before/after access-control comparison
- JSON and CSV reports
- Mock mode for reproducible demos without ECU hardware
- Unit tests for the comparison logic

## Scope

The default test catalog contains only three limited probes:

| Probe | UDS service | Purpose |
|---|---|---|
| Default Session | `0x10 0x01` | Verify baseline diagnostic access |
| Extended Session | `0x10 0x03` | Observe whether extended diagnostics are gated |
| SecurityAccess seed request | `0x27 0x01` | Observe service availability without attempting key calculation |

The tool **does not** calculate security keys, bypass authentication, brute-force access, write DIDs, clear DTCs, reset ECUs, request downloads, flash firmware, or fuzz services.

## Quick demo — no hardware required

```bash
python -m uds_access_control_audit audit --mode mock --output-dir reports/demo
```

Mock mode simulates a target where extended diagnostics and the seed request are unavailable before authorization and available afterwards. It produces:

```text
reports/demo/pre.json
reports/demo/post.json
reports/demo/comparison.json
reports/demo/comparison.csv
```

You can also run the two phases separately:

```bash
python -m uds_access_control_audit scan --mode mock --phase pre  --output reports/pre.json
python -m uds_access_control_audit scan --mode mock --phase post --output reports/post.json
python -m uds_access_control_audit compare reports/pre.json reports/post.json --output-dir reports/compare
```

## Authorized lab use with SocketCAN

Install the optional hardware dependencies:

```bash
pip install -e '.[hardware]'
```

Run a baseline scan using your own lab identifiers:

```bash
uds-audit scan \
  --mode socketcan \
  --channel vcan0 \
  --tx-id 0x123 \
  --rx-id 0x456 \
  --phase pre \
  --output reports/pre.json
```

For a before/after comparison on a real authorized ECU, use `audit`:

```bash
uds-audit audit \
  --mode socketcan \
  --channel can0 \
  --tx-id 0x123 \
  --rx-id 0x456 \
  --output-dir reports/lab
```

The tool runs the **pre** phase, then pauses while you perform authentication using your organization's approved tooling. Press Enter to continue with the **post** phase on the same diagnostic connection.

> Authentication itself is deliberately outside this public repository because those routines are often OEM- or project-specific.

## Example comparison

```text
Probe                         PRE                         POST                        Change
----------------------------------------------------------------------------------------------------
Default Session               POSITIVE                    POSITIVE                    unchanged
Extended Session              NEGATIVE:SecurityAccessDenied POSITIVE                 opened_after_auth
SecurityAccess seed request   NEGATIVE:SecurityAccessDenied POSITIVE                 opened_after_auth
```

## Design notes

### Test isolation

A common source of misleading diagnostic results is letting one probe change ECU state for the next probe. Before each catalog test, the hardware transport attempts to restore the default diagnostic session. This does not make every ECU stateless, but it reduces accidental cross-test coupling and makes the intent explicit.

### Minimal data collection

Reports store outcome categories and response-code names. Raw response payloads are not persisted by default. This helps keep reports useful for access-control analysis without collecting ECU-specific data unnecessarily.

### Authentication boundary

The project models authentication as an external, authorized transition. Mock mode simulates that transition; hardware mode pauses so approved tooling can perform it. This keeps the public code vendor-neutral and avoids publishing proprietary authentication material.

## Project structure

```text
src/uds_access_control_audit/
├── cli.py             # command-line interface
├── compare.py         # before/after comparison
├── models.py          # report data structures
├── reporters.py       # JSON/CSV output
├── runner.py          # scan orchestration
├── catalog.py         # non-destructive test catalog
└── transports.py      # mock + optional SocketCAN/ISO-TP transports

tests/
├── test_compare.py
└── test_mock_audit.py
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Ethics and authorization

Use this project only on systems you own or are explicitly authorized to test. Vehicle diagnostics can affect safety-critical systems; use an isolated lab setup and follow the applicable engineering and safety procedures.

## License

MIT
