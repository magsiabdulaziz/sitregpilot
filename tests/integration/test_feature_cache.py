"""The feature cache covers exactly the OK documents of the sealed manifest, and the committed report matches it.

Needs the extraction cache (artifacts/features/...); skipped otherwise (always in CI).
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import pytest

from core_register.features.extract import EXTRACTOR_VERSION, feature_ids, features_from_counts, read_cache

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports/features/extraction_report.json"
CACHE = ROOT / "artifacts/features" / EXTRACTOR_VERSION / "counts.jsonl"

pytestmark = [
    pytest.mark.requires_corpus,
    pytest.mark.skipif(not CACHE.is_file(), reason="feature cache not present"),
]


def test_cache_matches_report_and_manifest() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["extractor_version"] == EXTRACTOR_VERSION
    assert hashlib.sha256(CACHE.read_bytes()).hexdigest() == report["cache"]["sha256"]
    with (ROOT / "data/manifests/splits/split_manifest.csv").open(encoding="utf-8", newline="") as f:
        ok_ids = {r["doc_id"] for r in csv.DictReader(f) if r["status"] == "OK"}
    rows = read_cache(CACHE)
    assert set(rows) == ok_ids and len(rows) == report["cache"]["rows"]


def test_every_cached_row_yields_all_features() -> None:
    with (ROOT / "data/manifests/splits/split_manifest.csv").open(encoding="utf-8", newline="") as f:
        train_dev = {r["doc_id"] for r in csv.DictReader(f) if r["controlled_partition"] in ("train", "dev")}
    rows = read_cache(CACHE)
    ids = feature_ids()
    for row in [r for r in rows.values() if r["doc_id"] in train_dev][:2000]:  # never touch test rows
        feats = features_from_counts(row["counts"])
        assert list(feats) == ids
        assert all(isinstance(v, float) and (math.isnan(v) or v >= 0) for v in feats.values())
        assert row["n_window_ws_words"] <= 1000
