"""B0 constant baselines, fitted on training labels only (methodology section 7)."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]


def prevalence_scores(y_train: Array, n: int) -> Array:
    """Every document gets the training prevalence of each label as its score (an AP reference)."""
    return np.tile(np.asarray(y_train, dtype=float).mean(axis=0), (n, 1))


def most_frequent_set(y_train: Array, n: int) -> Array:
    """Predict the most frequent training label set for every document (ties broken by first occurrence)."""
    sets = Counter(map(tuple, np.asarray(y_train, dtype=bool)))
    best = np.asarray(max(sets.items(), key=lambda kv: kv[1])[0], dtype=bool)
    return np.tile(best, (n, 1))


def all_negative(n: int, n_labels: int) -> Array:
    """Diagnostic: predicts no label at all."""
    return np.zeros((n, n_labels), dtype=bool)
