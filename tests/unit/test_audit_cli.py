"""Audit counts and CLI behaviour on a synthetic corpus with hand-computable answers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_register.cli import main
from core_register.data.audit import run_audit

ROWS = {
    "train": [
        b"NA NE\t0000001\tone two three\n",
        b"NA OP NE OB\t0000002\tfour five\n",  # multi-main, multi-sub
        b"OTHER\t0000003\tsix\n",
        b"IN\t0000004\t\n",  # empty text
    ],
    "dev": [b"NA NE DP\t1000005\tseven eight\n", b"NA DP NE\t1000006\tnine\n"],  # order variants
    "test": [b"IN XX\t1000007\tten\n", b"IN\t1000008\n"],  # unknown code, malformed
}


def test_audit_counts_are_hand_computable(corpus_factory) -> None:  # type: ignore[no-untyped-def]
    a = run_audit(corpus_factory(ROWS))
    g = a["global"]
    assert g["rows"] == 7  # malformed excluded from rows
    assert g["unique_ids"] == 7 and g["duplicate_ids"] == 0
    assert g["n_distinct_raw_label_strings"] == 7
    # dev order variants collapse, and "IN XX" parses to {IN} like "IN": 5 sets
    assert g["n_distinct_label_sets"] == 5
    assert g["whitespace_words_total"] == 10 and g["whitespace_words_max"] == 3
    tr = a["splits"]["train"]["stats"]
    assert tr["other_only"] == 1 and tr["multi_main"] == 1 and tr["multi_sub"] == 1
    assert tr["empty_text"] == 1 and tr["ids_leading_zero"] == 4
    assert tr["status_EMPTY_INPUT"] == 1
    te = a["splits"]["test"]["stats"]
    assert te["status_UNKNOWN_CODE"] == 1 and te["status_MALFORMED"] == 1
    dumped = json.dumps(a)
    for word in ("one two three", "seven", "nine", "ten"):  # no corpus content leaks into the audit
        assert word not in dumped


def test_cli_writes_json_and_fails_on_hash_mismatch(corpus_factory, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    cfg = corpus_factory(ROWS)
    cfg_path = tmp_path / "cfg.json"  # JSON is valid YAML
    cfg_path.write_text(cfg.model_dump_json(), encoding="utf-8")
    out = tmp_path / "out" / "audit.json"
    assert main(["audit", "--config", str(cfg_path), "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["global"]["rows"] == 7
    assert b"\r" not in out.read_bytes()

    bad = json.loads(cfg.model_dump_json())
    bad["expected_sha256"]["dev.tsv.gz"] = "f" * 64
    cfg_path.write_text(json.dumps(bad), encoding="utf-8")
    assert main(["audit", "--config", str(cfg_path)]) == 2


def test_cli_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        main([])
