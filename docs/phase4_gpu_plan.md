# Phase 4 (deferred): GPU/Colab experiment plan

**Status:** deferred by D-17 (owner, 2026-11-05). Nothing in this file has been run. Do not download large
checkpoints or start transformer training on the laptop. This plan is optional and separable from the CPU pipeline.

## Preconditions (all required before starting)
1. CPU baselines, Phase 3b analyses (D-15) and the D-16 check are complete and merged.
2. Owner approval of a concrete Phase 4 issue (model list, budget, runtime environment).
3. Selected CPU configurations and thresholds frozen (no test inspection before Phase 5).

## Candidate experiments (methodology section 7, experiment plan E1/E2)
| ID | Representation | Classifier | Notes |
|---|---|---|---|
| E1 | frozen open sentence encoder (mean-pooled embeddings) | OvR LogReg, same threshold procedure | cheap; CPU-feasible inference for a small encoder, GPU preferred |
| E2 | small open transformer fine-tuned, first window only | multilabel head (independent sigmoids) | GPU required; first-window baseline before any chunk aggregation |

## Checkpoint vetting (before use)
- License and exact revision (commit hash) recorded.
- Prior register fine-tuning and possible CORE exposure checked. **A checkpoint trained on CORE (e.g. TurkuNLP register models) is not an independent baseline.**
- Generic pretraining exposure to web text is disclosed as unknown where it cannot be ruled out.

## Data and leakage rules
- Same controlled split, functional cohort and T1 labels. The test set stays sealed until Phase 5.
- Only the window text is uploaded to the runtime. **No corpus text is committed**, and the CORE text licence situation (`docs/architecture.md`) applies to any upload.
- Chunks of one document stay in its partition. Metrics are document-level. Long documents are weighted so they do not dominate training through many chunks.

## Reproducibility
- Pinned `neural` dependency group and lock (to be created then); seeds and nondeterminism limits recorded.
- Token counts with special tokens reserved; truncation recorded per document.
- Same run-manifest format as the CPU runs (commit, hashes, config, environment, timing, memory).

## Budget
Colab free tier is not guaranteed. Runs must be resumable from checkpoints. An unrun configuration is reported as **not run**, never estimated.
