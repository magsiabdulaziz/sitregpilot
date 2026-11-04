# Source ledger

Primary article: Laippala, Rönnqvist, Oinonen, Kyröläinen, Salmela, Biber, Egbert & Pyysalo (2023). *Register identification from the unrestricted open Web using the Corpus of Online Registers of English.* Language Resources and Evaluation 57:1045–1079. https://doi.org/10.1007/s10579-022-09624-1. Published online 26 Oct 2022; the article is CC BY 4.0 (p. 1076). Page numbers below are journal pages. I read the local PDF in full.

Evidence types: **SRC** = stated in the source · **AUD** = measured by our audit (`reports/audit/`) · **INF** = our inference · **UNK** = not specified.

## A. Corpus and annotation

| # | Claim | Location | Type | Uncertainty / note | Extension |
|---|---|---|---|---|---|
| A1 | CORE was compiled from Google searches of frequent English 3-grams, saving and randomly sampling pages; searches Nov–Dec 2012 | §4.1 p.1053 | SRC | snapshot; biased toward the searchable Web (§8 p.1075) | time/domain limits go in the dataset card |
| A2 | 4 coders annotated each document through a hierarchical decision tree (situational characteristics → main register → subregister), via Mechanical Turk | §4.1 p.1054 | SRC | raw votes not released | — |
| A3 | Taxonomy has 8 main registers and 47 subregisters (Table 1); in Table 1, mains are upper-case and subs lower-case | Table 1 p.1054 | SRC | the release uses upper case for all codes, so level cannot be read from case | label schema encodes level explicitly |
| A4 | A label is assigned when ≥2 coders agree, at main and sub level; hybrids arise when votes split 2–2; no frequency threshold | §4.2 p.1055 | SRC | 2–2 hybrids may not be recurrent combinations (p.1055) | report cross-main overlap separately |
| A5 | Propagated version: the main label is added whenever one of its subs is assigned | §4.2 p.1056; Table 2 | SRC | — | — |
| A6 | Nonpropagated version: the main label is kept only when it lacks a propagated sub (Table 3: Text 2 → "News article, Sports report" without NA) | §4.2 p.1056; Table 3 p.1058 | SRC | not released; the release looks propagated (audit: `hierarchy.sub_without_reference_parent` lists only DP) | optional **derived approximation** (see compatibility.md) |
| A7 | Table 2, Document 3: Coder 3 chose NARRATIVE + "Description of a person"; final labels IN + NA without a sub | Table 2 p.1057 | SRC | shows that DP can be selected under NA in the decision tree | basis for treating DP-without-IN as a **contextual exception**, not an error |
| A8 | Multiclass setting = 460 combination labels; multilabel = 56 labels | §4.2 p.1056; Table 4 | SRC | 460 equals our count of distinct **raw label strings**; distinct **sets** = 455 (audit: `global.n_distinct_combinations`; raw-string count recorded in ISS-003) | INF: the article may count order variants as distinct classes; unverified |
| A9 | Corpus = 48,452 documents | §4.3 p.1059 | SRC | equals AUD total | — |
| A10 | Most frequent document lengths are 700–1000 words; some exceed 10,000 | §4.3 p.1056; Fig.1 | SRC | word definition UNK | our whitespace median is 634 (train) |
| A11 | Multi-main hybrids: ~20% hybrid with NA, ~9% "with the other one in the pair" (IN/OP) | §4.3 p.1059 | SRC | denominator ambiguous | not used quantitatively |
| A12 | Some subregisters were excluded in Biber & Egbert (2016b) for small size or low agreement, but are kept here | §4.1 p.1055 | SRC | low-agreement subs (e.g., "O*" other-categories) | flag low-support labels |
| A13 | Social-media documents are not included | §4.1 p.1055 | SRC | — | dataset card |

## B. Experimental method

| # | Claim | Location | Type | Note |
|---|---|---|---|---|
| B1 | 70/10/20 train/dev/test, stratified on register labels | §5.1 p.1061 | SRC | stratification algorithm UNK; released files match 70/10/20 (AUD) |
| B2 | Metrics: P, R, F1, PR-AUC, all **micro-averaged** | §5.1 p.1061 | SRC | PR-AUC integration method UNK (average precision vs trapezoid) |
| B3 | Grid search for hyperparameters; mean of 3 training runs with the same hyperparameters | §5.1 pp.1061–1062 | SRC | grid ranges UNK; selection metric UNK (presumably dev) |
| B4 | Models: BERT Base and BERT Large (512 tokens, first part of document), fastText (pretrained 300-d English vectors), CNN (frozen embeddings capped at 100k, 128 filters) | §5.2 pp.1062–1063 | SRC | BERT checkpoint (cased/uncased) UNK; text preprocessing UNK |
| B5 | Hyperparameters: BERT-L batch 7, seq 512, 5 epochs, LR 7e-6 (prop), 1e-5 (nonprop), 4e-5 (multiclass); BERT-B batch 6, LR 3e-5 / 4e-5; fastText LR 0.1, 80 epochs, n-gram 3, window 5 (prop); CNN LR 0.001, threshold 0.4, kernel 2, batch 32 (prop) | Appendix 1 p.1075 | SRC | **BERT decision threshold UNK**; CNN threshold 0.4 stated |
| B6 | Code repos named: google-research/bert, haamis/neuro_classifier, facebookresearch/fastText, mavela/Multiling-Multilabel-CNN, TurkuNLP/multiling-cnn | §5.2 | SRC | not inspected; exact commits UNK |

## C. Reported results (for reference only; **not** comparable to our cohorts unless every setting matches)

| # | Result | Location |
|---|---|---|
| C1 | BERT-L propagated 56-label multilabel: micro F1 68 (SD 0.33), P 71, R 65, PR-AUC 75 | Table 4 p.1062 |
| C2 | BERT-L nonpropagated: F1 58, PR-AUC 63; propagated multiclass (460): F1 56, PR-AUC 46 | Table 4 |
| C3 | BERT-B propagated: F1 67, PR-AUC 75; fastText propagated F1 62; CNN propagated F1 59 | Table 4 |
| C4 | Learning curve flattens at ~30% and ~70% of training data | Fig.4 p.1065 |
| C5 | Per-label PR-AUC is correlated with training size; LY, SL, RE, SR, NE, NA, ID are high; IB is low despite large N; TV, PO, TA high despite small N | §6.2, Fig.6 pp.1066–1067 |
| C6 | Hybrids are misclassified more often; "No label" documents are spread across many predicted labels | §6.2 pp.1067–1068, Fig.8 |
| C7 | Fig.8 heatmap reduces subs to mains and treats combinations as rows/columns; the counting rule is not fully specified | Fig.8 p.1069 | 
| C8 | First 512-token block performs best; longer documents score lower; ~1.7 BERT tokens per word, 329.9 words per block | §7.1 pp.1069–1071, Figs.9–10 |
| C9 | LSTM over per-block BERT probabilities (10-fold CV) reaches dev F1 66.56%, no gain | §7.2 p.1072, Fig.11 |
| C10 | Limitations: discrete multilabel cannot capture continuous variation; temporal snapshot; search-engine bias; English only | §8 p.1075 |

## D. Secondary claims about other works (as reported by the primary article; not independently verified)

| # | Claim | Location | Status |
|---|---|---|---|
| D1 | Laippala, Egbert, Biber & Kyröläinen (2021), LRE 55(3):757–788: linear SVMs on lexico-grammatical features from parsed documents, 26 CORE subregisters, F1 74.5%, well-defined **non-hybrid** subset | §2.2 p.1050; §8 p.1074; refs p.1077 | **complementary study not accessed.** Needs a user-supplied PDF before its features, tagger, or stability method can be cited. |
| D2 | Biber & Egbert (2016b): avg precision 34% / recall 39.6% on 20-subregister subset; 26.9% / 28.6% full corpus | §2.2 p.1050 | secondary |
| D3 | Madjarov et al. (2019): multilabel preferable to multiclass | §2.2 p.1051 | secondary |

## E. Repository / licensing

| # | Claim | Location | Type |
|---|---|---|---|
| E1 | "The annotations of this corpus are licensed under CC BY-SA 4.0" | LICENSE.txt | SRC. Covers **annotations only**. Nothing grants rights to the underlying web text. |
| E2 | README asks users to cite Laippala et al. (2022) and credits Biber, Egbert & Davies for compilation (3 references) | README.md | SRC |
| E3 | Release contains labels, ID, text only: no votes, URLs/domains, features, code, or checkpoints | repository contents | AUD |
