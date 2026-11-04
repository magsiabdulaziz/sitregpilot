# Compatibility matrix: article vs. this project

Legend: **R** = replicable from the release · **A** = adaptation (same idea, different known settings) · **E** = new extension · **X** = not possible with released data.

| Aspect | Article (ledger ref) | This project (proposed) | Status |
|---|---|---|---|
| Data | 48,452 docs, released split (A9, B1) | identical files, hashes verified | R |
| Split | 70/10/20 stratified (B1) | `released_split` unchanged + `controlled_split` (duplicate groups cannot cross partitions) | R + E |
| Label space, propagated 56 | multilabel 56 (A8, C1) | Task T2, full 56 codes including OTHER | R (label space) |
| Nonpropagated | Table 3 (A6) | optional **derived** labels: drop the main when one of its Table-1 subs is present. **DP-under-NA cannot be resolved**, because we cannot know whether NA had its own sub agreement. | A (approximation) |
| Multiclass 460 | (A8, C2) | optional label-powerset ablation over **455 label sets**; unseen dev/test sets reported (dev 19, test 21 unseen in train) | A |
| Coarse 8-main task | not a separate task in the article (Fig.8 collapses to mains for error analysis) | Task T1, primary | E |
| Input window | BERT first 512 tokens (B4, C8) | linear models use the same declared word window across representations; transformers use the first window | A |
| Models | BERT-B/L, fastText, CNN (B4) | constant, TF-IDF+LR/SVM, linguistic features+LR, combined, optional encoders | E (BERT optional, A) |
| Hyperparameters | partially given (B5) | own declared grids | A |
| Threshold | BERT: UNK; CNN 0.4 (B5) | global threshold tuned on dev; 0.5 also reported | A |
| Metric | micro P/R/F1, micro PR-AUC (B2) | primary macro-F1 (T1); micro/weighted/samples-F1, exact match, per-label, **average precision** (named as such) | A + E |
| PR-AUC integration | UNK | report AP (step-wise). Trapezoidal PR-AUC only if labelled. | X (exact) |
| Seeds | 3 runs, mean (SD) (B3) | 3 seeds for stochastic models; deterministic linear fits reported once | A |
| Uncertainty | SD across runs only | paired document-level bootstrap CIs + seed spread | E |
| Annotator agreement / votes | used to build labels (A4) | not released | X |
| Source/domain held-out | — | no domain metadata, so impossible without an ID→URL mapping | X |
| Lexico-grammatical features | not in this article; cited from D1 | registry of interpretable features (spaCy, pinned) | E (not a replication of D1) |

**Conclusion:** exact replication of Table 4 is **not** claimed. The BERT checkpoint, preprocessing, threshold, PR-AUC method, and grid are unknown (UNK in source_ledger.md).
