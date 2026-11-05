# T1 dev results: CPU baselines B0–B4

**DEV ONLY.** Thresholds (global, then per-label shrunk 50%) and model selection both use the dev set,
so these numbers are **optimistic** and are *not* the study's result. The controlled test set stays
sealed until Phase 5.
Task T1: 8 main registers, multilabel; functional cohort; controlled split. Train n = 33,463, dev n = 4,785.
Conventions: zero_division = 0; samples-F1 counts empty-vs-empty as 1; AP = step-wise average precision.
**No significance testing has been done.** Differences between models (e.g. B4 vs B1) are untested point
estimates on dev; paired bootstrap intervals are computed only in Phase 5.

| Model | macro-F1 | micro-F1 | weighted-F1 | samples-F1 | exact set | macro-AP | selected settings |
|---|---|---|---|---|---|---|---|
| B0 prevalence (scores; 0.5 cut) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.140 | AP reference |
| B0 most-frequent label set | 0.077 | 0.420 | 0.245 | 0.420 | 0.369 | — |  |
| B0 all-negative | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | diagnostic |
| B1 word TF-IDF + LogReg | 0.610 | 0.667 | 0.670 | 0.666 | 0.458 | 0.624 | {"max_features":200000,"ngram_range":[1,2],"min_df":3,"C":10.0,"class_weight":"balanced"} |
| B2 word TF-IDF + LinearSVC (margins) | 0.605 | 0.659 | 0.657 | 0.667 | 0.427 | 0.629 | {"max_features":200000,"ngram_range":[1,2],"min_df":3,"C":1.0,"class_weight":null} |
| B3 linguistic features + LogReg | 0.479 | 0.586 | 0.585 | 0.596 | 0.267 | 0.438 | {"C":0.1,"class_weight":null} |
| B4 TF-IDF ⊕ α·linguistic + LogReg | 0.613 | 0.667 | 0.669 | 0.666 | 0.469 | 0.625 | {"alpha":0.5,"b1_params":{"max_features":200000,"ngram_range":[1,2],"min_df":3,"C":10.0,"class_weight":"balanced"}} |

## Per-register F1 (dev, tuned thresholds)

| Model | SP | LY | IN | IP | OP | NA | HI | ID |
|---|---|---|---|---|---|---|---|---|
| B1 word TF-IDF + LogReg | 0.514 | 0.788 | 0.627 | 0.392 | 0.576 | 0.783 | 0.509 | 0.688 |
| B2 word TF-IDF + LinearSVC (margins) | 0.504 | 0.803 | 0.615 | 0.407 | 0.562 | 0.762 | 0.497 | 0.694 |
| B3 linguistic features + LogReg | 0.427 | 0.619 | 0.576 | 0.127 | 0.495 | 0.723 | 0.424 | 0.438 |
| B4 TF-IDF ⊕ α·linguistic + LogReg | 0.536 | 0.815 | 0.629 | 0.377 | 0.581 | 0.780 | 0.513 | 0.674 |
| *dev support* | 76 | 68 | 1272 | 207 | 1053 | 2128 | 203 | 349 |

## Effect of threshold tuning (macro-F1, dev)

| Model | default threshold | tuned |
|---|---|---|
| B1 word TF-IDF + LogReg | 0.600 | 0.610 |
| B2 word TF-IDF + LinearSVC (margins) | 0.515 | 0.605 |
| B3 linguistic features + LogReg | 0.317 | 0.479 |
| B4 TF-IDF ⊕ α·linguistic + LogReg | 0.608 | 0.613 |

Default threshold = 0.5 for probabilities and 0.0 for SVM margins.

## B3: strongest linguistic associations per register (dev-selected model, fitted on train)

Logistic-regression weights on robust-scaled features (`missingindicator_*` = feature was missing).
These are **predictive associations given the other features**, not functional definitions of a
register. Correlated features share or trade weight; signs can flip under collinearity.

| Register | strongest positive | strongest negative |
|---|---|---|
| SP | `pos_pron` +0.77, `amod_per_noun` +0.37, `question_mark_sent` +0.25 | `missingindicator_mattr_500` -1.97, `pos_verb` -1.05, `pos_adj` -0.85 |
| LY | `pos_pron` +1.33, `missingindicator_mattr_500` +0.30, `pos_det` +0.28 | `mean_word_len` -1.25, `pos_num` -0.51, `dem_pron` -0.49 |
| IN | `mean_word_len` +0.63, `present_tense` +0.47, `missingindicator_sd_sent_len` +0.38 | `negation` -0.27, `perfect_aspect` -0.18, `comp_per_clause` -0.18 |
| IP | `pos_pron` +0.48, `lexical_density` +0.34, `poss_det` +0.28 | `past_tense` -0.65, `pos_verb` -0.58, `pron_1sg` -0.35 |
| OP | `pos_pron` +0.51, `present_tense` +0.30, `poss_det` +0.27 | `missingindicator_mattr_500` -0.50, `pron_1sg` -0.48, `pron_3` -0.39 |
| NA | `pos_propn` +0.29, `perfect_aspect` +0.26, `progressive_aspect` +0.26 | `pos_pron` -0.66, `missingindicator_sd_sent_len` -0.64, `present_tense` -0.59 |
| HI | `lexical_density` +0.52, `pos_noun` +0.34, `pos_det` +0.27 | `noun_verb_ratio` -0.73, `past_tense` -0.65, `pron_3` -0.57 |
| ID | `missingindicator_mattr_500` +0.66, `pos_pron` +0.41, `question_mark_sent` +0.30 | `past_tense` -1.20, `present_tense` -0.84, `mean_word_len` -0.70 |

## Provenance

- B0–B2 run `20261105T084605-5bb8e61` (commit `5bb8e61`, dirty False), 1594.9 s, peak 1974 MB.
- B3/B4 run `20261105T091306-c9d153b` (commit `c9d153b`, dirty False), 5513.5 s, peak 2447 MB; feature cache `f7e7bb9910ec…`.
- Model files and dev predictions: paths and sha256 in the JSON reports (git-ignored `artifacts/runs/`).
- Save/load parity verified for every selected model.
