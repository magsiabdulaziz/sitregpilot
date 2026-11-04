"""Corpus audit built on the package ingest path.

Produces counts only: no text, no per-document records. Its numbers must match
the stdlib reference audit (``scripts/phase1_corpus_audit.py``; integration test).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from core_register.config import SPLITS, DataConfig
from core_register.data.ingest import Status, iter_records
from core_register.data.labels import LabelSchema, load_label_schema
from core_register.data.validate import verify_source_files


def run_audit(cfg: DataConfig, schema: LabelSchema | None = None) -> dict[str, Any]:
    observed_hashes = verify_source_files(cfg)  # before any corpus file is read
    schema = schema or load_label_schema(cfg.label_schema)
    main = set(schema.main)
    sub = set(schema.sub)

    seen_ids: set[str] = set()
    duplicate_ids = 0
    label_sets: Counter[tuple[str, ...]] = Counter()
    raw_strings: set[str] = set()
    code_counts: Counter[str] = Counter()
    splits_out: dict[str, Any] = {}

    for split in SPLITS:
        st: Counter[str] = Counter()
        split_codes: Counter[str] = Counter()
        split_sets: set[tuple[str, ...]] = set()
        ws_total = ws_max = 0
        for rec in iter_records(cfg.split_path(split), split, schema):
            st[f"status_{rec.status.value}"] += 1
            if rec.status is Status.MALFORMED:
                continue
            st["rows"] += 1
            if rec.doc_id in seen_ids:
                duplicate_ids += 1
            seen_ids.add(rec.doc_id)
            if rec.doc_id.startswith("0"):
                st["ids_leading_zero"] += 1
            if rec.text == "":
                st["empty_text"] += 1
            labels = set(rec.labels)
            if labels == {schema.other_code}:
                st["other_only"] += 1
            if len(labels & main) >= 2:
                st["multi_main"] += 1
            if len(labels & sub) >= 2:
                st["multi_sub"] += 1
            code_counts.update(rec.labels)
            split_codes.update(rec.labels)
            label_sets[rec.labels] += 1
            split_sets.add(rec.labels)
            raw_strings.add(rec.raw_labels)
            ws_total += rec.n_ws_words
            ws_max = max(ws_max, rec.n_ws_words)
        splits_out[split] = {
            "stats": dict(sorted(st.items())),
            "code_counts": {c: split_codes.get(c, 0) for c in schema.codes},
            "n_distinct_label_sets": len(split_sets),
            "whitespace_words_total": ws_total,
            "whitespace_words_max": ws_max,
        }

    return {
        "audit_source": "core_register.data.audit",
        "label_schema_version": schema.version,
        "file_sha256": observed_hashes,
        "splits": splits_out,
        "global": {
            "rows": sum(s["stats"].get("rows", 0) for s in splits_out.values()),
            "unique_ids": len(seen_ids),
            "duplicate_ids": duplicate_ids,
            "n_distinct_label_sets": len(label_sets),
            "n_distinct_raw_label_strings": len(raw_strings),
            "code_counts": {c: code_counts.get(c, 0) for c in schema.codes},
            "n_observed_codes": sum(1 for c in schema.codes if code_counts.get(c, 0) > 0),
            "whitespace_words_total": sum(s["whitespace_words_total"] for s in splits_out.values()),
            "whitespace_words_max": max(s["whitespace_words_max"] for s in splits_out.values()),
        },
    }
