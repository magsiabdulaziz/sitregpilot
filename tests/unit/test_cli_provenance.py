"""The dedup -> split chain refuses to run on mismatched inputs, end to end on a synthetic corpus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_register import cli

ROOT = Path(__file__).resolve().parents[2]
WORDS = " ".join(f"w{i}" for i in range(80))
ROWS = {
    "train": [f"NA NE\t0000001\t{WORDS}\n".encode(), b"IN DT\t0000002\tanother text here\n"],
    "dev": [f"NA NE\t1000001\t{WORDS} x\n".encode()],
    "test": [b"OP OB\t2000001\tthird text\n", b"IN\t2000002\t\n"],
}


@pytest.fixture
def chain(corpus_factory, tmp_path: Path) -> dict[str, Path]:  # type: ignore[no-untyped-def]
    cfg = corpus_factory(ROWS)
    paths = {
        "cfg": tmp_path / "core.json",
        "dedup_report": tmp_path / "dedup.json",
        "groups": tmp_path / "groups.csv",
        "split_report": tmp_path / "split.json",
        "manifest": tmp_path / "manifest.csv",
    }
    paths["cfg"].write_text(cfg.model_dump_json(), encoding="utf-8")
    rc = cli.main(["dedup", "--config", str(paths["cfg"]), "--dedup-config", str(ROOT / "configs/data/dedup.yaml"),
                   "--report", str(paths["dedup_report"]), "--manifest", str(paths["groups"])])
    assert rc == 0
    return paths


def _split(p: dict[str, Path]) -> int:
    return cli.main(["split", "--config", str(p["cfg"]), "--split-config", str(ROOT / "configs/data/splits.yaml"),
                     "--dedup-report", str(p["dedup_report"]), "--report", str(p["split_report"]),
                     "--manifest", str(p["manifest"])])


def test_chain_succeeds_and_groups_the_near_duplicate(chain: dict[str, Path]) -> None:
    assert _split(chain) == 0
    report = json.loads(chain["split_report"].read_text(encoding="utf-8"))
    assert all(v for k, v in report["assertions"].items() if not k.endswith("violations"))
    # train doc 0000001 and dev doc 1000001 are near-duplicates: dev has priority
    assert report["exclusions_by_released_split_and_reason"]["train/cross_split_duplicate"] == 1
    assert report["exclusions_by_released_split_and_reason"]["test/status_EMPTY_INPUT"] == 1


def test_split_refuses_a_tampered_dedup_manifest(chain: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    with chain["groups"].open("a", encoding="utf-8", newline="\n") as f:
        f.write("9999999,train,G9999999,1,False,False,False\n")
    assert _split(chain) == 2
    assert "not the manifest recorded" in capsys.readouterr().err
    assert not chain["manifest"].exists()


def test_split_refuses_a_dedup_report_from_other_sources(
    chain: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    report = json.loads(chain["dedup_report"].read_text(encoding="utf-8"))
    report["source_sha256"]["train.tsv.gz"] = "0" * 64
    chain["dedup_report"].write_text(json.dumps(report), encoding="utf-8")
    assert _split(chain) == 2
    assert "different source files" in capsys.readouterr().err
    assert not chain["manifest"].exists()


def test_split_exits_3_and_writes_nothing_when_an_assertion_fails(
    chain: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    real = cli.build_split_manifest

    def broken(*args, **kwargs):  # type: ignore[no-untyped-def]
        rows, report = real(*args, **kwargs)
        report["assertions"]["controlled_group_disjoint"] = False
        return rows, report

    monkeypatch.setattr(cli, "build_split_manifest", broken)
    assert _split(chain) == 3
    assert "split assertions failed" in capsys.readouterr().err
    assert not chain["manifest"].exists() and not chain["split_report"].exists()
