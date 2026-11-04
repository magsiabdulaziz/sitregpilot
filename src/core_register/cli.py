"""Command-line interface: ``python -m core_register.cli <command> ...``.

Run from the repository root (config paths are relative to it).
"""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import sys
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from core_register.config import SPLITS, load_data_config, load_dedup_config, load_split_config
from core_register.data.audit import run_audit
from core_register.data.deduplicate import build_report, group_documents, manifest_rows
from core_register.data.ingest import Record, iter_records
from core_register.data.labels import load_label_schema
from core_register.data.splits import MANIFEST_FIELDS, build_split_manifest
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


def _cmd_split(args: argparse.Namespace) -> int:
    cfg = load_data_config(args.config)
    scfg = load_split_config(args.split_config)
    try:
        hashes = verify_source_files(cfg)
    except SourceIntegrityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    dedup_report = json.loads(args.dedup_report.read_text(encoding="utf-8"))
    groups_path = Path(dedup_report["manifest"]["path"])
    if not groups_path.is_file() or sha256_file(groups_path) != dedup_report["manifest"]["sha256"]:
        print(f"error: {groups_path} missing or not the manifest recorded in {args.dedup_report}; "
              "re-run `dedup` first", file=sys.stderr)
        return 2
    if dedup_report["source_sha256"] != hashes:
        print("error: the dedup report was produced from different source files", file=sys.stderr)
        return 2
    with groups_path.open(encoding="utf-8", newline="") as f:
        group_of = {row["doc_id"]: row["group_id"] for row in csv.DictReader(f)}
    schema = load_label_schema(cfg.label_schema)

    def records() -> Iterator[Record]:
        for split in SPLITS:
            yield from iter_records(cfg.split_path(split), split, schema)

    rows, report = build_split_manifest(records(), group_of, schema, scfg)
    if not all(v for k, v in report["assertions"].items() if not k.endswith("violations")):
        print(f"error: split assertions failed: {report['assertions']}", file=sys.stderr)
        return 3
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "source_sha256": hashes,
        "split_config_file": args.split_config.as_posix(),
        "split_config": scfg.model_dump(mode="json"),
        "dedup_report": {"path": args.dedup_report.as_posix(), "sha256": sha256_file(args.dedup_report)},
        "dedup_groups_sha256": dedup_report["manifest"]["sha256"],
        "manifest": {"path": args.manifest.as_posix(), "sha256": sha256_file(args.manifest), "rows": len(rows)},
        **report,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {args.report} and {args.manifest}", file=sys.stderr)
    return 0


def _cmd_features(args: argparse.Namespace) -> int:
    import math

    import spacy

    from core_register.features.extract import EXTRACTOR_VERSION, extract_to_cache, feature_ids, features_from_counts
    from core_register.features.extract import read_cache as read_feature_cache
    from core_register.features.registry import REGISTRY_VERSION, validate_registry

    validate_registry()
    cfg = load_data_config(args.config)
    try:
        hashes = verify_source_files(cfg)
    except SourceIntegrityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    with args.split_manifest.open(encoding="utf-8", newline="") as f:
        partition = {r["doc_id"]: r["controlled_partition"] for r in csv.DictReader(f)}
    schema = load_label_schema(cfg.label_schema)
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    model = f"{nlp.meta['lang']}_{nlp.meta['name']}-{nlp.meta['version']}"
    cache = args.cache_dir / EXTRACTOR_VERSION / "counts.jsonl"

    def docs() -> Iterator[tuple[str, str]]:
        for split in SPLITS:
            for rec in iter_records(cfg.split_path(split), split, schema):
                if rec.status.value == "OK":
                    yield rec.doc_id, rec.text

    start = time.perf_counter()
    stats = extract_to_cache(docs(), nlp, cache, args.window_words, n_process=args.n_process,
                             batch_size=args.batch_size)
    rows = read_feature_cache(cache)
    # Descriptive statistics on train and dev only: the test set is sealed (extracted, never inspected).
    summary: dict[str, Any] = {}
    for part in ("train", "dev"):
        ids = [i for i, p in partition.items() if p == part and i in rows]
        missing = {fid: 0 for fid in feature_ids()}
        for i in ids:
            for fid, v in features_from_counts(rows[i]["counts"]).items():
                missing[fid] += math.isnan(v)
        summary[part] = {
            "n_extracted": len(ids),
            "n_truncated": sum(rows[i]["truncated"] for i in ids),
            "missing_rate": {k: round(v / len(ids), 4) for k, v in missing.items()} if ids else {},
        }
    n_test = sum(1 for i, p in partition.items() if p == "test" and i in rows)
    report = {
        "source_sha256": hashes,
        "extractor_version": EXTRACTOR_VERSION,
        "registry_version": REGISTRY_VERSION,
        "spacy_model": model,
        "spacy_version": importlib.metadata.version("spacy"),
        "disabled_pipes": ["ner"],
        "window_ws_words": args.window_words,
        "cache": {"path": cache.as_posix(), "sha256": sha256_file(cache), "rows": len(rows)},
        "run": {**stats, "seconds": round(time.perf_counter() - start, 1),
                "n_process": args.n_process, "batch_size": args.batch_size},
        "extraction_failures": 0,
        "controlled_train_dev": summary,
        "controlled_test": {"n_extracted": n_test, "note": "sealed: no descriptive statistics reported"},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {args.report}; cache {cache}", file=sys.stderr)
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
    split = sub.add_parser("split", help="build released/controlled split manifests and seal test (D-07)")
    split.add_argument("--config", type=Path, required=True, help="data config YAML")
    split.add_argument("--split-config", type=Path, required=True, help="split protocol YAML")
    split.add_argument("--dedup-report", type=Path, default=Path("reports/dedup/dedup_report.json"))
    split.add_argument("--report", type=Path, default=Path("reports/splits/split_report.json"))
    split.add_argument("--manifest", type=Path, default=Path("data/manifests/splits/split_manifest.csv"))
    split.set_defaults(func=_cmd_split)
    feats = sub.add_parser("features", help="cached spaCy feature extraction (methodology section 6)")
    feats.add_argument("--config", type=Path, required=True, help="data config YAML")
    feats.add_argument("--split-manifest", type=Path, default=Path("data/manifests/splits/split_manifest.csv"))
    feats.add_argument("--cache-dir", type=Path, default=Path("artifacts/features"))
    feats.add_argument("--report", type=Path, default=Path("reports/features/extraction_report.json"))
    feats.add_argument("--window-words", type=int, default=1000, help="D-06 window")
    feats.add_argument("--n-process", type=int, default=1)
    feats.add_argument("--batch-size", type=int, default=32)
    feats.set_defaults(func=_cmd_features)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rc: int = args.func(args)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
