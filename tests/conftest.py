"""Shared fixtures: a tiny synthetic CORE-format corpus (no real corpus text)."""

from __future__ import annotations

import gzip
import hashlib
from pathlib import Path

import pytest

from core_register.config import DataConfig
from core_register.data.labels import LabelSchema, load_label_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/labels/label_schema_v0.draft.json"


@pytest.fixture(scope="session")
def schema() -> LabelSchema:
    return load_label_schema(SCHEMA_PATH)


@pytest.fixture
def corpus_factory(tmp_path: Path):  # type: ignore[no-untyped-def]
    def _make(rows: dict[str, list[bytes]]) -> DataConfig:
        return make_corpus(tmp_path, rows)

    return _make


def write_gz(path: Path, lines: list[bytes]) -> None:
    with gzip.open(path, "wb") as f:
        f.write(b"".join(lines))


def make_corpus(tmp_path: Path, rows: dict[str, list[bytes]]) -> DataConfig:
    """Write train/dev/test .tsv.gz plus a legend and return a hash-pinned config."""
    raw = tmp_path / "raw"
    raw.mkdir()
    for split in ("train", "dev", "test"):
        write_gz(raw / f"{split}.tsv.gz", rows.get(split, []))
    (raw / "legend.txt").write_bytes(b"IN\tinformational\n")
    names = ["train.tsv.gz", "dev.tsv.gz", "test.tsv.gz", "legend.txt"]
    return DataConfig(
        raw_dir=raw,
        files={"train": "train.tsv.gz", "dev": "dev.tsv.gz", "test": "test.tsv.gz"},
        legend_file="legend.txt",
        label_schema=SCHEMA_PATH,
        expected_sha256={n: hashlib.sha256((raw / n).read_bytes()).hexdigest() for n in names},
    )
