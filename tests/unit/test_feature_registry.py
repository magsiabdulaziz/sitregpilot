"""Registry integrity, missingness rules, MATTR, windowing, and cache resume (no corpus needed)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
import spacy

from core_register.features.extract import (
    extract_to_cache,
    feature_ids,
    features_from_counts,
    make_window,
    mattr,
    read_cache,
)
from core_register.features.registry import ALL_FEATURES, render_dictionary, validate_registry


def test_registry_is_valid_and_ids_unique() -> None:
    validate_registry()
    assert len(feature_ids()) == len(set(feature_ids())) == len(ALL_FEATURES)
    assert all(f.denominator and f.ambiguities is not None for f in ALL_FEATURES)


def test_feature_dictionary_is_in_sync_with_registry() -> None:
    doc = Path(__file__).resolve().parents[2] / "docs/feature_dictionary.md"
    assert doc.read_bytes().decode("utf-8") == render_dictionary(), "regenerate docs/feature_dictionary.md"


def test_zero_denominator_is_missing_not_zero() -> None:
    feats = features_from_counts({"n_tokens_nonpunct": 10.0, "n_sents": 0.0, "n_pos_NOUN": 3.0})
    assert feats["pos_noun"] == pytest.approx(300.0)
    assert math.isnan(feats["mean_sent_len"])  # no sentences
    assert math.isnan(feats["noun_verb_ratio"])  # no lexical verbs
    assert math.isnan(feats["mattr_500"])  # not computed


def test_mattr_hand_computed() -> None:
    assert math.isnan(mattr(["a"] * 10, window=20))
    assert mattr(list("abcd"), window=2) == pytest.approx(1.0)  # every window has 2 types
    assert mattr(list("aabb"), window=2) == pytest.approx((1 + 2 + 1) / (3 * 2))


def test_window_keeps_case_and_flags_truncation() -> None:
    w, truncated = make_window("One  Two\tThree four", 3)
    assert (w, truncated) == ("One Two Three", True)
    assert make_window("a b", 3) == ("a b", False)


def test_cache_is_resumable_and_tolerates_a_torn_line(tmp_path: Path) -> None:
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    cache = tmp_path / "counts.jsonl"
    docs = [("1", "I like it."), ("2", "They left early.")]
    assert extract_to_cache(docs, nlp, cache, window_words=1000) == {"parsed": 2}
    with cache.open("a", encoding="utf-8") as f:
        f.write('{"doc_id": "3", "key": ')  # simulate an interrupted write
    assert set(read_cache(cache)) == {"1", "2"}
    stats = extract_to_cache([*docs, ("3", "New text.")], nlp, cache, window_words=1000)
    assert stats == {"cached": 2, "parsed": 1}
    rows = read_cache(cache)
    assert set(rows) == {"1", "2", "3"} and rows["1"]["counts"]["n_pron_1sg"] == 1.0
    assert all(json.loads(json.dumps(r)) == r for r in rows.values())
