"""Command-line interface: ``python -m core_register.cli <command> ...``.

Run from the repository root (config paths are relative to it).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from core_register.config import load_data_config
from core_register.data.audit import run_audit
from core_register.data.validate import SourceIntegrityError


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="core_register", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="verify source hashes and report corpus counts (no text)")
    audit.add_argument("--config", type=Path, required=True, help="data config YAML")
    audit.add_argument("--out", type=Path, default=None, help="write JSON here instead of stdout")
    audit.set_defaults(func=_cmd_audit)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rc: int = args.func(args)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
