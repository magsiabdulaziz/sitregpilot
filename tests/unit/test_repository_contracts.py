"""Corpus-free checks that run in CI: package import and committed reference artifacts."""

from __future__ import annotations

import json
import py_compile
from pathlib import Path

import core_register

ROOT = Path(__file__).resolve().parents[2]
MAIN = ["SP", "LY", "IN", "IP", "OP", "NA", "HI", "ID"]


def test_package_imports_with_version() -> None:
    assert core_register.__version__ == "0.0.1"


def test_label_schema_structure() -> None:
    schema = json.loads((ROOT / "schemas/labels/label_schema_v0.draft.json").read_text(encoding="utf-8"))
    codes = schema["codes"]
    assert len(codes) == 56
    assert len({c["code"] for c in codes}) == 56
    levels = [c["level"] for c in codes]
    assert levels.count("main") == 8 and levels.count("sub") == 47 and levels.count("annotation_outcome") == 1
    assert schema["main_order_article"] == MAIN
    # Every subcode has a Table-1 reference parent that is a main code (reference only, not a constraint).
    for c in codes:
        if c["level"] == "sub":
            assert c["reference_parent_table1"] in MAIN


def test_audit_json_has_no_text_fields_and_expected_totals() -> None:
    audit = json.loads((ROOT / "reports/audit/corpus_audit.json").read_text(encoding="utf-8"))
    assert audit["global"]["rows"] == 48452
    assert audit["global"]["unique_ids"] == 48452
    assert audit["global"]["n_distinct_combinations"] == 455

    def walk(o: object) -> None:
        if isinstance(o, dict):
            assert "text" not in o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            assert len(o) < 200, "unexpectedly long string in audit JSON (possible text leak)"

    walk(audit)


def test_reference_scripts_compile() -> None:
    for script in ("phase1_corpus_audit.py", "phase1_template_overlap.py"):
        py_compile.compile(str(ROOT / "scripts" / script), doraise=True)


def test_tracked_text_files_use_lf(tmp_path: Path) -> None:
    for rel in ("README.md", "CLAUDE.md", "pyproject.toml", "reports/audit/corpus_audit.json"):
        assert b"\r" not in (ROOT / rel).read_bytes(), rel
