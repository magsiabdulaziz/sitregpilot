"""Ingestion, label parsing, config validation, and hash verification on synthetic fixtures."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest
from pydantic import ValidationError

from core_register.config import DataConfig, load_data_config
from core_register.data.ingest import Status, iter_records
from core_register.data.labels import LabelSchema, parse_label_string
from core_register.data.validate import SourceIntegrityError, verify_source_files


def _records(tmp_path: Path, schema: LabelSchema, data: bytes) -> list:  # type: ignore[type-arg]
    p = tmp_path / "x.tsv.gz"
    with gzip.open(p, "wb") as f:
        f.write(data)
    return list(iter_records(p, "train", schema))


# --- label parsing -------------------------------------------------------------------------


def test_label_order_variants_parse_to_same_set_in_schema_order(schema: LabelSchema) -> None:
    a = parse_label_string("NA DP NE", schema)
    b = parse_label_string("NA NE DP", schema)
    assert a.labels == b.labels
    assert list(a.labels) == sorted(a.labels, key=schema.index)


def test_unknown_and_duplicate_codes_are_reported_not_dropped_silently(schema: LabelSchema) -> None:
    p = parse_label_string("IN XX IN", schema)
    assert p.labels == ("IN",)
    assert p.unknown == ("XX",)
    assert p.had_duplicates


def test_schema_has_expected_levels(schema: LabelSchema) -> None:
    assert len(schema.codes) == 56 and len(schema.main) == 8 and len(schema.sub) == 47
    assert schema.other_code == "OTHER"


# --- ingest statuses -------------------------------------------------------------------------


def test_leading_zero_id_stays_a_string(tmp_path: Path, schema: LabelSchema) -> None:
    (r,) = _records(tmp_path, schema, b"IN DT\t0012345\tSome text here.\n")
    assert r.doc_id == "0012345" and isinstance(r.doc_id, str)
    assert r.status is Status.OK
    assert r.raw_labels == "IN DT"
    assert r.labels == tuple(c for c in schema.codes if c in {"IN", "DT"})


def test_statuses_ok_empty_unknown_malformed(tmp_path: Path, schema: LabelSchema) -> None:
    data = b"".join(
        [
            b"NA NE\t0000001\tA news text.\n",  # OK
            b"IN\t0000002\t\n",  # EMPTY_INPUT
            b"IN ZZ\t0000003\ttext\n",  # UNKNOWN_CODE
            b"\t0000004\ttext\n",  # UNKNOWN_CODE (empty label field)
            b"IN\t0000005\n",  # MALFORMED (2 fields)
            b"IN\t0000006\t\xff\xfe bad utf8\n",  # MALFORMED (invalid UTF-8)
        ]
    )
    rs = _records(tmp_path, schema, data)
    assert [r.status for r in rs] == [
        Status.OK,
        Status.EMPTY_INPUT,
        Status.UNKNOWN_CODE,
        Status.UNKNOWN_CODE,
        Status.MALFORMED,
        Status.MALFORMED,
    ]
    assert rs[2].unknown_codes == ("ZZ",)
    assert [r.line_no for r in rs] == [1, 2, 3, 4, 5, 6]


def test_empty_id_is_malformed_and_whitespace_only_text_is_empty_input(tmp_path: Path, schema: LabelSchema) -> None:
    rs = _records(tmp_path, schema, b"IN\t\ttext\nIN\t0000009\t  \t \nIN\t0000010\t \xc2\xa0 \n")
    assert [r.status for r in rs] == [Status.MALFORMED, Status.EMPTY_INPUT, Status.EMPTY_INPUT]
    assert rs[0].issue == "empty document ID field"
    assert rs[1].text == "  \t "  # raw text is still preserved exactly


def test_bare_carriage_return_stays_inside_text(tmp_path: Path, schema: LabelSchema) -> None:
    # The one case where LF-only splitting differs from text-mode reading: none occur in the release.
    (r,) = _records(tmp_path, schema, b"IN\t1\tleft\rright\n")
    assert r.text == "left\rright" and r.status is Status.OK


def test_issue_strings_are_truncated(tmp_path: Path, schema: LabelSchema) -> None:
    (r,) = _records(tmp_path, schema, b"IN " + b"Z" * 300 + b"\t1\ttext\n")
    assert r.status is Status.UNKNOWN_CODE and len(r.issue) <= 80


def test_text_is_preserved_including_tabs_quotes_and_unicode_separators(tmp_path: Path, schema: LabelSchema) -> None:
    text = 'He said "hi"\tthen left    ok'
    (r,) = _records(tmp_path, schema, b"OP OB\t1\t" + text.encode("utf-8") + b"\n")
    assert r.text == text  # extra tab stays in text; U+2028 does not split the record
    assert r.n_ws_words == len(text.split())


def test_crlf_line_ending_and_missing_final_newline(tmp_path: Path, schema: LabelSchema) -> None:
    rs = _records(tmp_path, schema, b"IN\t1\tfirst\r\nIN\t2\tsecond")
    assert [r.text for r in rs] == ["first", "second"]
    assert all(r.status is Status.OK for r in rs)


# --- config and integrity ----------------------------------------------------------------------


def test_config_rejects_unknown_keys(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text(
        "raw_dir: r\nfiles: {train: a, dev: b, test: c}\nlabel_schema: s.json\nverify_hashes: false\n"
        "expected_sha256: {}\nsurprise: 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_data_config(p)


def test_config_requires_hashes_when_verifying() -> None:
    with pytest.raises(ValidationError):
        DataConfig(
            raw_dir=Path("r"),
            files={"train": "a", "dev": "b", "test": "c"},
            label_schema=Path("s.json"),
            expected_sha256={},
        )


_BASE = {
    "raw_dir": "r",
    "files": {"train": "a", "dev": "b", "test": "c"},
    "label_schema": "s.json",
    "legend_file": "l",
    "expected_sha256": {n: "0" * 64 for n in ("a", "b", "c", "l")},
}


@pytest.mark.parametrize(
    "change",
    [
        {"files": {"train": "a", "dev": "a", "test": "c"}},  # two splits share one file
        {"expected_sha256": {**_BASE["expected_sha256"], "zz": "0" * 64}},  # hash for an unconfigured file
        {"verify_hashes": "yes"},  # strings are not coerced to bool
        {"expected_sha256": {**_BASE["expected_sha256"], "a": "ABC"}},  # not a lowercase hex digest
    ],
)
def test_config_rejects_invalid_combinations(change: dict) -> None:  # type: ignore[type-arg]
    DataConfig.model_validate(_BASE)  # the base is valid
    with pytest.raises(ValidationError):
        DataConfig.model_validate({**_BASE, **change})


def test_hash_mismatch_is_refused_and_file_left_untouched(corpus_factory) -> None:  # type: ignore[no-untyped-def]
    cfg = corpus_factory({"train": [b"IN\t1\tx\n"]})
    verify_source_files(cfg)  # passes when pinned
    target = cfg.raw_dir / "train.tsv.gz"
    before = target.read_bytes()
    bad = cfg.model_copy(update={"expected_sha256": {**cfg.expected_sha256, "train.tsv.gz": "0" * 64}})
    with pytest.raises(SourceIntegrityError):
        verify_source_files(bad)
    assert target.read_bytes() == before


def test_repository_config_parses() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_data_config(root / "configs/data/core.yaml")
    assert cfg.verify_hashes and len(cfg.expected_sha256) == 4
