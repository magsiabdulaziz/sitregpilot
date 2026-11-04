"""Phase 1 cheap overlap indicator: documents sharing an identical normalized
first-50 or last-50 word sequence (docs >= 60 words). This is a boilerplate /
template indicator, NOT a near-duplicate detector and NOT source provenance.

Usage: python -I scripts/phase1_template_overlap.py --raw data/raw/CORE-corpus --out reports/audit
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import re
import unicodedata
from pathlib import Path

N, MIN_LEN = 50, 60


def norm(t: str) -> list[str]:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t).casefold()).split()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    keys = {"first50": collections.defaultdict(list), "last50": collections.defaultdict(list)}
    for s in ("train", "dev", "test"):
        with gzip.open(a.raw / f"{s}.tsv.gz", "rt", encoding="utf-8", newline="") as f:
            for line in f:
                parts = line.rstrip("\r\n").split("\t", 2)
                if len(parts) != 3:  # malformed row: skip (reported by phase1_corpus_audit.py)
                    continue
                lab, i, t = parts
                w = norm(t)
                if len(w) < MIN_LEN:
                    continue
                rec = (s, i, lab)
                keys["first50"][" ".join(w[:N])].append(rec)
                keys["last50"][" ".join(w[-N:])].append(rec)
    out = {"definition": f"identical normalized first/last {N} words; docs with >= {MIN_LEN} whitespace words"}
    for name, d in keys.items():
        g = [v for v in d.values() if len(v) > 1]
        cross = [v for v in g if len({x[0] for x in v}) > 1]
        top = sorted(g, key=len, reverse=True)[:10]
        out[name] = {
            "groups": len(g), "records": sum(map(len, g)), "max_group": max(map(len, g), default=0),
            "cross_split_groups": len(cross),
            "dev_test_records_in_cross_split_groups": sum(1 for v in cross for x in v if x[0] != "train"),
            "label_set_conflict_groups": sum(1 for v in g if len({frozenset(x[2].split()) for x in v}) > 1),
            # labels only, no text, for the largest groups
            "largest_groups_label_profile": [
                {"size": len(v), "splits": dict(collections.Counter(x[0] for x in v)),
                 "top_labels": collections.Counter(x[2] for x in v).most_common(3)} for v in top],
        }
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "template_overlap_indicator.json").write_text(json.dumps(out, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "largest_groups_label_profile"}
                      for k, v in out.items() if k != "definition"}, indent=1))


if __name__ == "__main__":
    main()
