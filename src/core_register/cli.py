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


def _cmd_baselines(args: argparse.Namespace) -> int:
    from core_register.config import load_baseline_config
    from core_register.preprocessing.text import lexical_view
    from core_register.training.tracking import git_state

    cfg = load_data_config(args.config)
    exp = load_baseline_config(args.experiment)
    try:
        hashes = verify_source_files(cfg)
    except SourceIntegrityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    git = git_state()
    run_id = time.strftime("%Y%m%dT%H%M%S") + "-" + (git["commit"][:7] or "nogit")
    run_dir = args.runs_dir / f"T1_lexical_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)  # never overwrite a run
    schema = load_label_schema(cfg.label_schema)
    lx = exp.lexical

    def view(text: str) -> str:
        return lexical_view(text, exp.window_words, unicode=lx.unicode, lowercase=lx.lowercase,
                            mask_urls_emails=lx.mask_urls_emails)

    try:
        return _run_baselines(args, cfg, exp, hashes, git, run_id, run_dir, schema, view)
    except Exception as exc:  # record failed runs instead of leaving an unexplained directory
        (run_dir / "FAILED.json").write_text(
            json.dumps({"run_id": run_id, "git": git, "error": f"{type(exc).__name__}: {exc}"}, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        raise


def _run_baselines(args: argparse.Namespace, cfg: Any, exp: Any, hashes: dict[str, str], git: dict[str, Any],
                   run_id: str, run_dir: Path, schema: Any, view: Any) -> int:
    import joblib
    import numpy as np
    import pandas as pd

    from core_register.data.tasks import load_t1
    from core_register.training.lexical import constant_baselines, run_linear_grid
    from core_register.training.tracking import RunTimer, environment

    with RunTimer() as timer:
        data = load_t1(cfg, schema, args.split_manifest, ["train", "dev"], view)
        train, dev = data["train"], data["dev"]
        b0 = constant_baselines(train, dev)
        grid, best = run_linear_grid(train, dev, exp)
        selected: dict[str, Any] = {}
        for family, cand in best.items():
            model_path = run_dir / f"B{1 if family == 'logreg' else 2}_{family}.joblib"
            joblib.dump(cand.pipeline, model_path)
            reloaded = joblib.load(model_path)
            fresh = (reloaded.predict_proba(dev.texts) if family == "logreg"
                     else reloaded.decision_function(dev.texts))
            parity = bool(np.allclose(fresh, cand.dev_scores, atol=1e-6))
            if not parity:
                print(f"error: save/load parity failed for {family}", file=sys.stderr)
                return 4
            preds = cand.thresholds.apply(cand.dev_scores)
            frame = pd.DataFrame({"doc_id": dev.doc_ids})
            for j, lab in enumerate(dev.labels):
                frame[f"gold_{lab}"] = dev.y[:, j]
                frame[f"score_{lab}"] = cand.dev_scores[:, j]
                frame[f"pred_{lab}"] = preds[:, j]
            pred_path = run_dir / f"dev_predictions_{family}.parquet"
            frame.to_parquet(pred_path, index=False)
            selected[family] = {
                "params": cand.params,
                "score_type": "probability" if family == "logreg" else "svm_margin (not a probability)",
                "thresholds": cand.thresholds.to_dict(dev.labels),
                "dev_tuned": cand.tuned,
                "dev_default_threshold": cand.untuned,
                "model_path": model_path.as_posix(),
                "model_sha256": sha256_file(model_path),
                "dev_predictions_path": pred_path.as_posix(),
                "dev_predictions_sha256": sha256_file(pred_path),
                "save_load_parity": parity,
            }
    manifest = {
        "run_id": run_id,
        "task": "T1", "cohort": "functional", "split": "controlled", "partitions_used": ["train", "dev"],
        "test_inference": False,
        "git": git,
        "source_sha256": hashes,
        "split_manifest_sha256": sha256_file(args.split_manifest),
        "label_schema_version": schema.version,
        "experiment_config_file": args.experiment.as_posix(),
        "experiment_config": exp.model_dump(mode="json"),
        "environment": environment(),
        "timing": timer.to_dict(),
        "n_train": len(train.doc_ids), "n_dev": len(dev.doc_ids),
        "selection": "dev macro-F1 after threshold tuning (thresholds and selection both use dev: dev scores are "
                     "optimistic; the test set stays sealed)",
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    report = {"run": manifest, "B0": b0, "grid": grid, "selected": selected}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {args.report} and {run_dir}", file=sys.stderr)
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
    base = sub.add_parser("baselines", help="B0-B2 lexical baselines on T1 (train fit, dev selection; no test)")
    base.add_argument("--config", type=Path, required=True, help="data config YAML")
    base.add_argument("--experiment", type=Path, required=True, help="baseline experiment YAML")
    base.add_argument("--split-manifest", type=Path, default=Path("data/manifests/splits/split_manifest.csv"))
    base.add_argument("--runs-dir", type=Path, default=Path("artifacts/runs"))
    base.add_argument("--report", type=Path, default=Path("reports/baselines/T1_dev_lexical.json"))
    base.set_defaults(func=_cmd_baselines)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rc: int = args.func(args)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
