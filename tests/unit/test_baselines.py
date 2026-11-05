"""Metrics, thresholds, constant baselines, lexical view, sealing guard, and a tiny grid run (synthetic data)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import f1_score

from core_register.config import load_baseline_config
from core_register.data.tasks import SealedTestError, TaskData, load_t1
from core_register.evaluation.metrics import multilabel_report, samples_f1
from core_register.models.baselines import all_negative, most_frequent_set, prevalence_scores
from core_register.models.thresholds import margin_grid, probability_grid, tune_thresholds
from core_register.preprocessing.text import lexical_view
from core_register.training.lexical import constant_baselines, run_linear_grid

ROOT = Path(__file__).resolve().parents[2]
Y = np.array([[1, 0, 0], [1, 1, 0], [0, 0, 0], [0, 1, 1]], dtype=bool)
P = np.array([[1, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0]], dtype=bool)


def test_metrics_hand_computed_and_match_sklearn() -> None:
    rep = multilabel_report(Y, P, None, ["a", "b", "c"])
    # label a: tp2 fp0 fn0 -> 1; b: tp1 fn1 -> 2/3; c: tp0 fn1 -> 0
    assert rep["per_label"]["a"]["f1"] == pytest.approx(1.0)
    assert rep["per_label"]["b"]["f1"] == pytest.approx(2 / 3)
    assert rep["per_label"]["c"]["f1"] == 0.0 and rep["per_label"]["c"]["predicted"] == 0
    assert rep["macro_f1"] == pytest.approx(f1_score(Y, P, average="macro", zero_division=0))
    assert rep["micro_f1"] == pytest.approx(f1_score(Y, P, average="micro", zero_division=0))
    assert rep["weighted_f1"] == pytest.approx(f1_score(Y, P, average="weighted", zero_division=0))
    assert rep["exact_set_accuracy"] == pytest.approx(2 / 4)  # rows 0 and 2


def test_samples_f1_empty_vs_empty_scores_one() -> None:
    # per doc: 1, 2*1/(2+1)=2/3, empty-empty=1, 2*1/(2+1)=2/3
    assert samples_f1(Y, P) == pytest.approx((1 + 2 / 3 + 1 + 2 / 3) / 4)


def test_ap_is_reported_only_for_labels_with_positives() -> None:
    y = np.array([[1, 0], [0, 0], [1, 0]], dtype=bool)
    s = np.array([[0.9, 0.1], [0.2, 0.3], [0.8, 0.2]])
    rep = multilabel_report(y, s >= 0.5, s, ["a", "b"])
    assert rep["per_label"]["a"]["ap"] == pytest.approx(1.0) and rep["per_label"]["b"]["ap"] is None
    assert rep["macro_ap"] == pytest.approx(1.0)


def test_threshold_tuning_global_then_shrunk_per_label() -> None:
    rng = np.random.default_rng(0)
    y = np.zeros((200, 2), dtype=bool)
    y[:100, 0] = True
    y[:10, 1] = True  # too few positives for a per-label threshold
    s = np.where(y, 0.7, 0.2) + rng.normal(0, 0.01, y.shape)
    thr = tune_thresholds(y, s, probability_grid(0.05, 0.95, 0.05), min_pos=50, shrinkage=0.5)
    assert thr.per_label_tuned == (True, False)
    assert thr.per_label[1] == thr.global_threshold
    assert (thr.apply(s) == y).all()
    assert len(margin_grid(s, 0.05, 0.95, 0.05)) <= 19


def test_constant_baselines() -> None:
    ytr = np.array([[1, 0], [1, 0], [0, 1]], dtype=bool)
    assert np.allclose(prevalence_scores(ytr, 2), [[2 / 3, 1 / 3]] * 2)
    assert (most_frequent_set(ytr, 2) == [[True, False]] * 2).all()
    assert not all_negative(3, 2).any()


def test_lexical_view_masks_lowercases_and_windows() -> None:
    text = "Visit WWW.Example.com or mail Me@Site.org now Ｆｕｌｌ"
    assert lexical_view(text, 1000) == "visit urltoken or mail emailtoken now full"
    assert lexical_view("a b c d", 2) == "a b"


def test_loader_refuses_sealed_test() -> None:
    with pytest.raises(SealedTestError):
        load_t1(None, None, Path("x"), ["train", "test"], str)  # type: ignore[arg-type]


def _synthetic(n: int, seed: int) -> TaskData:
    rng = np.random.default_rng(seed)
    labels = ["SP", "LY", "IN", "IP", "OP", "NA", "HI", "ID"]
    vocab = {lab: [f"{lab.lower()}word{i}" for i in range(5)] for lab in labels}
    texts, ys = [], []
    for _ in range(n):
        row = rng.random(8) < 0.3
        if not row.any():
            row[rng.integers(8)] = True
        words = [w for lab, on in zip(labels, row, strict=True) if on for w in rng.choice(vocab[lab], 4)]
        words += [f"noise{rng.integers(50)}" for _ in range(6)]
        texts.append(" ".join(words))
        ys.append(row)
    return TaskData("x", [str(i) for i in range(n)], texts, np.asarray(ys), labels)


def test_tiny_grid_runs_and_separates_signal() -> None:
    cfg = load_baseline_config(ROOT / "configs/experiments/cpu_baselines.yaml")
    small = cfg.model_copy(update={
        "tfidf_grid": cfg.tfidf_grid.model_copy(update={"max_features": [100], "ngram_range": [(1, 1)], "min_df": 1}),
        "logreg_grid": cfg.logreg_grid.model_copy(update={"C": [1.0], "class_weight": [None]}),
        "svm_grid": cfg.svm_grid.model_copy(update={"C": [1.0], "class_weight": [None]}),
        "thresholds": cfg.thresholds.model_copy(update={"per_label_min_dev_positives": 5}),
        "n_jobs": 1,
    })
    train, dev = _synthetic(300, 1), _synthetic(120, 2)
    grid, best = run_linear_grid(train, dev, small)
    assert len(grid) == 2 and set(best) == {"logreg", "svm"}
    assert best["logreg"].tuned["macro_f1"] > 0.9  # the synthetic signal is easy
    b0 = constant_baselines(train, dev)
    assert b0["B0_all_negative"]["macro_f1"] == 0.0
    assert best["logreg"].tuned["macro_f1"] > b0["B0_most_frequent_set"]["macro_f1"]


def test_experiment_config_matches_d09() -> None:
    cfg = load_baseline_config(ROOT / "configs/experiments/cpu_baselines.yaml")
    assert cfg.logreg_grid.C == cfg.svm_grid.C == [0.1, 1.0, 10.0]
    assert cfg.logreg_grid.class_weight == [None, "balanced"]
    assert cfg.tfidf_grid.max_features == [50000, 200000] and cfg.tfidf_grid.min_df == 3
    assert [tuple(r) for r in cfg.tfidf_grid.ngram_range] == [(1, 1), (1, 2)]
