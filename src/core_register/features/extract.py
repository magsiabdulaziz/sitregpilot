"""Count extraction from spaCy parses, feature computation, and a resumable cached corpus run.

The window is the first ``window_words`` whitespace tokens of the raw text, re-joined with single spaces
(case and punctuation preserved; D-06). Counts are stored, not only rates, so any feature can be recomputed
and audited. Cache key = sha256(window text) + extractor version + spaCy model version.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from spacy.language import Language
from spacy.tokens import Doc, Token

from core_register.features.registry import ALL_FEATURES, FEATURES, MATTR_WINDOW, REGISTRY_VERSION

EXTRACTOR_VERSION = f"1.0.0+registry{REGISTRY_VERSION}"

POS_TAGS = ("NOUN", "PROPN", "VERB", "ADJ", "ADV", "PRON", "DET", "CCONJ", "SCONJ", "ADP", "NUM", "INTJ")
CONTENT = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}
NON_WORD_POS = {"PUNCT", "SYM", "SPACE"}
PRONOUNS = {
    "n_pron_1sg": {"i", "me", "my", "mine", "myself"},
    "n_pron_1pl": {"we", "us", "our", "ours", "ourselves"},
    "n_pron_2": {"you", "your", "yours", "yourself", "yourselves"},
    "n_pron_3": {"he", "him", "his", "himself", "she", "her", "hers", "herself",
                 "they", "them", "their", "theirs", "themselves"},
    "n_pron_it": {"it", "its", "itself"},
}
DEMONSTRATIVES = {"this", "that", "these", "those"}
MODALS = {
    "n_modal_possibility": {"can", "ca", "could", "may", "might"},
    "n_modal_necessity": {"must", "should", "ought"},
    "n_modal_prediction": {"will", "wo", "would", "shall", "sha", "'ll", "'d"},
}
WH_WORDS = {"what", "who", "whom", "whose", "which", "when", "where", "why", "how"}
NOMINAL_SUFFIXES = ("tion", "sion", "ment", "ness", "ity")
SUBJECT_DEPS = {"nsubj", "nsubjpass", "expl", "csubj", "csubjpass"}


def make_window(text: str, window_words: int) -> tuple[str, bool]:
    words = text.split()
    return " ".join(words[:window_words]), len(words) > window_words


def _is_word(t: Token) -> bool:
    return t.pos_ not in NON_WORD_POS and not t.is_space


def mattr(tokens: list[str], window: int = MATTR_WINDOW) -> float:
    """Moving-average type-token ratio; NaN if fewer than ``window`` tokens."""
    n = len(tokens)
    if n < window:
        return math.nan
    counts: Counter[str] = Counter(tokens[:window])
    total = len(counts)
    for i in range(window, n):
        out, inc = tokens[i - window], tokens[i]
        counts[out] -= 1
        if counts[out] == 0:
            del counts[out]
        counts[inc] += 1
        total += len(counts)
    return total / ((n - window + 1) * window)


def count_doc(doc: Doc) -> dict[str, float]:
    c: Counter[str] = Counter()
    words: list[str] = []
    for t in doc:
        if not _is_word(t):
            continue
        low = t.lower_
        words.append(low)
        c["n_tokens_nonpunct"] += 1
        c["n_chars_nonpunct"] += len(t.text)
        if t.pos_ in POS_TAGS:
            c[f"n_pos_{t.pos_}"] += 1
        if t.pos_ in CONTENT:
            c["n_content"] += 1
        if t.pos_ in ("PRON", "DET"):
            for key, forms in PRONOUNS.items():
                if low in forms:
                    c[key] += 1
        if low in DEMONSTRATIVES:
            if t.pos_ == "PRON":
                c["n_dem_pron"] += 1
            elif t.pos_ == "DET":
                c["n_dem_det"] += 1
        if t.pos_ in ("VERB", "AUX") and "Fin" in t.morph.get("VerbForm", []):
            c["n_finite_verbs"] += 1
            tense = t.morph.get("Tense", [])
            if "Past" in tense:
                c["n_tense_past"] += 1
            elif "Pres" in tense:
                c["n_tense_pres"] += 1
        if t.tag_ == "MD":
            for key, forms in MODALS.items():
                if low in forms:
                    c[key] += 1
        if t.dep_ == "aux" and t.lemma_.lower() == "have" and t.head.tag_ == "VBN":
            c["n_perfect"] += 1
        if t.dep_ == "aux" and t.lemma_.lower() == "be" and t.head.tag_ == "VBG":
            c["n_progressive"] += 1
        if t.dep_ == "auxpass":
            c["n_passive"] += 1
        if t.dep_ == "neg":
            c["n_neg"] += 1
        if t.dep_ == "relcl":
            c["n_relcl"] += 1
        if t.dep_ == "advcl":
            c["n_advcl"] += 1
        if t.dep_ in ("ccomp", "xcomp"):
            c["n_ccomp_xcomp"] += 1
        if t.dep_ == "amod":
            c["n_amod"] += 1
        if t.pos_ == "NOUN" and len(low) >= 7 and low.endswith(NOMINAL_SUFFIXES):
            c["n_nominalisation"] += 1
    c["n_pos_NOUN_PROPN"] = c["n_pos_NOUN"] + c["n_pos_PROPN"]
    for sent in doc.sents:
        toks = [t for t in sent if _is_word(t)]
        if not toks:
            continue
        c["n_sents"] += 1
        last = [t for t in sent if not t.is_space]
        is_q = bool(last) and "?" in last[-1].text
        if is_q:
            c["n_qmark_sents"] += 1
            first = toks[0]
            if first.pos_ == "AUX" or first.lower_ in WH_WORDS:
                c["n_interrogative_sents"] += 1
        # imperative heuristic: skip leading adverbs/interjections/conjunctions ("Then add ...", "Now open ...")
        lead = next((t for t in toks if t.pos_ not in ("ADV", "INTJ", "CCONJ")), None)
        if lead is not None and lead.tag_ == "VB" and not any(ch.dep_ in SUBJECT_DEPS for ch in lead.children):
            c["n_imperative_sents"] += 1
    out: dict[str, float] = {k: float(v) for k, v in c.items()}
    out["mattr_500"] = mattr(words)
    return out


def features_from_counts(counts: dict[str, float]) -> dict[str, float]:
    feats: dict[str, float] = {}
    for f in FEATURES:
        den = counts.get(f.denominator, 0.0)
        feats[f.id] = math.nan if den < f.min_denominator else f.scale * counts.get(f.numerator, 0.0) / den
    feats["mattr_500"] = counts.get("mattr_500", math.nan)
    return feats


def feature_ids() -> list[str]:
    return [f.id for f in ALL_FEATURES]


def cache_key(window_text: str, model_version: str) -> str:
    h = hashlib.sha256(window_text.encode("utf-8")).hexdigest()
    return f"{h}:{EXTRACTOR_VERSION}:{model_version}"


def read_cache(path: Path) -> dict[str, dict[str, Any]]:
    """doc_id -> cached row. Tolerates a truncated final line from an interrupted run."""
    rows: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows[row["doc_id"]] = row
    return rows


def extract_to_cache(
    docs: Iterable[tuple[str, str]],
    nlp: Language,
    cache_path: Path,
    window_words: int,
    n_process: int = 1,
    batch_size: int = 32,
) -> dict[str, int]:
    """Parse (doc_id, raw text) pairs not yet cached; append one JSON line per document. Resumable."""
    model_version = f"{nlp.meta['lang']}_{nlp.meta['name']}-{nlp.meta['version']}"
    cached = read_cache(cache_path)
    todo: list[tuple[str, str, bool]] = []
    stats = Counter[str]()
    for doc_id, text in docs:
        window, truncated = make_window(text, window_words)
        key = cache_key(window, model_version)
        if doc_id in cached and cached[doc_id]["key"] == key:
            stats["cached"] += 1
            continue
        todo.append((doc_id, window, truncated))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # An interrupted run can leave a torn final line: start a fresh line so new rows stay parseable.
    if cache_path.is_file() and cache_path.stat().st_size > 0:
        with cache_path.open("rb") as fr:
            fr.seek(-1, 2)
            torn = fr.read(1) != b"\n"
        if torn:
            with cache_path.open("ab") as fw:
                fw.write(b"\n")

    def texts() -> Iterator[str]:
        for _, w, _ in todo:
            yield w

    with cache_path.open("a", encoding="utf-8", newline="\n") as out:
        for (doc_id, window, truncated), doc in zip(todo, nlp.pipe(texts(), n_process=n_process, batch_size=batch_size),
                                                    strict=True):
            row = {
                "doc_id": doc_id,
                "key": cache_key(window, model_version),
                "truncated": truncated,
                "n_window_ws_words": len(window.split()),
                "counts": count_doc(doc),
            }
            out.write(json.dumps(row, allow_nan=True) + "\n")
            stats["parsed"] += 1
            if stats["parsed"] % 200 == 0:
                out.flush()
    return dict(stats)
