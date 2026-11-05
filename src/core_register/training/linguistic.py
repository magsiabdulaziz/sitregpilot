"""B3 (linguistic features + LogReg) and B4 (B1-best TF-IDF ⊕ α·scaled linguistic block + LogReg) on T1.

Imputation (median plus missing indicators) and RobustScaler are fitted inside the Pipeline on TRAIN only.
B4 is a single ColumnTransformer pipeline: the TF-IDF settings and classifier settings are the B1 selection,
read from the committed B0-B2 report; only α is searched. Thresholds and selection use DEV.
"""

from __future__ import annotations

import math
import sys
import time
from typing import Any

import numpy as np
import pandas as pd
from joblib import parallel_config
from numpy.typing import NDArray
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from core_register.config import BaselineExperimentConfig
from core_register.data.tasks import TaskData
from core_register.evaluation.metrics import multilabel_report
from core_register.features.extract import feature_ids, features_from_counts
from core_register.models.thresholds import probability_grid, tune_thresholds
from core_register.training.lexical import Candidate

Array = NDArray[Any]


def feature_frame(doc_ids: list[str], rows: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """One row per document (in ``doc_ids`` order), one column per registry feature; NaN = missing."""
    missing = [i for i in doc_ids if i not in rows]
    if missing:
        raise ValueError(f"{len(missing)} documents have no cached features (e.g. {missing[:3]})")
    data = [features_from_counts(rows[i]["counts"]) for i in doc_ids]
    frame = pd.DataFrame(data, columns=feature_ids(), index=doc_ids, dtype=float)
    return frame.replace([math.inf, -math.inf], np.nan)


def _ling_block() -> Pipeline:
    return Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)), ("scale", RobustScaler())])


def _fit_eval(name: str, pipe: Pipeline, x_train: Any, y_train: Array, x_dev: Any, dev: TaskData,
              cfg: BaselineExperimentConfig, params: dict[str, Any]) -> Candidate:
    th = cfg.thresholds
    t0 = time.perf_counter()
    with parallel_config(backend="threading", n_jobs=cfg.n_jobs):  # ISS-012
        pipe.fit(x_train, y_train.astype(int))
    scores = np.asarray(pipe.predict_proba(x_dev), dtype=float)
    grid = probability_grid(th.probability_grid.start, th.probability_grid.stop, th.probability_grid.step)
    thr = tune_thresholds(dev.y, scores, grid, th.per_label_min_dev_positives, th.per_label_shrinkage)
    tuned = multilabel_report(dev.y, thr.apply(scores), scores, dev.labels)
    untuned = multilabel_report(dev.y, scores >= 0.5, scores, dev.labels)
    secs = round(time.perf_counter() - t0, 1)
    print(f"[{name}] {params} dev macro-F1 tuned={tuned['macro_f1']:.4f} ({secs}s)", file=sys.stderr, flush=True)
    return Candidate(name, params, scores, thr, tuned, untuned, secs, pipe)


def _logreg(c: float, cw: str | None, seed: int, n_jobs: int) -> OneVsRestClassifier:
    return OneVsRestClassifier(LogisticRegression(C=c, class_weight=cw, solver="liblinear", max_iter=1000,
                                                  random_state=seed), n_jobs=n_jobs)


def run_b3(train: TaskData, dev: TaskData, f_train: pd.DataFrame, f_dev: pd.DataFrame,
           cfg: BaselineExperimentConfig) -> tuple[list[dict[str, Any]], Candidate]:
    grid_out: list[dict[str, Any]] = []
    best: Candidate | None = None
    for c in cfg.linguistic.logreg_grid.C:
        for cw in cfg.linguistic.logreg_grid.class_weight:
            pipe = Pipeline([("ling", _ling_block()), ("clf", _logreg(c, cw, cfg.seed, cfg.n_jobs))])
            params = {"C": c, "class_weight": cw}
            cand = _fit_eval("B3_linguistic_logreg", pipe, f_train, train.y, f_dev, dev, cfg, params)
            grid_out.append({"family": "B3_linguistic_logreg", "params": params,
                             "dev_macro_f1_tuned": cand.tuned["macro_f1"], "dev_macro_ap": cand.tuned["macro_ap"],
                             "fit_seconds": cand.fit_seconds})
            if best is None or cand.tuned["macro_f1"] > best.tuned["macro_f1"]:
                best = cand
    assert best is not None
    return grid_out, best


def run_b4(train: TaskData, dev: TaskData, f_train: pd.DataFrame, f_dev: pd.DataFrame,
           cfg: BaselineExperimentConfig, b1_params: dict[str, Any]) -> tuple[list[dict[str, Any]], Candidate]:
    def frame(data: TaskData, feats: pd.DataFrame) -> pd.DataFrame:
        out = feats.copy()
        out.insert(0, "__text__", data.texts)
        return out

    x_train, x_dev = frame(train, f_train), frame(dev, f_dev)
    cols = feature_ids()
    grid_out: list[dict[str, Any]] = []
    best: Candidate | None = None
    for alpha in cfg.linguistic.combined_alpha:
        vec = TfidfVectorizer(max_features=b1_params["max_features"], ngram_range=tuple(b1_params["ngram_range"]),
                              min_df=b1_params["min_df"], token_pattern=cfg.lexical.token_pattern, lowercase=False,
                              dtype=np.float32)
        ct = ColumnTransformer([("tfidf", vec, "__text__"), ("ling", _ling_block(), cols)],
                               transformer_weights={"tfidf": 1.0, "ling": alpha}, sparse_threshold=1.0)
        pipe = Pipeline([("features", ct),
                         ("clf", _logreg(b1_params["C"], b1_params["class_weight"], cfg.seed, cfg.n_jobs))])
        params = {"alpha": alpha, "b1_params": b1_params}
        cand = _fit_eval("B4_combined_logreg", pipe, x_train, train.y, x_dev, dev, cfg, params)
        grid_out.append({"family": "B4_combined_logreg", "params": params,
                         "dev_macro_f1_tuned": cand.tuned["macro_f1"], "dev_macro_ap": cand.tuned["macro_ap"],
                         "fit_seconds": cand.fit_seconds})
        if best is None or cand.tuned["macro_f1"] > best.tuned["macro_f1"]:
            best = cand
    assert best is not None
    return grid_out, best


def b4_frame(data: TaskData, feats: pd.DataFrame) -> pd.DataFrame:
    """The input frame B4 pipelines expect (for reload parity and later inference)."""
    out = feats.copy()
    out.insert(0, "__text__", data.texts)
    return out
