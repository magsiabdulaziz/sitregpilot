"""Versioned feature registry (methodology section 6).

Every feature is a ratio ``scale * count[numerator] / count[denominator]`` of raw counts stored by the
extractor (``features.extract``), except MATTR, which is computed directly. When the denominator is 0,
or below ``min_denominator``, the value is **missing** (NaN plus an indicator), never 0. Imputation and
scaling happen later, inside train-only pipelines.

Construct labels are interpretive aids, not causal claims. ``source`` cites where the operationalisation
is motivated. Entries marked UNVERIFIED still need a page-level check against the cited work. Tagger and
parser outputs (spaCy ``en_core_web_sm``) are measurements with error, not gold annotation.
"""

from __future__ import annotations

from dataclasses import dataclass

REGISTRY_VERSION = "1.0.0"

PER_1K = 1000.0
NONPUNCT = "n_tokens_nonpunct"  # tokens that are not punctuation, space or symbol-only
SENTS = "n_sents"
FINITE = "n_finite_verbs"  # VerbForm=Fin on VERB/AUX: finite-clause proxy
NOUNS = "n_pos_NOUN"

UNVERIFIED = "UNVERIFIED: motivated by Biber (1988) / Biber & Conrad (2009) via the primary article's references"


@dataclass(frozen=True)
class FeatureSpec:
    id: str
    family: str
    construct: str
    numerator: str
    denominator: str
    scale: float = PER_1K
    min_denominator: int = 1
    ambiguities: str = ""
    source: str = UNVERIFIED


def _pos(tag: str, construct: str) -> FeatureSpec:
    return FeatureSpec(f"pos_{tag.lower()}", "pos", construct, f"n_pos_{tag}", NONPUNCT,
                       ambiguities="tagger error on web text; titles fused into first sentence")


FEATURES: tuple[FeatureSpec, ...] = (
    # --- POS proportions (per 1,000 non-punctuation tokens)
    _pos("NOUN", "information packaging (nominal)"),
    _pos("PROPN", "reference to named entities"),
    _pos("VERB", "clausal / verbal style"),
    _pos("ADJ", "attributive elaboration"),
    _pos("ADV", "stance and circumstance"),
    _pos("PRON", "involvement / interaction"),
    _pos("DET", "nominal reference"),
    _pos("CCONJ", "phrasal and clausal coordination"),
    _pos("SCONJ", "subordination"),
    _pos("ADP", "prepositional elaboration"),
    _pos("NUM", "quantification"),
    _pos("INTJ", "interactive / spoken style"),
    # --- pronouns (lemma lists intersected with PRON or possessive-determiner tags)
    FeatureSpec("pron_1sg", "pronoun", "speaker reference", "n_pron_1sg", NONPUNCT,
                ambiguities="quoted speech counts as the writer's own"),
    FeatureSpec("pron_1pl", "pronoun", "inclusive/exclusive group reference", "n_pron_1pl", NONPUNCT),
    FeatureSpec("pron_2", "pronoun", "addressee reference", "n_pron_2", NONPUNCT,
                ambiguities="generic 'you' is not distinguished from addressee 'you'"),
    FeatureSpec("pron_3", "pronoun", "third-person reference (narration)", "n_pron_3", NONPUNCT,
                ambiguities="excludes 'it' (separate feature)"),
    FeatureSpec("pron_it", "pronoun", "pronoun 'it' (inexplicit reference)", "n_pron_it", NONPUNCT,
                ambiguities="anaphoric vs dummy 'it' are not separated"),
    FeatureSpec("dem_pron", "pronoun", "demonstrative pronoun", "n_dem_pron", NONPUNCT,
                ambiguities="relies on the PRON vs DET tag for this/that/these/those; "
                            "'that' complementiser excluded by tag"),
    FeatureSpec("dem_det", "pronoun", "demonstrative determiner", "n_dem_det", NONPUNCT),
    # --- verbs
    FeatureSpec("past_tense", "verb", "narration (past orientation)", "n_tense_past", FINITE,
                ambiguities="morphological Tense=Past on finite verbs; not semantic time reference"),
    FeatureSpec("present_tense", "verb", "present orientation / immediacy", "n_tense_pres", FINITE),
    FeatureSpec("modal_possibility", "verb", "stance: possibility", "n_modal_possibility", FINITE,
                ambiguities="can/could/may/might; epistemic vs root senses not separated"),
    FeatureSpec("modal_necessity", "verb", "stance: necessity/obligation", "n_modal_necessity", FINITE,
                ambiguities="must/should/ought"),
    FeatureSpec("modal_prediction", "verb", "stance: prediction/volition", "n_modal_prediction", FINITE,
                ambiguities="will/would/shall, incl. contracted 'll/'d where tagged MD"),
    FeatureSpec("perfect_aspect", "verb", "perfect aspect", "n_perfect", FINITE,
                ambiguities="auxiliary 'have' child of a VBN head; parser-dependent"),
    FeatureSpec("progressive_aspect", "verb", "progressive aspect", "n_progressive", FINITE,
                ambiguities="auxiliary 'be' child of a VBG head; overlaps going-to future; passive progressive "
                            "('is being painted') counts as passive only"),
    FeatureSpec("passive", "verb", "impersonal / agentless style", "n_passive", FINITE,
                ambiguities="auxpass or nsubjpass dependency; get-passives partly missed"),
    FeatureSpec("imperative_sent", "verb", "directive / instruction", "n_imperative_sents", SENTS,
                ambiguities="heuristic: first word after any leading ADV/INTJ/CCONJ is a base-form verb (VB) with no "
                            "subject; titles and fragments give false positives"),
    # --- negation and questions
    FeatureSpec("negation", "interaction", "negation / stance", "n_neg", NONPUNCT),
    FeatureSpec("question_mark_sent", "interaction", "questions (orthographic)", "n_qmark_sents", SENTS,
                ambiguities="includes quoted questions and FAQ headings"),
    FeatureSpec("interrogative_sent", "interaction", "questions (syntactic heuristic)", "n_interrogative_sents", SENTS,
                ambiguities="'?' sentence starting with an auxiliary or wh-word; misses declarative questions"),
    # --- length and density
    FeatureSpec("mean_sent_len", "density", "sentence length (non-punct tokens)", NONPUNCT, SENTS, scale=1.0,
                ambiguities="flattened paragraphs and fused titles inflate sentence length"),
    FeatureSpec("mean_word_len", "density", "word length (characters)", "n_chars_nonpunct", NONPUNCT, scale=1.0),
    FeatureSpec("lexical_density", "density", "content-word proportion", "n_content", NONPUNCT, scale=1.0,
                ambiguities="content = NOUN, PROPN, VERB, ADJ, ADV"),
    FeatureSpec("noun_verb_ratio", "density", "nominal vs verbal style", "n_pos_NOUN_PROPN", "n_pos_VERB", scale=1.0,
                ambiguities="missing if no lexical verb"),
    # --- dependency proxies (per finite clause or per noun)
    FeatureSpec("relcl_per_clause", "dependency", "relative clauses (NP elaboration)", "n_relcl", FINITE, scale=1.0),
    FeatureSpec("advcl_per_clause", "dependency", "adverbial subordination", "n_advcl", FINITE, scale=1.0),
    FeatureSpec("comp_per_clause", "dependency", "complement clauses", "n_ccomp_xcomp", FINITE, scale=1.0,
                ambiguities="ccomp and xcomp pooled"),
    FeatureSpec("amod_per_noun", "dependency", "prenominal adjectival modification", "n_amod", NOUNS, scale=1.0),
    # --- nominalisation
    FeatureSpec("nominalisation", "lexical", "abstraction (nominalisation)", "n_nominalisation", NONPUNCT,
                ambiguities="NOUN ending -tion/-sion/-ment/-ness/-ity, length >= 7; string match, not morphology"),
)

# MATTR is not a ratio of stored counts: it is computed by the extractor over the lowercased non-punct tokens.
MATTR_WINDOW = 500
MATTR = FeatureSpec("mattr_500", "diversity", "lexical diversity (moving-average TTR)", "mattr_500",
                    "n_tokens_nonpunct", scale=1.0, min_denominator=MATTR_WINDOW,
                    ambiguities="missing below 500 non-punct tokens; tokenisation-dependent")

ALL_FEATURES: tuple[FeatureSpec, ...] = (*FEATURES, MATTR)


def render_dictionary() -> str:
    """Markdown feature dictionary (docs/feature_dictionary.md is generated from this; a test enforces sync)."""
    lines = [
        f"# Feature dictionary (registry v{REGISTRY_VERSION})",
        "",
        "Generated from `src/core_register/features/registry.py`. Do not edit by hand.",
        "Value = scale × numerator / denominator over the D-06 window (first 1,000 whitespace words). "
        "**Missing** (not 0) when the denominator is below its minimum. Measured with spaCy `en_core_web_sm` "
        "3.8.0 (NER disabled). Parser output is measurement with error.",
        "",
        "| ID | Family | Construct (interpretive) | Numerator | Denominator | Scale | Min. denom. "
        "| Known ambiguities |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f in ALL_FEATURES:
        scale = "per 1,000" if f.scale == PER_1K else "×1"
        lines.append(
            f"| `{f.id}` | {f.family} | {f.construct} | `{f.numerator}` | `{f.denominator}` | {scale} | "
            f"{f.min_denominator} | {f.ambiguities or '—'} |"
        )
    lines += ["", f"Sources: {UNVERIFIED}. Construct labels are not causal claims.", ""]
    return "\n".join(lines)


def validate_registry() -> None:
    ids = [f.id for f in ALL_FEATURES]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate feature ids")
    for f in ALL_FEATURES:
        if not f.numerator or not f.denominator or f.min_denominator < 1:
            raise ValueError(f"{f.id}: incomplete definition")
