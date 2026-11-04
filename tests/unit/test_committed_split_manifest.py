"""Corpus-free contract on the committed, sealed split manifest (runs in CI).

The manifest must match the hash recorded in reports/splits/split_report.json, account for every
released row, keep controlled partitions group-disjoint, and reproduce the sealed test-ID hashes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = json.loads((ROOT / "reports/splits/split_report.json").read_text(encoding="utf-8"))
MANIFEST = ROOT / REPORT["manifest"]["path"]


def _rows() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _ids_sha(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode("utf-8")).hexdigest()


def test_manifest_hash_matches_report() -> None:
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == REPORT["manifest"]["sha256"]


def test_every_released_row_present_once() -> None:
    rows = _rows()
    ids = [r["doc_id"] for r in rows]
    assert len(rows) == 48452 == REPORT["n_input_rows"] and len(set(ids)) == len(ids)
    assert all(len(i) == 7 and i.isdigit() for i in ids)  # leading zeros preserved as strings


def test_controlled_partitions_are_group_disjoint_and_never_moved() -> None:
    parts: dict[str, set[str]] = defaultdict(set)
    for r in _rows():
        p = r["controlled_partition"]
        if p != "excluded":
            assert p == r["released_split"]
            parts[r["group_id"]].add(p)
        else:
            assert r["controlled_reason"] != "kept"
    assert all(len(p) == 1 for p in parts.values())


def test_sealed_test_hashes_recompute() -> None:
    rows = _rows()
    sealed = REPORT["sealed_test"]
    assert _ids_sha([r["doc_id"] for r in rows if r["released_split"] == "test"]) == sealed["released_test_ids_sha256"]
    controlled_test = [r["doc_id"] for r in rows if r["controlled_partition"] == "test"]
    assert _ids_sha(controlled_test) == sealed["controlled_test_ids_sha256"]
