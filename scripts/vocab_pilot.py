"""D-16 training-only pilot: TF-IDF memory/runtime at a given vocabulary cap (controlled TRAIN only).

Run once per cap in a fresh process, so peak memory is per configuration:
    .venv\\Scripts\\python.exe scripts/vocab_pilot.py --max-features 200000 --out artifacts/pilot_200k.json
    .venv\\Scripts\\python.exe scripts/vocab_pilot.py --max-features 400000 --out artifacts/pilot_400k.json
    .venv\\Scripts\\python.exe scripts/vocab_pilot.py --combine artifacts/pilot_200k.json artifacts/pilot_400k.json

Stop rules (declared in D-16 before the pilot): peak RSS > 12 GB, or 400k vectoriser fit > 3x the 200k fit.
No dev or test data is read.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from joblib import parallel_config
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

from core_register.config import load_baseline_config, load_data_config
from core_register.data.labels import load_label_schema
from core_register.data.tasks import load_t1
from core_register.preprocessing.text import lexical_view
from core_register.training.tracking import RunTimer, environment, git_state

MAX_RSS_MB = 12 * 1024
MAX_FIT_RATIO = 3.0


def measure(max_features: int) -> dict[str, object]:
    cfg = load_data_config(Path("configs/data/core.yaml"))
    exp = load_baseline_config(Path("configs/experiments/cpu_baselines.yaml"))
    lx = exp.lexical

    def view(text: str) -> str:
        return lexical_view(text, exp.window_words, unicode=lx.unicode, lowercase=lx.lowercase,
                            mask_urls_emails=lx.mask_urls_emails)

    schema = load_label_schema(cfg.label_schema)
    with RunTimer() as total:
        train = load_t1(cfg, schema, Path("data/manifests/splits/split_manifest.csv"), ["train"], view)["train"]
        t0 = time.perf_counter()
        vec = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2), min_df=exp.tfidf_grid.min_df,
                              token_pattern=lx.token_pattern, lowercase=False, dtype=np.float32)
        x = vec.fit_transform(train.texts)
        vec_s = time.perf_counter() - t0
        t1 = time.perf_counter()
        with parallel_config(backend="threading", n_jobs=1):
            OneVsRestClassifier(LogisticRegression(C=10.0, class_weight="balanced", solver="liblinear",
                                                   max_iter=1000, random_state=exp.seed), n_jobs=1).fit(
                x, train.y.astype(int))
        clf_s = time.perf_counter() - t1
    return {"max_features": max_features, "ngram_range": [1, 2], "n_train": len(train.doc_ids),
            "vocabulary_size": len(vec.vocabulary_), "nnz": int(x.nnz), "vectoriser_fit_seconds": round(vec_s, 1),
            "b1best_logreg_fit_seconds": round(clf_s, 1), "timing": total.to_dict(), "git": git_state(),
            "environment": environment()}


def combine(a: Path, b: Path) -> dict[str, object]:
    base, cand = (json.loads(p.read_text(encoding="utf-8")) for p in (a, b))
    ratio = cand["vectoriser_fit_seconds"] / base["vectoriser_fit_seconds"]
    peak = cand["timing"]["peak_rss_mb"]
    stop = []
    if peak > MAX_RSS_MB:
        stop.append(f"peak RSS {peak} MB > {MAX_RSS_MB} MB")
    if ratio > MAX_FIT_RATIO:
        stop.append(f"vectoriser fit ratio {ratio:.2f} > {MAX_FIT_RATIO}")
    return {"decision_rule": "D-16: stop if peak RSS > 12 GB or 400k vectoriser fit > 3x the 200k fit",
            "baseline_200k": base, "candidate_400k": cand, "vectoriser_fit_ratio": round(ratio, 2),
            "outcome": "STOP: keep the 200k cap" if stop else "CONTINUE: run the 400k settings",
            "stop_reasons": stop, "partitions_used": ["train"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-features", type=int)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--combine", nargs=2, type=Path)
    ap.add_argument("--report", type=Path, default=Path("reports/baselines/vocab_pilot_D16.json"))
    args = ap.parse_args()
    if args.combine:
        result = combine(*args.combine)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(result["outcome"], result["stop_reasons"])
    else:
        result = measure(args.max_features)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: result[k] for k in ("max_features", "vectoriser_fit_seconds",
                                                  "b1best_logreg_fit_seconds", "timing")}))


if __name__ == "__main__":
    main()
