# Methodology: proposed protocol (v0.1, awaiting method-gate approval)

Every item marked **[D-xx]** is a decision listed in `decisions.md` that needs explicit approval. Audit numbers come from `reports/audit/corpus_audit.json` and `template_overlap_indicator.json`.

## 1. Research questions → analyses

| RQ | Operationalisation |
|---|---|
| RQ1 Lexical vs grammatical vs combined | Same task, cohort, window, and split for: word TF-IDF, linguistic features, and their combination. Compare macro-F1, per-label F1, AP, and paired bootstrap differences. |
| RQ1b Minority registers | Per-label results stratified by training support (main and sub); low-support flags. |
| RQ1c Robustness | (a) released vs controlled split; (b) template-seen vs template-unseen test documents (§5.3); (c) length strata; (d) optional template-masking ablation. |
| RQ2 Overlapping labels | Multilabel (T1/T2) vs single-main subset (T3b) vs label-powerset (T3c). Error analysis separates cross-main hybrids (5,687 docs) from same-main multiple subs (1,043 docs). |
| RQ3 Feature contributions | Standardised LR coefficients per label, feature-family ablations, correlation/redundancy report. Coefficients are **predictive associations, not functional definitions**. |
| RQ3b Register vs topic/source shortcuts | Top lexical features inspected for topic or site-template words; template-seen gap; lexical-only vs grammar-only comparison under the template-unseen cohort. |

## 2. Data facts that shape the protocol (audit, 2026-11-05)

- 48,452 rows, all parse as exactly 3 tab fields; no tabs/CR inside text; no BOM; IDs are unique 7-character digit strings (26,177 with a leading zero), so they **must stay strings**.
- 17 empty texts (train 10, dev 1, test 6); no whitespace-only texts.
- 56 codes observed, matching the legend exactly. **460 distinct raw label strings but 455 distinct label sets**: 5 sets occur in two orders (e.g. `NA DP NE` / `NA NE DP`). Label order carries no meaning; we treat labels as sets.
- In every row, main codes precede subcodes. No row has a sub without some main.
- Every subcode except DP always co-occurs with its Table-1 parent, so the release looks **propagated**. DP lacks IN in 293 rows; DP co-occurs with NA 515 times. The article's Table 2 shows DP selected under NARRATIVE.
- OTHER never co-occurs with another code (582 rows).
- Paragraph breaks are flattened to spaces. Titles run into the first sentence. Page boilerplate (menus, cookie notices, "About me") remains. Some texts contain control characters (U+0007, U+0014/15) and U+00A0.
- Whitespace words: median 634, p95 ≈ 3,800, max 118,278; 28,791 docs exceed 512 words.
- Exact duplicates: 12 two-member groups (raw = normalised); 6 cross split (5 train/test, 1 train/dev); 3 groups have conflicting label sets (0610929/0654134 IN vs NA NE across train/dev; two within train).
- **Template indicator** (identical normalised first-50/last-50 words): 114 prefix groups (745 docs, max 129) and 670 suffix groups (3,276 docs, max 477). 409 suffix groups cross splits. Large groups are label-homogeneous site templates: a forum-software header goes with ID DF (121/129), a free-trial billing notice with IP DS, publisher footers with NA NE. This is direct evidence of **source/template shortcuts**. It is not provenance.

## 3. Tasks and labels

`source_labels` (raw string, preserved) → `analysis_labels` (task-specific set) → `predictions` (scores + decisions) are separate fields.

- **T1, primary: coarse main-register multilabel** over SP LY IN IP OP NA HI ID, using **observed** main codes only. No closure is applied: DP rows without IN stay without IN. **[D-03]**
- **OTHER policy [D-04]**, proposed: OTHER-only rows (582) are **excluded from T1 training and from the primary metric cohort ("functional cohort")**. Their T1 predictions are still produced and reported descriptively (rate of empty prediction sets, label distribution). Sensitivity S-OTHER: retrain with OTHER rows as all-negative and report the change on the functional cohort plus the empty-set rate on OTHER rows. Labelled as a sensitivity analysis because OTHER rows are not verified negatives.
- **T2: released 56-code multilabel**, all rows, OTHER as a code. This matches the article's propagated label space (not its models or settings).
- **T3, optional [D-05]**: (a) derived nonpropagated approximation; (b) single-main subset (docs with exactly one main; coverage loss reported: 5,687 of 47,853 non-empty functional docs (11.9%) are cross-main); (c) label-powerset multiclass over 455 sets, unseen-combination counts reported.
- Hybridity is reported as **cross-main overlap** (≥2 mains). Multiple subs under one main are counted separately and are not called hybrids.

## 4. Text handling

- Raw text is never modified on disk. `text_for_model` is derived per representation, with recorded settings.
- Linguistic pipeline: original case; NFC; control characters U+0000–U+001F (except whitespace) replaced by a space and counted; no stopword, punctuation, or pronoun removal.
- Lexical pipeline: NFKC, lowercase, URL/e-mail masking to `<URL>`/`<EMAIL>` (a declared setting); default tokenisation pattern recorded.
- **Input window [D-06]**: primary comparisons use the **first 1,000 whitespace words** for every representation, so that lexical and grammatical models see the same text and parser cost stays bounded. Truncation is flagged per document (14,675 docs, 30.3%, exceed 1,000 words). Ablation: full-text TF-IDF. The window size is checked against Phase-3 profiling before freezing; changing it later needs approval.
- Empty texts get status `EMPTY_INPUT`. They are kept in manifests, excluded from fitting, and given **no prediction**. In evaluation they are excluded from primary cohorts (17 docs) and listed in the cohort manifest.

## 5. Splits and leakage control

### 5.1 `released_split`
The original files, unchanged, for reference comparability. Known contamination is disclosed: 6 exact cross-split pairs plus near-duplicate and template overlap. It is never called leakage-free.

### 5.2 `controlled_split` [D-07]
- Groups = connected components over (a) exact raw-hash duplicates, (b) exact normalised-hash duplicates, (c) verified near-duplicates: word 5-shingle MinHash (128 permutations, 32 bands × 4 rows), candidate pairs **verified by exact Jaccard ≥ 0.80** on shingle sets; documents < 25 words get exact matching only. Thresholds are fixed **before** any modelling and are not tuned on model performance.
- Membership rule: keep original memberships. For a group spanning partitions, priority is test > dev > train: members in the highest-priority partition are kept and the others are **excluded** (manifested). Within a partition, one deterministic representative (lowest ID) is kept for training sets. Duplicates inside test/dev are kept but share one bootstrap group.
- Label-conflict groups: held-out members are kept; conflicting training members are **quarantined** (excluded from fitting, listed with reason).
- Assertion: no group spans two partitions. Excluded counts per label are reported, with loss of benchmark comparability stated.
- Template groups (§5.3) are **not** used for exclusion in the primary controlled split. Excluding all template-sharing docs would remove legitimate same-site documents and act as an undocumented domain filter. They drive the diagnostic below.

### 5.3 Template diagnostic (no repartitioning)
Template keys (normalised first-50 and last-50 words) are computed from **training documents only**. A test document is "template-seen" if it shares a key with any training document. Report metrics for template-seen vs template-unseen test cohorts and the paired gap. Optional ablation: mask spans matching training template keys. A true domain-held-out experiment is impossible without an ID→URL mapping; this is a proxy and is labelled as one.

### 5.4 Test sealing
Test manifests are frozen in Phase 2 before any fitting. Test inference runs only once, in Phase 5, for finalists frozen beforehand.

## 6. Linguistic features (registry, Phase 3)

Measurement tool: spaCy 3.8.x with a pinned English pipeline (proposed `en_core_web_sm`, CPU-friendly; compatibility with Python 3.14 still to be verified) **[D-08]**. Tagger and parser output is measurement with error, not gold. Counts and denominators are stored. Rates are per 1,000 non-punctuation tokens unless stated.

| Family | Features (operational) | Construct (interpretive, not causal) | Main ambiguities |
|---|---|---|---|
| POS | NOUN, PROPN, VERB (lexical), ADJ, ADV, PRON, DET, CCONJ, SCONJ, ADP, NUM, INTJ per 1k | information packaging vs involvement | tagger error on web text; title fusion |
| Pronouns | 1st/2nd/3rd person personal (lemma lists ∩ PRON), possessive determiners, *it*, demonstrative pronoun (PRON) vs determiner (DET) | interaction, audience address, narration | generic *you*; quoted speech |
| Verbs | past (Tense=Past on VERB/AUX), present, modals by class (possibility/necessity/prediction), perfect (*have* + VBN), progressive (*be* + VBG), passive (`auxpass`/`nsubjpass`, or *be* + VBN) per finite clause | narration, instruction, stance, impersonality | parser dependence; overlap of patterns documented |
| Imperatives | sentence-initial base-form VERB without subject (heuristic) | instruction | fragment/title false positives |
| Negation | `neg` dependency per 1k | stance/interaction | — |
| Questions | (a) `?` per sentence; (b) syntactic interrogative heuristic (aux-initial / wh-initial) | interaction | quoted questions; FAQs |
| Length & density | mean/SD sentence length (tokens), mean word length, lexical density (content/all), noun/verb ratio (safe denominator) | information density | flattened paragraphs inflate sentence length; length confounding |
| Lexical diversity | MATTR, window 500 tokens; undefined below 500 tokens (+ indicator) | lexical variation | short-text policy |
| Optional dependency | relative clauses (`relcl`), adverbial clauses (`advcl`), clausal complements (`ccomp`, `xcomp`) per finite clause; prenominal modifiers per noun | elaboration, NP complexity | proxies only |
| Optional lists | nominalisation suffixes (-tion/-ment/-ness/-ity on NOUN, with exclusion list); stance adverbs; discourse markers | abstraction, stance | string match ≠ function |

Each registry entry carries: ID, construct, source, formula, denominator, tagger requirement, ambiguities, missingness, and tests. **Sources:** bibliographic entries for Biber (1988) and Biber & Conrad (2009) are verified only via the primary article's reference list. Page-level support for each construct mapping is still **pending** and will be marked "unverified" in the registry until checked. We will not call this "multidimensional analysis".
Validation: hand-built positive/negative/ambiguous fixtures per feature, plus a fixed 60-document **training-only** inspection sample. No measured extraction accuracy is claimed unless a qualified manual assessment is done.
Missingness: undefined ≠ zero; NaN plus indicator; train-only median imputation; train-only robust scaling.

## 7. Models (Phase 3 CPU)

1. Constant baselines: per-label training prevalence scores (AP reference); most-frequent label set; all-negative (diagnostic).
2. Word TF-IDF (1–2-grams) + one-vs-rest LogisticRegression (liblinear/saga).
3. Same + one-vs-rest LinearSVC (raw margins, never called probabilities).
4. Linguistic features + L2 one-vs-rest LogisticRegression.
5. Combined sparse TF-IDF ⊕ scaled linguistic block, with a block weight α as a declared hyperparameter.
6. Optional character 3–5-gram TF-IDF (max 200k features).

All fitting (vocabulary, IDF, imputation, scaling, thresholds) is done inside sklearn Pipelines on training data. **Search [D-09]**: C ∈ {0.1, 1, 10} × class_weight ∈ {None, balanced}; TF-IDF max_features ∈ {50k, 200k}, ngram ∈ {(1,1), (1,2)}, min_df = 3; α ∈ {0.5, 1, 2}. Selection by **dev macro-F1** (T1) after threshold tuning. Global threshold grid 0.05–0.95, step 0.05 (LR); SVM margin grid over dev quantiles. Per-label thresholds are only allowed if dev positives ≥ 50, shrunk 50% toward the global value; otherwise the global threshold is used.

Phase 4 (optional, separate approval): frozen open sentence encoder + LR; one small open transformer, first-window only. Checkpoints are vetted for license, revision, and CORE exposure. Any TurkuNLP register checkpoint trained on CORE is excluded as an independent baseline.

## 8. Evaluation

- **Primary endpoint [D-10]**: T1 macro-F1 over 8 mains, functional cohort, **controlled_split test**, with the frozen dev-selected threshold.
- Secondary: micro-F1, weighted-F1, samples-F1 (empty-vs-empty = 1), exact-set accuracy, per-label P/R/F1/support, average precision (macro and micro, named "AP"), per-label 2×2 confusion, Brier score and reliability for LR models. Also released_split results, T2 results (micro and macro, with zero-support labels flagged), zero_division = 0 declared.
- Uncertainty: paired bootstrap, 2,000 resamples, seed 20261105. The resampling unit is the controlled-split group (a singleton for most docs). Prespecified comparisons: (C1) combined vs TF-IDF-LR, (C2) linguistic-LR vs TF-IDF-LR, (C3) TF-IDF-LR vs prevalence baseline. Holm correction across C1–C3; effect sizes reported.
- Error analysis covers rare labels, OTHER predictions, cross-main vs same-main overlaps, length deciles, truncation flag, parser-failure flag, template-seen flag, and top lexical shortcut features.

## 9. Not done / limits stated up front

No raw votes; no source domains; nonpropagated labels can only be approximated; parser error is not measured against gold; 2012 snapshot; possible web-text pretraining exposure for any Phase-4 checkpoint; the complementary 2021 study is not yet accessed.
