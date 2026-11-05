"""Multilabel metrics with explicit conventions (methodology section 8).

* zero_division = 0 for per-label P/R/F1 (a label never predicted has precision 0).
* samples-F1: a document with empty gold **and** empty prediction scores 1; otherwise standard per-document F1.
* exact-set accuracy: predicted set == gold set.
* AP = scikit-learn ``average_precision_score`` (step-wise; *not* trapezoidal PR-AUC). Macro over labels with
  at least one positive; micro over all label-document pairs.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import average_precision_score, precision_recall_fscore_support

Array = NDArray[Any]


def samples_f1(y_true: Array, y_pred: Array) -> float:
    tp = (y_true & y_pred).sum(axis=1)
    denom = y_true.sum(axis=1) + y_pred.sum(axis=1)
    per_doc = np.where(denom == 0, 1.0, 2.0 * tp / np.maximum(denom, 1))
    return float(per_doc.mean())


def multilabel_report(y_true: Array, y_pred: Array, scores: Array | None, labels: list[str]) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)
    out: dict[str, Any] = {
        "n_documents": int(y_true.shape[0]),
        "macro_f1": float(np.mean(f)),
        "micro_f1": float(precision_recall_fscore_support(y_true, y_pred, average="micro", zero_division=0)[2]),
        "weighted_f1": float(np.average(f, weights=s)) if s.sum() else 0.0,
        "samples_f1": samples_f1(y_true, y_pred),
        "exact_set_accuracy": float((y_true == y_pred).all(axis=1).mean()),
        "per_label": {
            lab: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i]),
                  "predicted": int(y_pred[:, i].sum())}
            for i, lab in enumerate(labels)
        },
    }
    if scores is not None:
        has_pos = y_true.sum(axis=0) > 0
        aps = [float(average_precision_score(y_true[:, i], scores[:, i])) for i in range(len(labels)) if has_pos[i]]
        out["macro_ap"] = float(np.mean(aps)) if aps else float("nan")
        out["micro_ap"] = float(average_precision_score(y_true.ravel(), np.asarray(scores).ravel()))
        for i, lab in enumerate(labels):
            out["per_label"][lab]["ap"] = (float(average_precision_score(y_true[:, i], scores[:, i]))
                                           if has_pos[i] else None)
    return out
