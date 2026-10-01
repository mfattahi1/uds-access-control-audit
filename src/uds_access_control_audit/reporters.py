from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .models import ComparisonRow, ScanReport


def write_scan_json(report: ScanReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return target


def read_scan_json(path: str | Path) -> ScanReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ScanReport.from_dict(data)


def write_comparison_json(rows: list[ComparisonRow], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps([asdict(row) for row in rows], indent=2) + "\n", encoding="utf-8")
    return target


def write_comparison_csv(rows: list[ComparisonRow], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["probe_id", "label", "pre", "post", "change"])
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    return target
