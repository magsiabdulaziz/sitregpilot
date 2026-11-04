"""controlled_split rules (D-07) on synthetic records with hand-computable outcomes."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from core_register.config import load_split_config
from core_register.data.ingest import Record, Status
from core_register.data.labels import LabelSchema
from core_register.data.splits import build_split_manifest

ROOT = Path(__file__).resolve().parents[2]
CFG = load_split_config(ROOT / "configs/data/splits.yaml")

LONG = " ".join(f"w{i}" for i in range(80))  # >= 60 words: gets template keys


def rec(doc_id: str, split: str, labels: tuple[str, ...] = ("NA", "NE"), text: str = "some text") -> Record:
    return Record(
        doc_id=doc_id,
        split=split,  # type: ignore[arg-type]
        source_file=f"{split}.tsv.gz",
        line_no=1,
        raw_labels=" ".join(labels),
        labels=labels,
        unknown_codes=(),
        text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        n_ws_words=len(text.split()),
        status=Status.OK if text.strip() else Status.EMPTY_INPUT,
    )


def build(records: list[Record], groups: dict[str, str], schema: LabelSchema):  # type: ignore[no-untyped-def]
    rows, report = build_split_manifest(records, groups, schema, CFG)
    return {r["doc_id"]: r for r in rows}, report


def ok_groups(records: list[Record], pairs: dict[str, str] | None = None) -> dict[str, str]:
    g = {r.doc_id: "G" + r.doc_id for r in records if r.status is Status.OK}
    g.update(pairs or {})
    return g


def test_priority_test_over_dev_over_train(schema: LabelSchema) -> None:
    rs = [rec("1", "train"), rec("2", "dev"), rec("3", "test"), rec("4", "train"), rec("5", "dev")]
    groups = ok_groups(rs, {"1": "G1", "2": "G1", "3": "G1", "4": "G4", "5": "G4"})
    rows, rep = build(rs, groups, schema)
    assert rows["3"]["controlled_partition"] == "test"
    assert rows["1"]["controlled_reason"] == rows["2"]["controlled_reason"] == "cross_split_duplicate"
    assert rows["5"]["controlled_partition"] == "dev" and rows["4"]["controlled_reason"] == "cross_split_duplicate"
    assert rep["assertions"]["controlled_group_disjoint"]


def test_within_train_keeps_lowest_id_and_quarantines_conflicts(schema: LabelSchema) -> None:
    rs = [
        rec("0000009", "train"), rec("0000003", "train"),  # same labels: keep 0000003
        rec("0000020", "train", ("ID",)), rec("0000021", "train", ("ID", "DF")),  # conflict: quarantine both
    ]
    groups = ok_groups(rs, {"0000009": "G0000003", "0000003": "G0000003", "0000020": "G0000020", "0000021": "G0000020"})
    rows, _ = build(rs, groups, schema)
    assert rows["0000003"]["controlled_reason"] == "kept"
    assert rows["0000009"]["controlled_reason"] == "within_train_duplicate"
    assert {rows[i]["controlled_reason"] for i in ("0000020", "0000021")} == {"train_label_conflict"}


def test_dev_and_test_duplicates_are_all_kept_and_share_a_group(schema: LabelSchema) -> None:
    rs = [rec("1", "test", ("IN",)), rec("2", "test", ("NA",))]  # even with conflicting labels
    rows, _ = build(rs, ok_groups(rs, {"1": "G1", "2": "G1"}), schema)
    assert rows["1"]["controlled_partition"] == rows["2"]["controlled_partition"] == "test"
    assert rows["1"]["group_id"] == rows["2"]["group_id"] == "G1" and rows["1"]["group_size"] == "2"


def test_empty_and_other_cohorts(schema: LabelSchema) -> None:
    rs = [rec("1", "train", text=""), rec("2", "test", ("OTHER",)), rec("3", "dev")]
    rows, rep = build(rs, ok_groups(rs), schema)
    assert (rows["1"]["controlled_partition"], rows["1"]["controlled_reason"], rows["1"]["cohort"]) == (
        "excluded", "status_EMPTY_INPUT", "empty")
    assert rows["2"]["cohort"] == "other_only" and rows["2"]["controlled_partition"] == "test"
    assert rows["3"]["cohort"] == "functional"
    assert rep["assertions"] == {
        "every_row_accounted": True,
        "controlled_group_disjoint": True,
        "controlled_group_disjoint_violations": [],
        "no_record_moved_between_partitions": True,
    }


def test_template_seen_uses_training_documents_only(schema: LabelSchema) -> None:
    other = " ".join(f"z{i}" for i in range(80))
    rs = [rec("1", "train", text=LONG), rec("2", "test", text=LONG + " tail"), rec("3", "dev", text=other),
          rec("4", "dev", text=other), rec("5", "test", text="short text")]
    rows, _ = build(rs, ok_groups(rs), schema)
    assert rows["2"]["template_seen_controlled"] == "true"  # shares the first 50 words with train doc 1
    assert rows["3"]["template_seen_controlled"] == "false"  # matches only another dev doc
    assert rows["5"]["template_seen_controlled"] == ""  # too short for template keys
    assert rows["1"]["template_seen_controlled"] == ""  # flags apply to dev/test only


def test_template_flag_ignores_excluded_training_docs(schema: LabelSchema) -> None:
    rs = [rec("1", "train", text=LONG), rec("2", "dev", text=LONG + " x"), rec("3", "test", text=LONG + " y")]
    # 1 and 3 are near-duplicates: 1 leaves train, so its template no longer counts as "seen" for controlled
    rows, _ = build(rs, ok_groups(rs, {"1": "G1", "3": "G1"}), schema)
    assert rows["2"]["template_seen_released"] == "true"
    assert rows["2"]["template_seen_controlled"] == "false"


def test_manifest_has_no_text_or_labels_and_is_deterministic(schema: LabelSchema) -> None:
    rs = [rec("2", "train", text=LONG), rec("1", "test", ("IP", "DS"))]
    rows1, _ = build_split_manifest(rs, ok_groups(rs), schema, CFG)
    rows2, _ = build_split_manifest(list(reversed(rs)), ok_groups(rs), schema, CFG)
    assert rows1 == rows2 and [r["doc_id"] for r in rows1] == ["1", "2"]
    flat = " ".join(" ".join(r.values()) for r in rows1)
    assert "w10" not in flat and "IP" not in flat.split()


def test_groups_must_cover_exactly_the_ok_documents(schema: LabelSchema) -> None:
    rs = [rec("1", "train"), rec("2", "dev")]
    with pytest.raises(ValueError, match="cover exactly"):
        build_split_manifest(rs, {"1": "G1"}, schema, CFG)


def test_split_config_rejects_bad_priority() -> None:
    from pydantic import ValidationError

    from core_register.config import SplitConfig

    data = CFG.model_dump()
    with pytest.raises(ValidationError):
        SplitConfig.model_validate({**data, "partition_priority": ["test", "test", "train"]})
