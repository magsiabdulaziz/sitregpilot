"""Profile spaCy throughput and memory on a fixed controlled-TRAIN sample (issue #19).

Training documents only (taken from the sealed split manifest); window = first 1,000 whitespace
words (D-06). Peak memory is sampled across the main process and its workers. Writes
reports/profiling/spacy_profile.json (counts and timings only, no text).

Usage (from the repo root):
    .venv\\Scripts\\python.exe scripts/profile_spacy.py --sample 300
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import platform
import random
import threading
import time
from pathlib import Path
from typing import Any

import psutil
import spacy

WINDOW = 1000


def load_sample(n: int, seed: int) -> list[str]:
    with open("data/manifests/splits/split_manifest.csv", encoding="utf-8", newline="") as f:
        train_ids = sorted(r["doc_id"] for r in csv.DictReader(f) if r["controlled_partition"] == "train")
    chosen = set(random.Random(seed).sample(train_ids, n))
    texts: dict[str, str] = {}
    with gzip.open("data/raw/CORE-corpus/train.tsv.gz", "rb") as f:
        for line in f:
            _, doc_id, text = line.rstrip(b"\n").decode("utf-8").split("\t", 2)
            if doc_id in chosen:
                texts[doc_id] = " ".join(text.split()[:WINDOW])
    return [texts[i] for i in sorted(texts)]


class PeakRSS:
    """Samples the summed RSS of this process and its children every 0.2 s."""

    def __init__(self) -> None:
        self.peak = 0
        self._stop = threading.Event()
        self._proc = psutil.Process()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                total = self._proc.memory_info().rss + sum(
                    c.memory_info().rss for c in self._proc.children(recursive=True)
                )
                self.peak = max(self.peak, total)
            except psutil.Error:
                pass
            time.sleep(0.2)

    def __enter__(self) -> PeakRSS:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join()


def profile(texts: list[str], disable: list[str], n_process: int, batch_size: int) -> dict[str, Any]:
    nlp = spacy.load("en_core_web_sm", disable=disable)
    words = sum(len(t.split()) for t in texts)
    with PeakRSS() as mem:
        start = time.perf_counter()
        tokens = sum(len(d) for d in nlp.pipe(texts, n_process=n_process, batch_size=batch_size))
        secs = time.perf_counter() - start
    return {
        "active_pipes": nlp.pipe_names,
        "disabled": disable,
        "n_process": n_process,
        "batch_size": batch_size,
        "docs": len(texts),
        "ws_words": words,
        "spacy_tokens": tokens,
        "seconds": round(secs, 1),
        "docs_per_sec": round(len(texts) / secs, 2),
        "ws_words_per_sec": round(words / secs),
        "peak_rss_mb_main_plus_workers": round(mem.peak / 2**20),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20261105)
    ap.add_argument("--out", type=Path, default=Path("reports/profiling/spacy_profile.json"))
    args = ap.parse_args()
    texts = load_sample(args.sample, args.seed)
    runs = [
        profile(texts, [], 1, 32),
        profile(texts, ["ner"], 1, 32),
        profile(texts, ["ner"], 3, 16),
    ]
    with open("data/manifests/splits/split_manifest.csv", encoding="utf-8", newline="") as f:
        n_windows = sum(1 for r in csv.DictReader(f) if r["status"] == "OK")
    best = max(runs, key=lambda r: r["docs_per_sec"])
    report = {
        "purpose": "issue #19 profiling before full extraction; training documents only",
        "sample": {
            "source": "controlled_partition == train",
            "n": len(texts),
            "seed": args.seed,
            "window_ws_words": WINDOW,
        },
        "environment": {
            "spacy": spacy.__version__,
            "model": "en_core_web_sm " + spacy.load("en_core_web_sm").meta["version"],
            "python": platform.python_version(),
            "cpu_logical": psutil.cpu_count(),
            "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        },
        "runs": runs,
        "estimate_full_extraction": {
            "n_documents": n_windows,
            "best_config": {k: best[k] for k in ("disabled", "n_process", "batch_size")},
            "estimated_hours": round(n_windows / best["docs_per_sec"] / 3600, 2),
            "note": "linear extrapolation from the sample; real runtime varies with document length",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
