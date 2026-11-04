"""Rebuilding the split manifest from the corpus reproduces the committed (sealed) manifest byte for byte.

Needs the raw corpus and the dedup group manifest (artifacts/dedup/groups.csv); skipped otherwise.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_register.cli import main

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ROOT / "artifacts/dedup/groups.csv"

pytestmark = [
    pytest.mark.requires_corpus,
    pytest.mark.skipif(
        not (ROOT / "data/raw/CORE-corpus/train.tsv.gz").is_file() or not GROUPS.is_file(),
        reason="raw corpus or dedup group manifest not present",
    ),
]


def test_rebuild_reproduces_sealed_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    committed = json.loads((ROOT / "reports/splits/split_report.json").read_text(encoding="utf-8"))
    monkeypatch.chdir(ROOT)  # config paths are relative to the repository root
    out_manifest, out_report = tmp_path / "m.csv", tmp_path / "r.json"
    rc = main(["split", "--config", "configs/data/core.yaml", "--split-config", "configs/data/splits.yaml",
               "--manifest", str(out_manifest), "--report", str(out_report)])
    assert rc == 0
    rebuilt = json.loads(out_report.read_text(encoding="utf-8"))
    assert rebuilt["manifest"]["sha256"] == committed["manifest"]["sha256"]
    assert rebuilt["sealed_test"] == committed["sealed_test"]
    assert out_manifest.read_bytes() == (ROOT / committed["manifest"]["path"]).read_bytes()
