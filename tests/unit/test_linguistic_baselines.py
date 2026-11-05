"""B3/B4 on synthetic counts: train-only preprocessing, signal recovery, missing handling, and reload parity."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pytest

from core_register.config import load_baseline_config
from core_register.data.tasks import TaskData
from core_register.features.extract import feature_ids
from core_register.training.linguistic import b4_frame, feature_frame, run_b3, run_b4

ROOT = Path(__file__).resolve().parents[2]
LABELS = ["SP", "LY", "IN", "IP", "OP", "NA", "HI", "ID"]


def _data(n: int, seed: int) -> tuple[TaskData, dict[str, dict[str, object]]]:
    rng = np.random.default_rng(seed)
    y = rng.random((n, 8)) < 0.3
    y[~y.any(axis=1), 0] = True
    rows: dict[str, dict[str, object]] = {}
    texts = []
    for i in range(n):
        tokens = 400.0
        counts = {"n_tokens_nonpunct": tokens, "n_sents": 20.0, "n_finite_verbs": 40.0, "n_pos_NOUN": 100.0,
                  "n_pos_VERB": 50.0, "n_sent_len_sq": 20 * 20.0**2 + 5,
                  # planted signal: 1st-person pronouns mark NA, imperatives mark HI
                  "n_pron_1sg": 30.0 if y[i, 5] else 2.0, "n_imperative_sents": 8.0 if y[i, 6] else 0.0}
        if i % 7 == 0:
            counts["n_sents"] = 1.0  # sd_sent_len missing for these rows
        rows[f"d{seed}_{i}"] = {"counts": counts}
        texts.append(" ".join(f"{lab.lower()}tok" for lab, on in zip(LABELS, y[i], strict=True) if on))
    return TaskData("x", list(rows), texts, y, LABELS), rows


def _cfg():  # type: ignore[no-untyped-def]
    cfg = load_baseline_config(ROOT / "configs/experiments/cpu_baselines.yaml")
    ling = cfg.linguistic.model_copy(update={
        "logreg_grid": cfg.linguistic.logreg_grid.model_copy(update={"C": [1.0], "class_weight": [None]}),
        "combined_alpha": [0.5, 2.0]})
    return cfg.model_copy(update={"linguistic": ling, "n_jobs": 1,
                                  "thresholds": cfg.thresholds.model_copy(update={"per_label_min_dev_positives": 5})})


def test_feature_frame_has_registry_columns_and_nan_for_missing() -> None:
    data, rows = _data(30, 1)
    frame = feature_frame(data.doc_ids, rows)
    assert list(frame.columns) == feature_ids() and frame.shape == (30, len(feature_ids()))
    assert frame["sd_sent_len"].isna().sum() == 5  # rows 0, 7, 14, 21, 28
    with pytest.raises(ValueError, match="no cached features"):
        feature_frame(["unknown"], rows)


def test_b3_learns_planted_signal_and_b4_combines() -> None:
    cfg = _cfg()
    train, tr_rows = _data(400, 1)
    dev, dv_rows = _data(150, 2)
    f_tr, f_dv = feature_frame(train.doc_ids, tr_rows), feature_frame(dev.doc_ids, dv_rows)
    g3, b3 = run_b3(train, dev, f_tr, f_dv, cfg)
    assert len(g3) == 1
    assert b3.tuned["per_label"]["NA"]["f1"] > 0.95 and b3.tuned["per_label"]["HI"]["f1"] > 0.95
    imputer = b3.pipeline.named_steps["ling"].named_steps["impute"]
    assert imputer.n_features_in_ == len(feature_ids())  # fitted on the training frame only
    b1 = {"max_features": 50, "ngram_range": [1, 1], "min_df": 1, "C": 1.0, "class_weight": None}
    g4, b4 = run_b4(train, dev, f_tr, f_dv, cfg, b1)
    assert [g["params"]["alpha"] for g in g4] == [0.5, 2.0]
    assert b4.tuned["macro_f1"] > 0.9  # text tokens carry every label
    reloaded = pickle.loads(pickle.dumps(b4.pipeline))
    assert np.allclose(reloaded.predict_proba(b4_frame(dev, f_dv)), b4.dev_scores)
