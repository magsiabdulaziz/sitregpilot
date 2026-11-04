"""Duplicate grouping on the real corpus reproduces the Phase 1 exact-duplicate findings.

Slow (full MinHash pass). Skipped when data/raw/CORE-corpus is absent (always in CI).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from core_register.config import SPLITS, load_data_config, load_dedup_config
from core_register.data.deduplicate import DedupResult, build_report, group_documents
from core_register.data.ingest import Record, iter_records
from core_register.data.labels import load_label_schema
from core_register.data.validate import verify_source_files

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/CORE-corpus"

pytestmark = [
    pytest.mark.requires_corpus,
    pytest.mark.skipif(not (RAW / "train.tsv.gz").is_file(), reason="raw CORE corpus not present"),
]


@pytest.fixture(scope="module")
def result() -> tuple[DedupResult, dict]:  # type: ignore[type-arg]
    cfg = load_data_config(ROOT / "configs/data/core.yaml")
    cfg = cfg.model_copy(update={"raw_dir": RAW, "label_schema": ROOT / cfg.label_schema})
    verify_source_files(cfg)
    schema = load_label_schema(cfg.label_schema)
    dcfg = load_dedup_config(ROOT / "configs/data/dedup.yaml")

    def source() -> Iterator[Record]:
        for split in SPLITS:
            yield from iter_records(cfg.split_path(split), split, schema)

    res = group_documents(source, dcfg)
    return res, build_report(res, dcfg)


def test_exact_groups_reproduce_the_reference_audit(result) -> None:  # type: ignore[no-untyped-def]
    res, report = result
    ref = json.loads((ROOT / "reports/audit/corpus_audit.json").read_text(encoding="utf-8"))
    ref_raw = ref["global"]["exact_duplicates_raw"]
    ours = report["exact_raw"]
    assert ours["n_groups"] == ref_raw["n_groups"] == 12
    assert ours["n_cross_split_groups"] == ref_raw["n_cross_split_groups"] == 6
    assert ours["cross_split_types"] == {"dev/train": 1, "test/train": 5}
    assert ours["n_label_conflict_groups"] == ref_raw["n_label_conflict_groups"] == 3
    assert report["exact_normalized"]["n_groups"] == ref["global"]["exact_duplicates_normalized"]["n_groups"]
    # exact_raw groups equal the reference groups member for member
    ours_groups: dict[str, set[str]] = {}
    for a, b, _ in res.edges["exact_raw"]:
        ours_groups.setdefault(a, {a}).add(b)
    assert {frozenset(g) for g in ours_groups.values()} == {frozenset(m["id"] for m in g) for g in ref_raw["groups"]}
    # and each reference group lies within one final component
    for group in ref_raw["groups"]:
        ids = {m["id"] for m in group}
        assert len({res.group_of[i] for i in ids}) == 1, ids


def test_empty_texts_excluded_and_no_text_in_report(result) -> None:  # type: ignore[no-untyped-def]
    res, report = result
    assert report["n_excluded_by_status"] == {"EMPTY_INPUT": 17}
    assert report["n_documents_considered"] == 48452 - 17
    assert len(report["verification_sample"]) <= 50
    assert all(set(s) == {"id_a", "split_a", "id_b", "split_b", "jaccard", "same_label_set"}
               for s in report["verification_sample"])
    assert all(s["jaccard"] >= 0.80 for s in report["verification_sample"])
