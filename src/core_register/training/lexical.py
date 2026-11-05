"""B0-B2 on T1: constant baselines, word TF-IDF + one-vs-rest LogisticRegression / LinearSVC (D-09).

Fitting uses the controlled TRAIN partition only (vocabulary, IDF and classifiers); thresholds and model
selection use DEV. The TF-IDF vectoriser is fitted once per vectoriser setting on train and reused across
classifier settings. That is equivalent to refitting the Pipeline, because the vectoriser has no
classifier-dependent parameters. The selected model is stored as a fitted ``Pipeline``.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from joblib import parallel_config
from numpy.typing import NDArray
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from core_register.config import BaselineExperimentConfig
from core_register.data.tasks import TaskData
from core_register.evaluation.metrics import multilabel_report
from core_register.models.baselines import all_negative, most_frequent_set, prevalence_scores
from core_register.models.thresholds import Thresholds, margin_grid, probability_grid, tune_thresholds

Array = NDArray[Any]


@dataclass
class Candidate:
    family: str
    params: dict[str, Any]
    dev_scores: Array
    thresholds: Thresholds
    tuned: dict[str, Any]
    untuned: dict[str, Any]
    fit_seconds: float
    pipeline: Pipeline


def constant_baselines(train: TaskData, dev: TaskData) -> dict[str, Any]:
    n, k = dev.y.shape
    prev = prevalence_scores(train.y, n)
    return {
        "B0_prevalence_scores": multilabel_report(dev.y, prev >= 0.5, prev, dev.labels)
        | {"note": "scores = training prevalence; decisions at 0.5 shown for completeness"},
        "B0_most_frequent_set": multilabel_report(dev.y, most_frequent_set(train.y, n), None, dev.labels),
        "B0_all_negative": multilabel_report(dev.y, all_negative(n, k), None, dev.labels),
    }


def _scores(clf: OneVsRestClassifier, x: Any, family: str) -> Array:
    return np.asarray(clf.predict_proba(x) if family == "logreg" else clf.decision_function(x), dtype=float)


def run_linear_grid(train: TaskData, dev: TaskData, cfg: BaselineExperimentConfig) -> tuple[list[dict[str, Any]],
                                                                                           dict[str, Candidate]]:
    th = cfg.thresholds
    prob_grid = probability_grid(th.probability_grid.start, th.probability_grid.stop, th.probability_grid.step)
    results: list[dict[str, Any]] = []
    best: dict[str, Candidate] = {}
    for max_features in cfg.tfidf_grid.max_features:
        for ngram in cfg.tfidf_grid.ngram_range:
            t0 = time.perf_counter()
            vec = TfidfVectorizer(max_features=max_features, ngram_range=tuple(ngram), min_df=cfg.tfidf_grid.min_df,
                                  token_pattern=cfg.lexical.token_pattern, lowercase=False, dtype=np.float32)
            x_train = vec.fit_transform(train.texts)  # train only
            x_dev = vec.transform(dev.texts)
            vec_seconds = time.perf_counter() - t0
            for family, grid in (("logreg", cfg.logreg_grid), ("svm", cfg.svm_grid)):
                for c in grid.C:
                    for cw in grid.class_weight:
                        t1 = time.perf_counter()
                        if family == "logreg":
                            est: Any = LogisticRegression(C=c, class_weight=cw, solver="liblinear", max_iter=1000,
                                                          random_state=cfg.seed)
                        else:
                            est = LinearSVC(C=c, class_weight=cw, max_iter=5000, random_state=cfg.seed)
                        # threading backend: the process backend memory-maps the sparse matrix read-only, which
                        # liblinear rejects ("WRITEBACKIFCOPY base is read-only", ISS-012); liblinear releases the GIL
                        with parallel_config(backend="threading", n_jobs=cfg.n_jobs):
                            clf = OneVsRestClassifier(est, n_jobs=cfg.n_jobs).fit(x_train, train.y.astype(int))
                        scores = _scores(clf, x_dev, family)
                        cands = prob_grid if family == "logreg" else margin_grid(
                            scores, th.margin_quantiles.start, th.margin_quantiles.stop, th.margin_quantiles.step)
                        thr = tune_thresholds(dev.y, scores, cands, th.per_label_min_dev_positives,
                                              th.per_label_shrinkage)
                        default = 0.5 if family == "logreg" else 0.0
                        untuned = multilabel_report(dev.y, scores >= default, scores, dev.labels)
                        tuned = multilabel_report(dev.y, thr.apply(scores), scores, dev.labels)
                        params = {"max_features": max_features, "ngram_range": list(ngram), "min_df":
                                  cfg.tfidf_grid.min_df, "C": c, "class_weight": cw}
                        fit_s = round(time.perf_counter() - t1 + vec_seconds, 1)
                        results.append({"family": family, "params": params, "dev_macro_f1_tuned": tuned["macro_f1"],
                                        "dev_macro_f1_default_threshold": untuned["macro_f1"],
                                        "dev_micro_f1_tuned": tuned["micro_f1"], "dev_macro_ap": tuned["macro_ap"],
                                        "global_threshold": thr.global_threshold, "fit_seconds": fit_s,
                                        "vocabulary_size": len(vec.vocabulary_)})
                        print(f"[grid {len(results)}] {family} {params} dev macro-F1 tuned="
                              f"{tuned['macro_f1']:.4f} ({fit_s}s)", file=sys.stderr, flush=True)
                        prev_best = best.get(family)
                        if prev_best is None or tuned["macro_f1"] > prev_best.tuned["macro_f1"]:
                            best[family] = Candidate(family, params, scores, thr, tuned, untuned, fit_s,
                                                     Pipeline([("tfidf", vec), ("clf", clf)]))
    return results, best
