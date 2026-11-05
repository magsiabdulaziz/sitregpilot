"""Fixed 60-document TRAINING-only inspection sample for feature validity (methodology section 6).

Draws controlled-train documents stratified by window length (short, medium, truncated), covering every
main register, and writes their IDs, labels, and feature values (no text) plus a checklist for a human
reviewer. No measured accuracy is claimed until a qualified reviewer completes it.

Usage: .venv\\Scripts\\python.exe scripts/feature_inspection_sample.py
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import random
from pathlib import Path

from core_register.features.extract import EXTRACTOR_VERSION, features_from_counts, read_cache

MAIN = ["SP", "LY", "IN", "IP", "OP", "NA", "HI", "ID"]
SEED = 20261105
N = 60


def main() -> None:
    with open("data/manifests/splits/split_manifest.csv", encoding="utf-8", newline="") as f:
        train = {r["doc_id"] for r in csv.DictReader(f) if r["controlled_partition"] == "train"}
    labels: dict[str, list[str]] = {}
    with gzip.open("data/raw/CORE-corpus/train.tsv.gz", "rb") as f:
        for line in f:
            lab, doc_id, _ = line.rstrip(b"\n").decode("utf-8").split("\t", 2)
            if doc_id in train:
                labels[doc_id] = lab.split()
    rows = read_cache(Path("artifacts/features") / EXTRACTOR_VERSION / "counts.jsonl")
    pool = sorted(i for i in train if i in rows)
    rng = random.Random(SEED)
    strata = {
        "short (<300 words)": [i for i in pool if rows[i]["n_window_ws_words"] < 300],
        "medium (300-999)": [i for i in pool if 300 <= rows[i]["n_window_ws_words"] < 1000 and not rows[i]["truncated"]],
        "truncated (1,000-word window)": [i for i in pool if rows[i]["truncated"]],
    }
    chosen: list[tuple[str, str]] = []
    for name, ids in strata.items():  # 20 per stratum, with at least 2 per main register where possible
        picked: list[str] = []
        for m in MAIN:
            cands = [i for i in ids if m in labels[i] and i not in picked]
            picked += rng.sample(cands, min(2, len(cands)))
        rest = [i for i in ids if i not in picked]
        picked += rng.sample(rest, max(0, N // 3 - len(picked)))
        chosen += [(i, name) for i in sorted(picked[: N // 3])]
    out = {
        "purpose": "manual feature-validity inspection (training documents only)",
        "status": "PENDING human review: no extraction accuracy is claimed",
        "extractor_version": EXTRACTOR_VERSION,
        "seed": SEED,
        "reviewer_checklist": [
            "Open the raw text by doc_id locally (never copy text into the repository).",
            "Check sentence segmentation, pronoun person counts, tense, passive, questions and imperatives.",
            "Record each feature as plausible / implausible with a short reason.",
        ],
        "documents": [
            {
                "doc_id": i,
                "stratum": s,
                "labels": labels[i],
                "window_ws_words": rows[i]["n_window_ws_words"],
                "truncated": rows[i]["truncated"],
                "features": {k: (None if math.isnan(v) else round(v, 3))
                             for k, v in features_from_counts(rows[i]["counts"]).items()},
                "review": {"reviewer": None, "verdict": None, "notes": None},
            }
            for i, s in chosen
        ],
    }
    path = Path("reports/features/inspection_sample.json")
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path} with {len(chosen)} documents")


if __name__ == "__main__":
    main()
