"""Command-line interface: ``python -m core_register.cli <command> ...``.

Run from the repository root (config paths are relative to it).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections.abc import Iterator, Sequence
from pathlib import Path

from core_register.config import SPLITS, load_data_config, load_dedup_config
from core_register.data.audit import run_audit
from core_register.data.deduplicate import build_report, group_documents, manifest_rows
from core_register.data.ingest import Record, iter_records
from core_register.data.labels import load_label_schema
from core_register.data.validate import SourceIntegrityError, sha256_file, verify_source_files


def _cmd_audit(args: argparse.Namespace) -> int:
    cfg = load_data_config(args.config)
    try:
        result = run_audit(cfg)
    except SourceIntegrityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out is None:
        sys.stdout.write(payload)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


def _cmd_dedup(args: argparse.Namespace) -> int:
    cfg = load_data_config(args.config)
    dcfg = load_dedup_config(args.dedup_config)
    try:
        hashes = verify_source_files(cfg)  # before any corpus file is read
    except SourceIntegrityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    schema = load_label_schema(cfg.label_schema)

    def source() -> Iterator[Record]:
        for split in SPLITS:
            yield from iter_records(cfg.split_path(split), split, schema)

    start = time.perf_counter()
    result = group_documents(source, dcfg)
    report = build_report(result, dcfg)

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    rows = manifest_rows(result)
    with args.manifest.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["doc_id"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "source_sha256": hashes,
        "dedup_config_file": args.dedup_config.as_posix(),
        "manifest": {"path": args.manifest.as_posix(), "sha256": sha256_file(args.manifest), "rows": len(rows)},
        **report,
        "runtime_seconds": round(time.perf_counter() - start, 1),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {args.report} and {args.manifest}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="core_register", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="verify source hashes and report corpus counts (no text)")
    audit.add_argument("--config", type=Path, required=True, help="data config YAML")
    audit.add_argument("--out", type=Path, default=None, help="write JSON here instead of stdout")
    audit.set_defaults(func=_cmd_audit)
    dedup = sub.add_parser("dedup", help="group exact and near-duplicate documents (D-07); IDs and counts only")
    dedup.add_argument("--config", type=Path, required=True, help="data config YAML")
    dedup.add_argument("--dedup-config", type=Path, required=True, help="frozen dedup policy YAML")
    dedup.add_argument("--report", type=Path, default=Path("reports/dedup/dedup_report.json"))
    dedup.add_argument("--manifest", type=Path, default=Path("artifacts/dedup/groups.csv"))
    dedup.set_defaults(func=_cmd_dedup)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rc: int = args.func(args)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
