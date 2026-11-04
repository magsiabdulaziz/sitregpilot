"""The package audit must reproduce the Phase 1 reference audit on the real corpus.

Skipped when data/raw/CORE-corpus is absent (always in CI: the corpus is never downloaded there).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_register.config import SPLITS, load_data_config
from core_register.data.audit import run_audit

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/CORE-corpus"

pytestmark = [
    pytest.mark.requires_corpus,
    pytest.mark.skipif(not (RAW / "train.tsv.gz").is_file(), reason="raw CORE corpus not present"),
]


@pytest.fixture(scope="module")
def audits() -> tuple[dict, dict]:  # type: ignore[type-arg]
    reference = json.loads((ROOT / "reports/audit/corpus_audit.json").read_text(encoding="utf-8"))
    cfg = load_data_config(ROOT / "configs/data/core.yaml")
    cfg = cfg.model_copy(update={"raw_dir": RAW, "label_schema": ROOT / cfg.label_schema})
    return reference, run_audit(cfg)


def test_hashes_match_reference(audits) -> None:  # type: ignore[no-untyped-def]
    ref, ours = audits
    for name, digest in ours["file_sha256"].items():
        assert ref["file_sha256"][name] == digest


def test_global_counts_match_reference(audits) -> None:  # type: ignore[no-untyped-def]
    ref, ours = audits
    rg, og = ref["global"], ours["global"]
    assert og["rows"] == rg["rows"] == 48452
    assert og["unique_ids"] == rg["unique_ids"]
    assert og["duplicate_ids"] == len(rg["duplicate_ids"]) == 0
    assert og["n_distinct_label_sets"] == rg["n_distinct_combinations"] == 455
    # The reference JSON stores only label *sets*; the 460 raw strings were counted in Phase 1 (ISS-003).
    assert og["n_distinct_raw_label_strings"] == 460
    assert og["code_counts"] == rg["code_counts"]
    assert og["n_observed_codes"] == rg["n_observed_codes"] == 56
    assert og["whitespace_words_total"] == rg["whitespace_words_total"]
    assert og["whitespace_words_max"] == rg["whitespace_words_max"]


@pytest.mark.parametrize("split", SPLITS)
def test_split_counts_match_reference(audits, split: str) -> None:  # type: ignore[no-untyped-def]
    ref, ours = audits
    rs, os_ = ref["splits"][split]["stats"], ours["splits"][split]["stats"]
    for key in ("rows", "empty_text", "other_only", "multi_main", "multi_sub", "ids_leading_zero"):
        assert os_.get(key, 0) == rs.get(key, 0), key
    assert os_.get("status_MALFORMED", 0) == 0 and os_.get("status_UNKNOWN_CODE", 0) == 0
    assert os_["status_EMPTY_INPUT"] == rs["empty_text"]
    ref_ws, our_split = ref["splits"][split]["whitespace_word_count"], ours["splits"][split]
    assert our_split["whitespace_words_total"] == ref_ws["total"]
    assert our_split["whitespace_words_max"] == ref_ws["max"]
    assert our_split["code_counts"] == ref["splits"][split]["code_counts"]
    assert our_split["n_distinct_label_sets"] == ref["splits"][split]["n_distinct_combinations"]
    statuses = sum(v for k, v in os_.items() if k.startswith("status_"))
    assert statuses == rs["lines"], "every physical line gets exactly one status"
