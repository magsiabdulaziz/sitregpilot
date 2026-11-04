"""Duplicate grouping on synthetic documents (D-07 policy from configs/data/dedup.yaml)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from core_register.config import DedupConfig, load_dedup_config
from core_register.data.deduplicate import build_report, group_documents, jaccard, manifest_rows, word_shingles
from core_register.data.ingest import Record, Status

ROOT = Path(__file__).resolve().parents[2]
CFG = load_dedup_config(ROOT / "configs/data/dedup.yaml")

BASE = [f"w{i}" for i in range(200)]  # 200 distinct tokens


def doc(words: list[str]) -> str:
    return " ".join(words)


def changed(words: list[str], positions: list[int]) -> list[str]:
    out = list(words)
    for p in positions:
        out[p] = f"x{p}"
    return out


def rec(doc_id: str, text: str, split: str = "train", labels: tuple[str, ...] = ("NA",)) -> Record:
    return Record(
        doc_id=doc_id,
        split=split,  # type: ignore[arg-type]
        source_file=f"{split}.tsv.gz",
        line_no=1,
        raw_labels=" ".join(labels),
        labels=labels,
        unknown_codes=(),
        text=text,
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        n_ws_words=len(text.split()),
        status=Status.OK if text.strip() else Status.EMPTY_INPUT,
    )


def run(records: list[Record]):  # type: ignore[no-untyped-def]
    def source() -> Iterator[Record]:
        return iter(records)

    return group_documents(source, CFG)


def test_frozen_policy_matches_d07() -> None:
    assert (CFG.shingle_words, CFG.num_perm, CFG.lsh_bands, CFG.lsh_rows) == (5, 128, 32, 4)
    assert CFG.jaccard_threshold == 0.80 and CFG.min_words_for_near_dup == 25


def test_identical_texts_group_as_exact_raw() -> None:
    r = run([rec("0000001", doc(BASE)), rec("0000002", doc(BASE), split="test")])
    assert r.group_of["0000001"] == r.group_of["0000002"] == "G0000001"
    assert [(a, b) for a, b, _ in r.edges["exact_raw"]] == [("0000001", "0000002")]


def test_case_and_whitespace_variants_group_as_exact_norm_only() -> None:
    r = run([rec("1", doc(BASE)), rec("2", "  " + doc(BASE).upper().replace(" ", "\n "))])
    assert r.group_of["1"] == r.group_of["2"]
    assert r.edges["exact_raw"] == [] and len(r.edges["exact_norm"]) == 1


def test_near_identical_long_texts_group_after_verification() -> None:
    a, b = doc(BASE), doc(changed(BASE, [100]))  # one word changed: J = 191/201 ~ 0.95
    expected = jaccard(word_shingles(a.split(), 5), word_shingles(b.split(), 5))
    assert expected > 0.9
    r = run([rec("1", a), rec("2", b)])
    assert r.group_of["1"] == r.group_of["2"]
    ((x, y, j),) = r.edges["near"]
    assert (x, y) == ("1", "2") and j == pytest.approx(expected)


def test_below_threshold_and_unrelated_texts_stay_apart() -> None:
    a = doc(BASE)
    moderate = doc(changed(BASE, list(range(0, 200, 8))))  # 25 changes: J well below 0.8
    unrelated = doc([f"u{i}" for i in range(200)])
    r = run([rec("1", a), rec("2", moderate), rec("3", unrelated)])
    assert len(set(r.group_of.values())) == 3
    assert r.edges["near"] == []


def test_short_documents_use_exact_matching_only() -> None:
    short = [f"s{i}" for i in range(20)]  # < 25 words
    r = run([rec("1", doc(short)), rec("2", doc(changed(short, [10]))), rec("3", doc(short))])
    assert r.group_of["1"] == r.group_of["3"] != r.group_of["2"]
    assert r.candidate_pairs == 0


def test_empty_texts_are_excluded() -> None:
    r = run([rec("1", ""), rec("2", ""), rec("3", doc(BASE))])
    assert set(r.group_of) == {"3"} and r.excluded == {"EMPTY_INPUT": 2}


def test_components_are_transitive_and_ids_deterministic() -> None:
    a, b = doc(BASE), doc(changed(BASE, [50]))
    records = [rec("0000009", a), rec("0000003", b), rec("0000007", b, split="dev", labels=("IN",))]
    r1, r2 = run(records), run(list(reversed(records)))
    assert r1.group_of == r2.group_of
    assert set(r1.group_of.values()) == {"G0000003"}  # near (9~3) + exact (3=7) -> one group
    rep = build_report(r1, CFG)
    assert rep["components"]["n_groups"] == 1
    assert rep["components"]["n_cross_split_groups"] == 1
    assert rep["components"]["n_label_conflict_groups"] == 1


def test_report_and_manifest_contain_no_text() -> None:
    r = run([rec("1", doc(BASE)), rec("2", doc(changed(BASE, [7]))), rec("3", "solo text " * 30)])
    dumped = json.dumps(build_report(r, CFG)) + json.dumps(manifest_rows(r))
    assert "w100" not in dumped and "solo text" not in dumped
    rows = manifest_rows(r)
    assert [row["doc_id"] for row in rows] == ["1", "2", "3"]
    assert {row["group_size"] for row in rows} == {2, 1}


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate document id"):
        run([rec("1", "a b c"), rec("1", "d e f")])


def test_dedup_config_rejects_inconsistent_banding() -> None:
    data = CFG.model_dump()
    with pytest.raises(ValidationError):
        DedupConfig.model_validate({**data, "lsh_bands": 30})
    with pytest.raises(ValidationError):
        DedupConfig.model_validate({**data, "unexpected": 1})
