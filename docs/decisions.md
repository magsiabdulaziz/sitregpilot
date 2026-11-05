# Decision log

Status: **ADOPTED** (within the authorised audit scope) · **PROPOSED** (needs approval at the method gate) · **APPROVED** / **REJECTED** (user).

| ID | Decision | Status | Alternatives / consequence |
|---|---|---|---|
| D-01 | REA is irrelevant (a reverse-engineering MCP server, currently failing to connect), so we use native Claude Code subagents or a single session | ADOPTED | `rea` MCP registration: **user chose KEEP (2026-11-05)**. Left as is and not used by this project. |
| D-02 | Corpus cloned from the user fork to `data/raw/CORE-corpus` (HEAD b57dbdb…, = upstream); raw files are never modified | ADOPTED | — |
| D-03 | T1 uses observed main labels; **no hierarchy closure** (DP-without-IN preserved) | APPROVED (2026-11-05) | closure would invent 293 IN labels against Table 2 evidence |
| D-04 | OTHER-only rows are excluded from T1 training and primary metrics but predicted and reported. Sensitivity: OTHER as all-negative. | APPROVED (2026-11-05) | (b) include as all-negative in the primary (treats OTHER as verified negatives); (c) a 9th "OTHER" output in T1 |
| D-05 | T3a nonprop-approximation, T3b single-main subset, T3c label-powerset are **optional**, run after the baselines | APPROVED (2026-11-05) | drop any of them |
| D-06 | Shared input window = first 1,000 whitespace words for the primary representation comparison; full-text TF-IDF ablation | APPROVED (2026-11-05) | 512 words (closer to the BERT window) / 2,000 / full text (parser cost on 118k-word docs) |
| D-07 | `controlled_split`: exact + verified near-dup (5-shingle MinHash, Jaccard ≥ 0.80) components; priority test > dev > train; conflicting training members quarantined; template groups used only for diagnostics | APPROVED (2026-11-05) | group-aware repartition (loses released comparability); also exclude template-sharing docs (domain-filter effect) |
| D-08 | spaCy 3.8.x + pinned `en_core_web_sm` for linguistic measurement | APPROVED (2026-11-05) | `en_core_web_md`/`lg` (slower, more RAM); Stanza (slower, no Py3.14 check yet) |
| D-09 | Grid as in methodology §7 (≤ 24 TF-IDF configs per model/task; the combined model B4 adds only 3 α values on top of the B1-best TF-IDF config, per experiment_plan) | APPROVED (2026-11-05) | smaller/larger grid |
| D-10 | Primary endpoint: T1 macro-F1, functional cohort, controlled_split test | APPROVED (2026-11-05) | released_split as primary (comparability, but contaminated) |
| D-11 | Initialise Git at `D:\SitRegPilot`; `.venv` + pip + frozen lock; data/artifacts git-ignored | APPROVED (2026-11-05) | — |
| D-12 | Code license: Apache-2.0 (default accepted with "approve all") | APPROVED (2026-11-05) | — |
| D-13 | Complementary study (2021) | BLOCKED | needs the user to supply a PDF; until then its methods are cited only as reported in the primary article |
| D-14 | D-07 clarification: a train-only duplicate group whose members carry different label sets is quarantined **entirely** (no representative kept), since the correct label cannot be determined. Affects 10 documents in 5 two-member groups. Implemented in PR #17 (`configs/data/splits.yaml`: `conflict_policy: quarantine_train`). | APPROVED (owner: "quarantine all", 2026-11-05) | keep the lowest-ID member (would keep a possibly wrong label) |
| D-15 | **Phase 3b dev-only analyses** (owner, 2026-11-05): (a) B3 feature-family ablation (drop one family at a time, refit on train with B3-selected settings fixed, evaluate on dev; report absolute and Δ scores and per-register effects; "contribution under fixed settings", not causal importance); (b) template-overlap diagnostic (dev documents with vs without a template key shared with controlled-train documents; template similarity defined explicitly and distinguished from duplicate text and source domain; report group sizes, label and length distributions as confounders; a gap is diagnostic, not proof of shortcut learning; no split or label changes); (c) full-document vs 1,000-word TF-IDF (same partitions, vocabulary cap and model settings; each vectoriser fitted on its own training texts; report performance, runtime, peak memory and effects by length). Issues #25, #26. | APPROVED (2026-11-05) | — |
| D-16 | **Amends D-09** (owner, 2026-11-05): B1/B2 add **one** TF-IDF vocabulary candidate, `max_features` = 400,000 (2× the D-09 maximum); all other search settings unchanged. Rationale: the selected B1/B2 settings sat at the D-09 grid boundary (200k). That motivates a check but does not show a larger vocabulary helps. **Training-only pilot first; stop rules declared before the pilot:** peak RSS > 12 GB, or vectoriser fit > 3× the 200k fit → keep the 200k cap. No further expansion. Run separately from (c); any combination is a labelled follow-up. Outcome to be recorded here. Issue #24. | APPROVED (2026-11-05); outcome PENDING | keep 200k cap |
| D-17 | **Phase 4 deferred** (owner, 2026-11-05): no neural training, no large checkpoint downloads, no transformer runs on the laptop. Neural support stays optional; a future GPU/Colab plan is documented in `docs/phase4_gpu_plan.md`. First complete the CPU baselines, Phase 3b, the D-16 check, testing, interpretation and documentation. | APPROVED (2026-11-05) | — |

### Evaluation controls for D-15 to D-17 (owner, 2026-11-05)
- Fit on train; make these decisions on dev only. The primary metric (D-10) and the label and cohort policies (D-03, D-04) are unchanged.
- Test performance is not inspected during these analyses.
- Every experiment is logged, including unsuccessful runs.
- Selected configurations and thresholds are frozen before the final test evaluation.
- Repeated dev comparisons create selection optimism. Dev improvements are **provisional** until the frozen test evaluation.
