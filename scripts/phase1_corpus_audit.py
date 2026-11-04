"""Phase 1 streaming corpus audit for the released CORE TSV files.

Read-only with respect to the source files. Stdlib only so it runs before any
project environment exists. Outputs a JSON audit plus a duplicate manifest.

Usage:
    python -I scripts/phase1_corpus_audit.py --raw data/raw/CORE-corpus --out reports/audit
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path

SPLITS = ("train", "dev", "test")
MAIN = ("SP", "LY", "IN", "IP", "OP", "NA", "HI", "ID")
# Article Table 1 reference grouping (navigation aid; NOT treated as a strict tree).
REFERENCE_GROUPING = {
    "IN": "CM DP DT EN FI IB LT OI RA TR",
    "NA": "HA MA NE ON PB SR SS TB",
    "HI": "FH HT OH RE TS",
    "LY": "OL PO PR SL",
    "IP": "DS ED OE PA",
    "OP": "AD AV LE OB OO RS RV",
    "ID": "DF OF QA RR",
    "SP": "FS IT OS TA TV",
}
SUB_TO_REF_PARENT = {s: p for p, subs in REFERENCE_GROUPING.items() for s in subs.split()}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def normalize_for_fingerprint(text: str) -> str:
    """Normalized fingerprint: NFKC, casefold, collapse all whitespace."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def load_legend(path: Path) -> list[tuple[str, str]]:
    rows = []
    raw = path.read_bytes().decode("utf-8")
    for line in raw.splitlines():
        if not line.strip():
            continue
        code, name = line.split("\t", 1)
        rows.append((code, name))
    return rows


def quantiles(values: list[int]) -> dict:
    if not values:
        return {}
    v = sorted(values)
    q = lambda p: v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]  # noqa: E731
    return {"min": v[0], "p05": q(0.05), "p25": q(0.25), "median": q(0.5),
            "p75": q(0.75), "p95": q(0.95), "p99": q(0.99), "max": v[-1],
            "mean": round(statistics.fmean(v), 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    legend = load_legend(args.raw / "register_label_abbreviations.txt")
    legend_codes = [c for c, _ in legend]
    legend_set = set(legend_codes)
    subcodes = sorted(legend_set - set(MAIN) - {"OTHER"})

    audit: dict = {
        "source_dir": args.raw.as_posix(),  # POSIX form so output hashes do not depend on OS separators
        "file_sha256": {},
        "legend": {"n_codes": len(legend_codes), "codes": legend,
                   "n_main": len(MAIN), "n_sub": len(subcodes), "subcodes": subcodes,
                   "names_with_trailing_space": [c for c, n in legend if n != n.strip()],
                   "reference_grouping_covers_all_subs":
                       sorted(set(subcodes)) == sorted(SUB_TO_REF_PARENT)},
        "splits": {},
    }
    for fname in ["README.md", "LICENSE.txt", "register_label_abbreviations.txt",
                  *[f"{s}.tsv.gz" for s in SPLITS]]:
        audit["file_sha256"][fname] = sha256_file(args.raw / fname)

    id_seen: dict[str, tuple[str, int]] = {}
    id_dupes = []
    raw_hash_groups: dict[str, list] = collections.defaultdict(list)
    norm_hash_groups: dict[str, list] = collections.defaultdict(list)
    global_code_counts = collections.Counter()
    global_combos = collections.Counter()
    sub_cooccur_main = {s: collections.Counter() for s in subcodes}
    sub_without_ref_parent = collections.Counter()
    sub_without_any_main = collections.Counter()
    examples_dp_without_in = []

    for split in SPLITS:
        path = args.raw / f"{split}.tsv.gz"
        st = collections.Counter()
        code_counts = collections.Counter()
        combos = collections.Counter()
        main_combo = collections.Counter()
        n_main_dist = collections.Counter()
        n_sub_dist = collections.Counter()
        wc_list: list[int] = []
        id_len = collections.Counter()
        anomalies = []
        with gzip.open(path, "rb") as fb:
            first = fb.read(4)
        st["utf8_bom"] = int(first.startswith(b"\xef\xbb\xbf"))
        with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
            for lineno, line in enumerate(f, start=1):
                st["lines"] += 1
                if line.endswith("\r\n"):
                    st["crlf_line_endings"] += 1
                body = line.rstrip("\n").rstrip("\r") if line.endswith("\n") else line
                if not line.endswith("\n"):
                    st["last_line_without_newline"] += 1
                parts = body.split("\t")
                nf = len(parts)
                st[f"fields_{nf}"] += 1
                if nf < 3:
                    anomalies.append({"line": lineno, "issue": f"{nf} fields"})
                    continue
                label_str, doc_id = parts[0], parts[1]
                text = "\t".join(parts[2:])  # tabs inside text, if any, are preserved
                if nf > 3:
                    st["rows_with_tab_in_text"] += 1
                st["rows"] += 1
                if label_str != label_str.strip():
                    st["label_field_outer_whitespace"] += 1
                if re.search(r" {2,}", label_str):
                    st["label_field_double_space"] += 1
                labels = label_str.split()
                if len(labels) != len(set(labels)):
                    st["rows_with_repeated_label"] += 1
                unknown = [l for l in labels if l not in legend_set]
                if unknown:
                    anomalies.append({"line": lineno, "id": doc_id, "issue": "unknown codes", "codes": unknown})
                if not labels:
                    st["rows_with_no_labels"] += 1
                # ids
                id_len[len(doc_id)] += 1
                if not doc_id.isdigit():
                    st["non_digit_ids"] += 1
                if doc_id.startswith("0"):
                    st["ids_leading_zero"] += 1
                if doc_id in id_seen:
                    id_dupes.append({"id": doc_id, "first": id_seen[doc_id], "second": (split, lineno)})
                else:
                    id_seen[doc_id] = (split, lineno)
                # text properties
                if text == "":
                    st["empty_text"] += 1
                elif text.strip() == "":
                    st["whitespace_only_text"] += 1
                if '"' in text:
                    st["rows_with_double_quote"] += 1
                if "\r" in text:
                    st["rows_with_cr_in_text"] += 1
                if "\\n" in text:
                    st["rows_with_literal_backslash_n"] += 1
                if "\u2029" in text or "\u2028" in text:
                    st["rows_with_unicode_line_sep"] += 1
                if "\ufffd" in text:
                    st["rows_with_replacement_char"] += 1
                if re.search(r"https?://|www\.", text):
                    st["rows_with_url_string"] += 1
                if "<" in text and re.search(r"</?[a-zA-Z][a-zA-Z0-9]*[ >]", text):
                    st["rows_with_html_like_tag"] += 1
                wc = len(text.split())
                wc_list.append(wc)
                # labels
                lset = set(labels)
                mains = sorted(lset & set(MAIN), key=MAIN.index)
                subs = sorted(lset & set(subcodes))
                n_main_dist[len(mains)] += 1
                n_sub_dist[len(subs)] += 1
                if lset == {"OTHER"}:
                    st["other_only"] += 1
                elif "OTHER" in lset:
                    st["other_with_other_codes"] += 1
                if len(mains) >= 2:
                    st["multi_main"] += 1
                if len(subs) >= 2:
                    st["multi_sub"] += 1
                if len(mains) == 1 and len(subs) >= 2:
                    st["single_main_multi_sub"] += 1
                if subs and not mains:
                    st["sub_without_any_main_row"] += 1
                if mains and not subs:
                    st["main_without_sub"] += 1
                if len(mains) == 1 and not (len(subs) >= 1 and any(SUB_TO_REF_PARENT[s] != mains[0] for s in subs)):
                    st["single_main_consistent_with_ref_grouping"] += 1
                for l in lset:
                    code_counts[l] += 1
                    global_code_counts[l] += 1
                combo = " ".join(sorted(lset, key=lambda c: legend_codes.index(c) if c in legend_set else 999))
                combos[combo] += 1
                global_combos[combo] += 1
                main_combo[" ".join(mains) if mains else ("OTHER" if "OTHER" in lset else "<none>")] += 1
                for s in subs:
                    for m in mains:
                        sub_cooccur_main[s][m] += 1
                    if SUB_TO_REF_PARENT[s] not in lset:
                        sub_without_ref_parent[s] += 1
                    if not mains:
                        sub_without_any_main[s] += 1
                if "DP" in lset and "IN" not in lset and len(examples_dp_without_in) < 10:
                    examples_dp_without_in.append({"split": split, "id": doc_id, "labels": label_str})
                # hashes (exclude empty / whitespace-only texts from duplicate grouping)
                if text.strip():
                    rec = {"split": split, "id": doc_id, "labels": label_str, "line": lineno}
                    raw_hash_groups[hashlib.sha256(text.encode("utf-8")).hexdigest()].append(rec)
                    norm_hash_groups[hashlib.sha256(normalize_for_fingerprint(text).encode("utf-8")).hexdigest()].append(rec)
        audit["splits"][split] = {
            "stats": dict(sorted(st.items())),
            "whitespace_word_count": {"total": sum(wc_list), **quantiles(wc_list)},
            "docs_over_512_ws_words": sum(w > 512 for w in wc_list),
            "docs_under_50_ws_words": sum(w < 50 for w in wc_list),
            "id_length_distribution": dict(sorted(id_len.items())),
            "n_main_labels_distribution": dict(sorted(n_main_dist.items())),
            "n_sub_labels_distribution": dict(sorted(n_sub_dist.items())),
            "code_counts": {c: code_counts.get(c, 0) for c in legend_codes},
            "n_distinct_combinations": len(combos),
            "main_combination_counts": dict(main_combo.most_common()),
            "anomalies": anomalies[:200],
            "n_anomalies": len(anomalies),
        }

    def dup_report(groups: dict) -> dict:
        multi = [g for g in groups.values() if len(g) > 1]
        cross = [g for g in multi if len({r["split"] for r in g}) > 1]
        pair_types = collections.Counter("/".join(sorted({r["split"] for r in g})) for g in cross)
        conflicts = [g for g in multi if len({frozenset(r["labels"].split()) for r in g}) > 1]
        return {"n_groups": len(multi), "n_records_in_groups": sum(len(g) for g in multi),
                "group_size_distribution": dict(collections.Counter(len(g) for g in multi)),
                "n_cross_split_groups": len(cross), "cross_split_types": dict(pair_types),
                "n_label_conflict_groups": len(conflicts),
                "groups": multi}

    audit["global"] = {
        "rows": sum(audit["splits"][s]["stats"]["rows"] for s in SPLITS),
        "unique_ids": len(id_seen),
        "duplicate_ids": id_dupes,
        "observed_codes": sorted(global_code_counts),
        "n_observed_codes": len(global_code_counts),
        "legend_codes_never_observed": sorted(legend_set - set(global_code_counts)),
        "n_distinct_combinations": len(global_combos),
        "combinations_singletons": sum(1 for v in global_combos.values() if v == 1),
        "code_counts": {c: global_code_counts.get(c, 0) for c in legend_codes},
        "whitespace_words_total": sum(audit["splits"][s]["whitespace_word_count"]["total"] for s in SPLITS),
        "whitespace_words_max": max(audit["splits"][s]["whitespace_word_count"]["max"] for s in SPLITS),
        "exact_duplicates_raw": dup_report(raw_hash_groups),
        "exact_duplicates_normalized": dup_report(norm_hash_groups),
    }
    # combos that appear in dev/test but never in train (relevant to label-powerset ablation)
    train_combos = set()
    # recompute quickly from per-split counts is not stored; derive via second light pass on label field only
    split_combos = {}
    for split in SPLITS:
        cs = set()
        with gzip.open(args.raw / f"{split}.tsv.gz", "rt", encoding="utf-8", newline="") as f:
            for line in f:
                lab = line.split("\t", 1)[0].split()
                cs.add(" ".join(sorted(set(lab))))
        split_combos[split] = cs
    train_combos = split_combos["train"]
    audit["global"]["combinations_unseen_in_train"] = {
        s: len(split_combos[s] - train_combos) for s in ("dev", "test")}

    audit["hierarchy"] = {
        "reference_grouping": REFERENCE_GROUPING,
        "sub_without_reference_parent": dict(sub_without_ref_parent.most_common()),
        "sub_without_any_main": dict(sub_without_any_main.most_common()),
        "sub_cooccurring_mains": {s: dict(c.most_common()) for s, c in sub_cooccur_main.items()},
        "examples_dp_without_in": examples_dp_without_in,
    }

    (args.out / "corpus_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    # compact summary to stdout
    g = audit["global"]
    print("rows", g["rows"], "unique_ids", g["unique_ids"], "observed_codes", g["n_observed_codes"],
          "combos", g["n_distinct_combinations"], "ws_words", g["whitespace_words_total"], "max", g["whitespace_words_max"])
    for s in SPLITS:
        sst = audit["splits"][s]["stats"]
        print(s, {k: sst.get(k, 0) for k in ("rows", "empty_text", "whitespace_only_text", "other_only",
                                             "other_with_other_codes", "multi_main", "multi_sub", "single_main_multi_sub",
                                             "sub_without_any_main_row", "main_without_sub", "rows_with_tab_in_text",
                                             "rows_with_double_quote", "rows_with_cr_in_text", "ids_leading_zero",
                                             "rows_with_repeated_label", "label_field_outer_whitespace", "crlf_line_endings")},
              "anomalies", audit["splits"][s]["n_anomalies"], "fields", {k: v for k, v in sst.items() if k.startswith("fields_")})
    for k in ("exact_duplicates_raw", "exact_duplicates_normalized"):
        d = g[k]
        print(k, {kk: d[kk] for kk in d if kk != "groups"})
    print("unseen combos", g["combinations_unseen_in_train"], "never observed legend codes", g["legend_codes_never_observed"])
    print("sub_without_ref_parent", audit["hierarchy"]["sub_without_reference_parent"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
