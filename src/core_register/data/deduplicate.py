"""Exact and near-duplicate grouping of documents (D-07).

Edges between documents:
  * ``exact_raw``  - identical raw text (sha256 of the UTF-8 text);
  * ``exact_norm`` - identical normalised text (NFKC, casefold, whitespace collapsed);
  * ``near``       - word-shingle Jaccard >= threshold, found by MinHash + LSH banding and
                     then **verified by exact Jaccard** on the shingle sets.
Groups are connected components over all edges. Only rows with status OK take part
(empty texts and malformed rows are excluded). Documents shorter than
``min_words_for_near_dup`` normalised words get exact matching only.

This is a text-similarity procedure, not source provenance, and it cannot guarantee
that all overlap is found (e.g. pages sharing only boilerplate are not grouped).
"""

from __future__ import annotations

import hashlib
import random
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from datasketch import MinHash

from core_register.config import DedupConfig
from core_register.data.ingest import Record, Status

_WS = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    return _WS.sub(" ", unicodedata.normalize("NFKC", text).casefold()).strip()


def word_shingles(words: list[str], k: int) -> set[str]:
    if len(words) < k:
        return set()
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, x: str) -> None:
        self.parent.setdefault(x, x)

    def find(self, x: str) -> str:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # deterministic: the smaller id becomes the root
            lo, hi = sorted((ra, rb))
            self.parent[hi] = lo


@dataclass(frozen=True)
class DocMeta:
    doc_id: str
    split: str
    labels: tuple[str, ...]
    n_norm_words: int


@dataclass
class DedupResult:
    group_of: dict[str, str]  # doc_id -> group id, for every participating document
    meta: dict[str, DocMeta]
    edges: dict[str, list[tuple[str, str, float]]] = field(default_factory=dict)  # kind -> (a, b, jaccard)
    excluded: Counter[str] = field(default_factory=Counter)  # status -> count
    candidate_pairs: int = 0
    candidate_jaccard_hist: dict[str, int] = field(default_factory=dict)
    max_lsh_bucket_size: int = 0


RecordSource = Callable[[], Iterator[Record]]


def group_documents(source: RecordSource, cfg: DedupConfig) -> DedupResult:
    """Two streaming passes over ``source()``: (1) hashes and MinHash, (2) shingle sets of LSH candidates."""
    meta: dict[str, DocMeta] = {}
    excluded: Counter[str] = Counter()
    raw_groups: dict[str, list[str]] = defaultdict(list)
    norm_groups: dict[str, list[str]] = defaultdict(list)
    buckets: dict[tuple[int, bytes], list[str]] = defaultdict(list)
    r = cfg.lsh_rows

    # Pass 1
    for rec in source():
        if rec.status is not Status.OK:
            excluded[rec.status.value] += 1
            continue
        if rec.doc_id in meta:
            raise ValueError(f"duplicate document id {rec.doc_id!r}: ids must be unique")
        norm = normalize_text(rec.text)
        words = norm.split()
        meta[rec.doc_id] = DocMeta(rec.doc_id, rec.split, rec.labels, len(words))
        raw_groups[rec.text_sha256].append(rec.doc_id)
        norm_groups[hashlib.sha256(norm.encode("utf-8")).hexdigest()].append(rec.doc_id)
        if len(words) >= cfg.min_words_for_near_dup:
            mh = MinHash(num_perm=cfg.num_perm, seed=cfg.seed)
            mh.update_batch([s.encode("utf-8") for s in word_shingles(words, cfg.shingle_words)])
            hv = np.asarray(mh.hashvalues, dtype=np.uint64)
            for band in range(cfg.lsh_bands):
                buckets[(band, hv[band * r : (band + 1) * r].tobytes())].append(rec.doc_id)

    candidates: set[tuple[str, str]] = set()
    max_bucket = max((len(ids) for ids in buckets.values()), default=0)
    for ids in buckets.values():  # pairs grow quadratically with bucket size; max_bucket is reported
        if len(ids) > 1:
            ids_sorted = sorted(ids)
            for i, a in enumerate(ids_sorted):
                for bb in ids_sorted[i + 1 :]:
                    candidates.add((a, bb))

    # Pass 2: exact Jaccard for candidate pairs only
    needed = {d for pair in candidates for d in pair}
    shingle_sets: dict[str, set[str]] = {}
    if needed:
        for rec in source():
            if rec.status is Status.OK and rec.doc_id in needed:
                shingle_sets[rec.doc_id] = word_shingles(normalize_text(rec.text).split(), cfg.shingle_words)

    hist: Counter[str] = Counter()
    near: list[tuple[str, str, float]] = []
    for a, b in sorted(candidates):
        j = jaccard(shingle_sets[a], shingle_sets[b])
        hist[f"{min(int(j * 10), 9) / 10:.1f}"] += 1
        if j >= cfg.jaccard_threshold:
            near.append((a, b, j))

    def pairs_from(groups: dict[str, list[str]]) -> list[tuple[str, str, float]]:
        out: list[tuple[str, str, float]] = []
        for ids in groups.values():
            if len(ids) > 1:
                s = sorted(ids)
                out.extend((s[0], other, 1.0) for other in s[1:])  # star edges suffice for components
        return out

    edges = {"exact_raw": pairs_from(raw_groups), "exact_norm": pairs_from(norm_groups), "near": near}
    uf = UnionFind()
    for d in meta:
        uf.add(d)
    for kind_edges in edges.values():
        for a, b, _ in kind_edges:
            uf.union(a, b)
    group_of = {d: "G" + uf.find(d) for d in meta}
    return DedupResult(
        group_of=group_of,
        meta=meta,
        edges=edges,
        excluded=excluded,
        candidate_pairs=len(candidates),
        candidate_jaccard_hist=dict(sorted(hist.items())),
        max_lsh_bucket_size=max_bucket,
    )


def _components(result: DedupResult) -> dict[str, list[str]]:
    comps: dict[str, list[str]] = defaultdict(list)
    for d, g in result.group_of.items():
        comps[g].append(d)
    return {g: sorted(m) for g, m in comps.items() if len(m) > 1}


def _group_summary(groups: Iterable[list[str]], meta: dict[str, DocMeta]) -> dict[str, Any]:
    groups = list(groups)
    cross = [g for g in groups if len({meta[d].split for d in g}) > 1]
    return {
        "n_groups": len(groups),
        "n_records_in_groups": sum(len(g) for g in groups),
        "group_size_distribution": {str(k): v for k, v in sorted(Counter(len(g) for g in groups).items())},
        "n_cross_split_groups": len(cross),
        "cross_split_types": dict(
            sorted(Counter("/".join(sorted({meta[d].split for d in g})) for g in cross).items())
        ),
        "n_label_conflict_groups": sum(1 for g in groups if len({meta[d].labels for d in g}) > 1),
    }


def _kind_groups(result: DedupResult, kind: str) -> list[list[str]]:
    uf = UnionFind()
    for a, b, _ in result.edges[kind]:
        uf.add(a)
        uf.add(b)
        uf.union(a, b)
    comps: dict[str, list[str]] = defaultdict(list)
    for d in uf.parent:
        comps[uf.find(d)].append(d)
    return [sorted(m) for m in comps.values()]


def build_report(result: DedupResult, cfg: DedupConfig) -> dict[str, Any]:
    """Counts, IDs, splits, label sets, and Jaccard values only: never text."""
    meta = result.meta
    comps = _components(result)
    near = result.edges["near"]
    rng = random.Random(cfg.sample_seed)
    sample = sorted(rng.sample(near, min(cfg.verification_sample_size, len(near))))
    return {
        "dedup_config": cfg.model_dump(),
        "n_documents_considered": len(meta),
        "n_excluded_by_status": dict(sorted(result.excluded.items())),
        "n_exact_only_short_documents": sum(1 for m in meta.values() if m.n_norm_words < cfg.min_words_for_near_dup),
        "exact_raw": _group_summary(_kind_groups(result, "exact_raw"), meta),
        "exact_normalized": _group_summary(_kind_groups(result, "exact_norm"), meta),
        "limitations": [
            "Text similarity only, not source provenance; detection of all overlap is not guaranteed.",
            "Pages sharing only boilerplate (Phase 1 template groups) are not grouped, by design (D-07).",
            "Thresholds are frozen policy (configs/data/dedup.yaml), not tuned on model performance.",
        ],
        "near_duplicate": {
            "max_lsh_bucket_size": result.max_lsh_bucket_size,
            "n_candidate_pairs": result.candidate_pairs,
            "candidate_jaccard_histogram_floor_0.1": result.candidate_jaccard_hist,
            "n_verified_pairs": len(near),
            "n_verified_pairs_below_1": sum(1 for *_, j in near if j < 1.0),
            **_group_summary(_kind_groups(result, "near"), meta),
        },
        "components": _group_summary(comps.values(), meta),
        "verification_sample": [
            {
                "id_a": a,
                "split_a": meta[a].split,
                "id_b": b,
                "split_b": meta[b].split,
                "jaccard": round(j, 4),
                "same_label_set": meta[a].labels == meta[b].labels,
            }
            for a, b, j in sample
        ],
    }


def manifest_rows(result: DedupResult) -> list[dict[str, Any]]:
    """One row per participating document, sorted by doc_id."""
    size = Counter(result.group_of.values())
    in_kind = {k: {d for e in edges for d in e[:2]} for k, edges in result.edges.items()}
    return [
        {
            "doc_id": d,
            "split": result.meta[d].split,
            "group_id": g,
            "group_size": size[g],
            "exact_raw": d in in_kind["exact_raw"],
            "exact_norm": d in in_kind["exact_norm"],
            "near": d in in_kind["near"],
        }
        for d, g in sorted(result.group_of.items())
    ]
