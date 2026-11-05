"""Task datasets built from the sealed split manifest and the raw corpus.

T1 = 8 main registers (D-03: observed main codes, no closure), functional cohort (D-04), controlled_split.
Loading the ``test`` partition is refused unless ``allow_test=True``, which only the Phase 5 evaluation may set.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from core_register.config import SPLITS, DataConfig
from core_register.data.ingest import iter_records
from core_register.data.labels import LabelSchema


class SealedTestError(RuntimeError):
    """Raised when development code asks for the sealed test partition."""


@dataclass(frozen=True)
class TaskData:
    partition: str
    doc_ids: list[str]
    texts: list[str]
    y: NDArray[Any]  # (n_docs, n_labels) bool
    labels: list[str]


def load_t1(
    cfg: DataConfig,
    schema: LabelSchema,
    manifest_path: Path,
    partitions: Iterable[str],
    text_view: Callable[[str], str],
    *,
    allow_test: bool = False,
) -> dict[str, TaskData]:
    parts = list(partitions)
    if "test" in parts and not allow_test:
        raise SealedTestError("the test partition is sealed until Phase 5 (methodology section 5.4)")
    with manifest_path.open(encoding="utf-8", newline="") as f:
        want = {r["doc_id"]: r["controlled_partition"] for r in csv.DictReader(f)
                if r["controlled_partition"] in parts and r["cohort"] == "functional"}
    labels = list(schema.main)
    acc: dict[str, tuple[list[str], list[str], list[list[bool]]]] = {p: ([], [], []) for p in parts}
    for split in SPLITS:
        for rec in iter_records(cfg.split_path(split), split, schema):
            part = want.get(rec.doc_id)
            if part is None:
                continue
            row = [lab in rec.labels for lab in labels]
            if not any(row):
                raise ValueError(f"{rec.doc_id}: functional document without a main label")
            ids, texts, ys = acc[part]
            ids.append(rec.doc_id)
            texts.append(text_view(rec.text))
            ys.append(row)
    out = {}
    for p, (ids, texts, ys) in acc.items():
        order = np.argsort(ids, kind="stable")  # deterministic order by doc_id
        out[p] = TaskData(p, [ids[i] for i in order], [texts[i] for i in order],
                          np.asarray(ys, dtype=bool)[order] if ys else np.zeros((0, len(labels)), bool), labels)
    return out
