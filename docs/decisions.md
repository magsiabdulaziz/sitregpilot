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
