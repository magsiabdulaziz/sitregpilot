"""Released and controlled split manifests (D-07; methodology section 5).

* ``released_split``: the original file membership of every input row, never changed.
* ``controlled_split``: the same memberships with records *removed* (never moved) so that no
  duplicate group spans two partitions:
    - a group spanning partitions keeps only its members in the highest-priority partition
      (test > dev > train); the others are excluded as ``cross_split_duplicate``;
    - in train, a group whose members carry different label sets is quarantined entirely
      (``train_label_conflict``); otherwise only the lowest doc_id is kept
      (``within_train_duplicate`` for the rest);
    - dev/test duplicates are all kept; they share one ``group_id``, which is the resampling unit;
    - rows whose status is not OK are excluded (``status_<STATUS>``).
* Template keys (identical normalised first/last N words) are computed from *training* documents
  only and give a ``template_seen`` diagnostic flag for dev/test documents. They never cause exclusion.

The manifest carries IDs, statuses, partitions, reasons, groups and flags: no text and no labels.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from core_register.config import SPLITS, SplitConfig
from core_register.data.deduplicate import normalize_text
from core_register.data.ingest import Record, Status
from core_register.data.labels import LabelSchema

MANIFEST_FIELDS = [
    "doc_id",
    "released_split",
    "status",
    "cohort",
    "group_id",
    "group_size",
    "controlled_partition",
    "controlled_reason",
    "template_seen_released",
    "template_seen_controlled",
]


@dataclass(frozen=True)
class _Doc:
    doc_id: str
    split: str
    status: Status
    labels: tuple[str, ...]
    template_keys: tuple[str, ...]  # sha256 of the first/last-N normalised words; empty if too short


def _template_keys(text: str, cfg: SplitConfig) -> tuple[str, ...]:
    words = normalize_text(text).split()
    if len(words) < cfg.template_min_words:
        return ()
    n = cfg.template_words
    return (
        "F" + hashlib.sha256(" ".join(words[:n]).encode("utf-8")).hexdigest(),
        "L" + hashlib.sha256(" ".join(words[-n:]).encode("utf-8")).hexdigest(),
    )


def _cohort(doc: _Doc, schema: LabelSchema) -> str:
    if doc.status is Status.EMPTY_INPUT:
        return "empty"
    if doc.status is not Status.OK:
        return "invalid"
    return "other_only" if doc.labels == (schema.other_code,) else "functional"


def build_split_manifest(
    records: Iterable[Record],
    group_of: Mapping[str, str],
    schema: LabelSchema,
    cfg: SplitConfig,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    docs: list[_Doc] = []
    seen: set[str] = set()
    for rec in records:
        if rec.status is Status.MALFORMED:
            raise ValueError(f"{rec.source_file}:{rec.line_no}: MALFORMED row has no usable id ({rec.issue})")
        if rec.doc_id in seen:
            raise ValueError(f"duplicate document id {rec.doc_id!r}")
        seen.add(rec.doc_id)
        keys = _template_keys(rec.text, cfg) if rec.status is Status.OK else ()
        docs.append(_Doc(rec.doc_id, rec.split, rec.status, rec.labels, keys))

    by_id = {d.doc_id: d for d in docs}
    ok_ids = {d.doc_id for d in docs if d.status is Status.OK}
    if set(group_of) != ok_ids:
        missing, extra = sorted(ok_ids - set(group_of))[:5], sorted(set(group_of) - ok_ids)[:5]
        raise ValueError(f"dedup groups do not cover exactly the OK documents (missing {missing}, extra {extra})")

    group_id = {d.doc_id: group_of.get(d.doc_id, "G" + d.doc_id) for d in docs}
    members: dict[str, list[str]] = defaultdict(list)
    for d in docs:
        members[group_id[d.doc_id]].append(d.doc_id)

    partition: dict[str, str] = {}
    reason: dict[str, str] = {}
    for d in docs:
        if d.status is not Status.OK:
            partition[d.doc_id], reason[d.doc_id] = "excluded", f"status_{d.status.value}"
    for ids in members.values():
        ok = sorted(i for i in ids if by_id[i].status is Status.OK)
        if not ok:
            continue
        keep_split = next(s for s in cfg.partition_priority if any(by_id[i].split == s for i in ok))
        kept = [i for i in ok if by_id[i].split == keep_split]
        for i in ok:
            if i not in kept:
                partition[i], reason[i] = "excluded", "cross_split_duplicate"
        if keep_split == "train" and len(kept) > 1:
            if len({by_id[i].labels for i in kept}) > 1:
                for i in kept:
                    partition[i], reason[i] = "excluded", "train_label_conflict"
                continue
            for i in kept[1:]:  # kept is sorted: kept[0] is the lowest doc_id
                partition[i], reason[i] = "excluded", "within_train_duplicate"
            kept = kept[:1]
        for i in kept:
            partition[i], reason[i] = keep_split, "kept"

    released_train_keys = {k for d in docs if d.split == "train" and d.status is Status.OK for k in d.template_keys}
    controlled_train_keys = {k for d in docs if partition[d.doc_id] == "train" for k in d.template_keys}

    def seen_flag(d: _Doc, train_keys: set[str], applies: bool) -> str:
        if d.split == "train" or not applies or not d.template_keys:
            return ""  # not applicable: train documents, non-applicable cohort, or too short for keys
        return "true" if any(k in train_keys for k in d.template_keys) else "false"

    size = Counter(group_id.values())
    rows = [
        {
            "doc_id": d.doc_id,
            "released_split": d.split,
            "status": d.status.value,
            "cohort": _cohort(d, schema),
            "group_id": group_id[d.doc_id],
            "group_size": str(size[group_id[d.doc_id]]),
            "controlled_partition": partition[d.doc_id],
            "controlled_reason": reason[d.doc_id],
            "template_seen_released": seen_flag(d, released_train_keys, d.status is Status.OK),
            "template_seen_controlled": seen_flag(d, controlled_train_keys, partition[d.doc_id] != "excluded"),
        }
        for d in sorted(docs, key=lambda x: x.doc_id)
    ]
    return rows, _report(rows, by_id, schema)


def _report(rows: list[dict[str, str]], by_id: Mapping[str, _Doc], schema: LabelSchema) -> dict[str, Any]:
    parts = [*SPLITS, "excluded"]
    # group disjointness: no group may have kept members in two controlled partitions
    group_parts: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        if r["controlled_partition"] != "excluded":
            group_parts[r["group_id"]].add(r["controlled_partition"])
    violations = sorted(g for g, p in group_parts.items() if len(p) > 1)
    moved = [r["doc_id"] for r in rows if r["controlled_partition"] not in ("excluded", r["released_split"])]

    def label_table(key: str, values: list[str]) -> dict[str, dict[str, int]]:
        table: dict[str, dict[str, int]] = {}
        for code in schema.codes:
            counts = Counter(r[key] for r in rows if code in by_id[r["doc_id"]].labels)
            table[code] = {v: counts.get(v, 0) for v in values}
        return table

    exclusions = Counter((r["released_split"], r["controlled_reason"]) for r in rows if r["controlled_partition"] == "excluded")
    cohorts = Counter((r["controlled_partition"], r["cohort"]) for r in rows)
    template = Counter(
        (r["released_split"], col, r[col]) for r in rows for col in ("template_seen_released", "template_seen_controlled")
        if r["released_split"] != "train"
    )
    test_released = sorted(r["doc_id"] for r in rows if r["released_split"] == "test")
    test_controlled = sorted(r["doc_id"] for r in rows if r["controlled_partition"] == "test")
    return {
        "n_input_rows": len(rows),
        "assertions": {
            "every_row_accounted": len(rows) == len(by_id),
            "controlled_group_disjoint": not violations,
            "controlled_group_disjoint_violations": violations[:20],
            "no_record_moved_between_partitions": not moved,
        },
        "released_split_sizes": dict(Counter(r["released_split"] for r in rows)),
        "controlled_partition_sizes": {p: sum(1 for r in rows if r["controlled_partition"] == p) for p in parts},
        "exclusions_by_released_split_and_reason": {f"{s}/{why}": n for (s, why), n in sorted(exclusions.items())},
        "cohort_by_controlled_partition": {f"{p}/{c}": n for (p, c), n in sorted(cohorts.items())},
        "template_seen_dev_test": {f"{s}/{col}/{v or 'n/a'}": n for (s, col, v), n in sorted(template.items())},
        "label_counts_released": label_table("released_split", list(SPLITS)),
        "label_counts_controlled": label_table("controlled_partition", parts),
        "sealed_test": {
            "released_test_ids_sha256": _ids_sha(test_released),
            "released_test_n": len(test_released),
            "controlled_test_ids_sha256": _ids_sha(test_controlled),
            "controlled_test_n": len(test_controlled),
        },
    }


def _ids_sha(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()
