# Feature dictionary (registry v1.0.0)

Generated from `src/core_register/features/registry.py`. Do not edit by hand.
Value = scale × numerator / denominator over the D-06 window (first 1,000 whitespace words). **Missing** (not 0) when the denominator is below its minimum. Measured with spaCy `en_core_web_sm` 3.8.0 (NER disabled). Parser output is measurement with error.

| ID | Family | Construct (interpretive) | Numerator | Denominator | Scale | Min. denom. | Known ambiguities |
|---|---|---|---|---|---|---|---|
| `pos_noun` | pos | information packaging (nominal) | `n_pos_NOUN` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_propn` | pos | reference to named entities | `n_pos_PROPN` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_verb` | pos | clausal / verbal style | `n_pos_VERB` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_adj` | pos | attributive elaboration | `n_pos_ADJ` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_adv` | pos | stance and circumstance | `n_pos_ADV` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_pron` | pos | involvement / interaction | `n_pos_PRON` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_det` | pos | nominal reference | `n_pos_DET` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_cconj` | pos | phrasal and clausal coordination | `n_pos_CCONJ` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_sconj` | pos | subordination | `n_pos_SCONJ` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_adp` | pos | prepositional elaboration | `n_pos_ADP` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_num` | pos | quantification | `n_pos_NUM` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pos_intj` | pos | interactive / spoken style | `n_pos_INTJ` | `n_tokens_nonpunct` | per 1,000 | 1 | tagger error on web text; titles fused into first sentence |
| `pron_1sg` | pronoun | speaker reference | `n_pron_1sg` | `n_tokens_nonpunct` | per 1,000 | 1 | quoted speech counts as the writer's own |
| `pron_1pl` | pronoun | inclusive/exclusive group reference | `n_pron_1pl` | `n_tokens_nonpunct` | per 1,000 | 1 | — |
| `pron_2` | pronoun | addressee reference | `n_pron_2` | `n_tokens_nonpunct` | per 1,000 | 1 | generic 'you' is not distinguished from addressee 'you' |
| `pron_3` | pronoun | third-person reference (narration) | `n_pron_3` | `n_tokens_nonpunct` | per 1,000 | 1 | excludes 'it' (separate feature) |
| `pron_it` | pronoun | pronoun 'it' (inexplicit reference) | `n_pron_it` | `n_tokens_nonpunct` | per 1,000 | 1 | anaphoric vs dummy 'it' are not separated |
| `dem_pron` | pronoun | demonstrative pronoun | `n_dem_pron` | `n_tokens_nonpunct` | per 1,000 | 1 | relies on the PRON vs DET tag for this/that/these/those; 'that' complementiser excluded by tag |
| `dem_det` | pronoun | demonstrative determiner | `n_dem_det` | `n_tokens_nonpunct` | per 1,000 | 1 | — |
| `past_tense` | verb | narration (past orientation) | `n_tense_past` | `n_finite_verbs` | per 1,000 | 1 | morphological Tense=Past on finite verbs; not semantic time reference |
| `present_tense` | verb | present orientation / immediacy | `n_tense_pres` | `n_finite_verbs` | per 1,000 | 1 | — |
| `modal_possibility` | verb | stance: possibility | `n_modal_possibility` | `n_finite_verbs` | per 1,000 | 1 | can/could/may/might; epistemic vs root senses not separated |
| `modal_necessity` | verb | stance: necessity/obligation | `n_modal_necessity` | `n_finite_verbs` | per 1,000 | 1 | must/should/ought |
| `modal_prediction` | verb | stance: prediction/volition | `n_modal_prediction` | `n_finite_verbs` | per 1,000 | 1 | will/would/shall, incl. contracted 'll/'d where tagged MD |
| `perfect_aspect` | verb | perfect aspect | `n_perfect` | `n_finite_verbs` | per 1,000 | 1 | auxiliary 'have' child of a VBN head; parser-dependent |
| `progressive_aspect` | verb | progressive aspect | `n_progressive` | `n_finite_verbs` | per 1,000 | 1 | auxiliary 'be' child of a VBG head; overlaps going-to future; passive progressive ('is being painted') counts as passive only |
| `passive` | verb | impersonal / agentless style | `n_passive` | `n_finite_verbs` | per 1,000 | 1 | auxpass or nsubjpass dependency; get-passives partly missed |
| `imperative_sent` | verb | directive / instruction | `n_imperative_sents` | `n_sents` | per 1,000 | 1 | heuristic: first word after any leading ADV/INTJ/CCONJ is a base-form verb (VB) with no subject; titles and fragments give false positives |
| `negation` | interaction | negation / stance | `n_neg` | `n_tokens_nonpunct` | per 1,000 | 1 | — |
| `question_mark_sent` | interaction | questions (orthographic) | `n_qmark_sents` | `n_sents` | per 1,000 | 1 | includes quoted questions and FAQ headings |
| `interrogative_sent` | interaction | questions (syntactic heuristic) | `n_interrogative_sents` | `n_sents` | per 1,000 | 1 | '?' sentence starting with an auxiliary or wh-word; misses declarative questions |
| `mean_sent_len` | density | sentence length (non-punct tokens) | `n_tokens_nonpunct` | `n_sents` | ×1 | 1 | flattened paragraphs and fused titles inflate sentence length |
| `mean_word_len` | density | word length (characters) | `n_chars_nonpunct` | `n_tokens_nonpunct` | ×1 | 1 | — |
| `lexical_density` | density | content-word proportion | `n_content` | `n_tokens_nonpunct` | ×1 | 1 | content = NOUN, PROPN, VERB, ADJ, ADV |
| `noun_verb_ratio` | density | nominal vs verbal style | `n_pos_NOUN_PROPN` | `n_pos_VERB` | ×1 | 1 | missing if no lexical verb |
| `relcl_per_clause` | dependency | relative clauses (NP elaboration) | `n_relcl` | `n_finite_verbs` | ×1 | 1 | — |
| `advcl_per_clause` | dependency | adverbial subordination | `n_advcl` | `n_finite_verbs` | ×1 | 1 | — |
| `comp_per_clause` | dependency | complement clauses | `n_ccomp_xcomp` | `n_finite_verbs` | ×1 | 1 | ccomp and xcomp pooled |
| `amod_per_noun` | dependency | prenominal adjectival modification | `n_amod` | `n_pos_NOUN` | ×1 | 1 | — |
| `nominalisation` | lexical | abstraction (nominalisation) | `n_nominalisation` | `n_tokens_nonpunct` | per 1,000 | 1 | NOUN ending -tion/-sion/-ment/-ness/-ity, length >= 7; string match, not morphology |
| `mattr_500` | diversity | lexical diversity (moving-average TTR) | `mattr_500` | `n_tokens_nonpunct` | ×1 | 500 | missing below 500 non-punct tokens; tokenisation-dependent |

Sources: UNVERIFIED: motivated by Biber (1988) / Biber & Conrad (2009) via the primary article's references. Construct labels are not causal claims.
