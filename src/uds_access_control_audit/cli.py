from __future__ import annotations

import argparse
from pathlib import Path

from .catalog import default_catalog
from .compare import compare_reports
from .reporters import (
    read_scan_json,
    write_comparison_csv,
    write_comparison_json,
    write_scan_json,
)
from .runner import run_scan
from .transports import MockTransport, UdsoncanSocketCanTransport


def int_auto(value: str) -> int:
    return int(value, 0)


def make_transport(args: argparse.Namespace):
    if args.mode == "mock":
        return MockTransport()
    if args.tx_id is None or args.rx_id is None:
        raise SystemExit("socketcan mode requires --tx-id and --rx-id")
    return UdsoncanSocketCanTransport(
        channel=args.channel,
        tx_id=args.tx_id,
        rx_id=args.rx_id,
        can_fd=not args.classic_can,
        request_timeout=args.timeout,
    )


def print_scan(report) -> None:
    print(f"\n[{report.phase.upper()}] {report.mode}")
    for item in report.observations:
        print(f"  {item.label:<32} {item.display}")


def print_comparison(rows) -> None:
    print("\nComparison")
    print(f"{'Probe':<32} {'PRE':<32} {'POST':<32} Change")
    print("-" * 116)
    for row in rows:
        print(f"{row.label:<32} {row.pre:<32} {row.post:<32} {row.change}")


def add_transport_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=["mock", "socketcan"], default="mock")
    parser.add_argument("--channel", default="can0", help="SocketCAN channel")
    parser.add_argument("--tx-id", type=int_auto, help="Tester -> ECU CAN identifier")
    parser.add_argument("--rx-id", type=int_auto, help="ECU -> tester CAN identifier")
    parser.add_argument("--classic-can", action="store_true", help="Use classic CAN instead of CAN FD")
    parser.add_argument("--timeout", type=float, default=2.0, help="UDS request timeout in seconds")


def cmd_scan(args: argparse.Namespace) -> int:
    transport = make_transport(args)
    with transport:
        report = run_scan(transport, default_catalog(), args.phase)
    write_scan_json(report, args.output)
    print_scan(report)
    print(f"\nSaved: {args.output}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    pre = read_scan_json(args.pre_report)
    post = read_scan_json(args.post_report)
    rows = compare_reports(pre, post)
    out_dir = Path(args.output_dir)
    json_path = write_comparison_json(rows, out_dir / "comparison.json")
    csv_path = write_comparison_csv(rows, out_dir / "comparison.csv")
    print_comparison(rows)
    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    transport = make_transport(args)

    with transport:
        pre = run_scan(transport, default_catalog(), "pre")
        write_scan_json(pre, out_dir / "pre.json")
        print_scan(pre)

        if args.mode == "socketcan":
            print(
                "\nPerform the approved authentication step using your authorized lab tooling.\n"
                "This public project does not implement OEM/project-specific authentication."
            )
            input("Press Enter when the target is ready for the post-auth scan...")

        post = run_scan(transport, default_catalog(), "post")
        write_scan_json(post, out_dir / "post.json")
        print_scan(post)

    rows = compare_reports(pre, post)
    write_comparison_json(rows, out_dir / "comparison.json")
    write_comparison_csv(rows, out_dir / "comparison.csv")
    print_comparison(rows)
    print(f"\nReports saved under: {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uds-audit",
        description="Compare limited UDS service accessibility before and after an authorized authentication step.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Run one scan phase")
    add_transport_args(scan)
    scan.add_argument("--phase", choices=["pre", "post"], required=True)
    scan.add_argument("--output", required=True)
    scan.set_defaults(func=cmd_scan)

    compare = sub.add_parser("compare", help="Compare two saved scan reports")
    compare.add_argument("pre_report")
    compare.add_argument("post_report")
    compare.add_argument("--output-dir", default="reports/compare")
    compare.set_defaults(func=cmd_compare)

    audit = sub.add_parser("audit", help="Run pre and post scans on the same transport")
    add_transport_args(audit)
    audit.add_argument("--output-dir", default="reports/audit")
    audit.set_defaults(func=cmd_audit)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
