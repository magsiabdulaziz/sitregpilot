# Bounded experiment plan (v0.1, proposed)

All entries are **not run**. Budgets are estimates for an i5-10310U / 24 GB machine and will be re-profiled before committing.

## Phase 2: data contracts (after approval)
| ID | Work | Acceptance |
|---|---|---|
| P2-1 | ingest/validate/audit CLI | reproduces `reports/audit/corpus_audit.json` counts exactly |
| P2-2 | exact + MinHash near-dup groups (thresholds frozen first) | group report; precision spot-check of 50 verified pairs (IDs + Jaccard; no text in reports) |
| P2-3 | released_split + controlled_split manifests, test sealed | group-disjointness assertion passes; per-label exclusion table |
| P2-4 | tests: IDs with leading zeros, malformed rows, unknown codes, empty input, conflicts, label order variants | pytest green |

## Phase 3: CPU baselines (T1 primary, then T2)
| ID | Representation | Model | Configs | Est. cost |
|---|---|---|---|---|
| B0 | — | prevalence / most-frequent set / all-negative | 3 | seconds |
| B1 | word TF-IDF 1–2g (window 1,000) | OvR LR | 24 | ~1–2 h total |
| B2 | same | OvR LinearSVC | 24 | ~1 h |
| B3 | linguistic registry v1 | OvR LR (L2) | 6 | minutes after extraction |
| B4 | B1-best ⊕ linguistic, α ∈ {0.5, 1, 2} | OvR LR | 3 | ~20 min |
| B5 (opt.) | char 3–5g TF-IDF, ≤200k | OvR LR | 6 | ~1–2 h |
| B6 (ablation) | full-text word TF-IDF | B1-best config | 1 | ~20 min |
| FX | spaCy extraction, ~29M words | — | 1 pass, cached | **profile first**: estimated 1–4 h with 3 processes |

Selection is on dev only. Test results are not looked at until Phase 5.

## Phase 3b: analyses on dev (allowed for development)
Coefficient tables, feature-family ablations (drop one family at a time), correlation report, template-seen vs unseen **on dev** (template keys from train).

## Phase 4 (optional; separate approval)
E1 frozen sentence encoder + LR; E2 small transformer, first window. Each is gated by checkpoint vetting and profiling. CPU feasibility of E2 on 34k docs is doubtful, so it is likely deferred to Colab.

## Phase 5: frozen test evaluation
Finalists (predeclared): B0-prevalence, B1-best, B3-best, B4-best (+ B2-best for SVM contrast).
Prespecified paired comparisons C1–C3 (methodology §8), Holm-corrected.
Cohorts: controlled functional (primary), released functional, template-unseen, OTHER rows (descriptive), T2 full.
Sensitivity: S-OTHER (all-negative training).

## Handoffs planned
- H-001 (`Explore`, read-only): independently recount §2 audit numbers from raw files; report mismatches.
- H-002 (`general-purpose`, after the data gate): write linguistic fixtures independently of the extractor implementation.
