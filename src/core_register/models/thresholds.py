"""Decision thresholds tuned on dev (methodology section 7).

1. A **global** threshold maximising dev macro-F1 over a candidate grid.
2. A **per-label** threshold (maximising that label's dev F1) only for labels with at least ``min_pos`` dev positives,
   then shrunk toward the global threshold: t_l = (1 - s) * t_label + s * t_global. Other labels use the global one.
Scores can be probabilities (LR) or raw margins (SVM); the same procedure applies to both score types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]


def _f1(y: Array, pred: Array) -> float:
    tp = float((y & pred).sum())
    denom = float(y.sum() + pred.sum())
    return 0.0 if denom == 0 else 2.0 * tp / denom


@dataclass(frozen=True)
class Thresholds:
    global_threshold: float
    per_label: tuple[float, ...]
    per_label_tuned: tuple[bool, ...]

    def apply(self, scores: Array) -> Array:
        return np.asarray(scores) >= np.asarray(self.per_label)[None, :]

    def to_dict(self, labels: list[str]) -> dict[str, Any]:
        return {
            "global": self.global_threshold,
            "per_label": {lab: {"threshold": t, "tuned": tuned}
                          for lab, t, tuned in zip(labels, self.per_label, self.per_label_tuned, strict=True)},
        }


def tune_thresholds(y_true: Array, scores: Array, candidates: Array, min_pos: int, shrinkage: float) -> Thresholds:
    y = np.asarray(y_true, dtype=bool)
    s = np.asarray(scores, dtype=float)
    best_t, best = float(candidates[0]), -1.0
    for t in candidates:  # first maximum wins (deterministic)
        macro = float(np.mean([_f1(y[:, j], s[:, j] >= t) for j in range(y.shape[1])]))
        if macro > best:
            best_t, best = float(t), macro
    per, tuned = [], []
    for j in range(y.shape[1]):
        if y[:, j].sum() >= min_pos:
            f1s = [_f1(y[:, j], s[:, j] >= t) for t in candidates]
            t_label = float(candidates[int(np.argmax(f1s))])
            per.append((1.0 - shrinkage) * t_label + shrinkage * best_t)
            tuned.append(True)
        else:
            per.append(best_t)
            tuned.append(False)
    return Thresholds(best_t, tuple(per), tuple(tuned))


def probability_grid(start: float, stop: float, step: float) -> Array:
    return np.round(np.arange(start, stop + step / 2, step), 10)


def margin_grid(scores: Array, start: float, stop: float, step: float) -> Array:
    return np.unique(np.quantile(np.asarray(scores).ravel(), probability_grid(start, stop, step)))
