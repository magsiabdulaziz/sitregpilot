# Session handoff

_Updated: 2026-11-05_

## Current Objective
M2 / Phase 3: finish #19 (features, PR #21), then #20 (CPU baselines B0–B4 on dev; test stays sealed).

## Last Verified State
- `main` = `bb63f2a` (PRs #10, #12–#18 merged; protected, DEC-006). Repo public. Gate C approved.
- Data contracts on `main`: `audit`, `dedup`, `split` CLIs. Sealed split manifest `data/manifests/splits/split_manifest.csv` (sha in `reports/splits/split_report.json`); controlled train 33,870 / dev 4,843 / test 9,686; 53 excluded.
- **Test set is sealed: no model work may look at test results until Phase 5.**

## Active Task
TASK-020 / #19 on `feature/issue-19-features` (PR #21): review round-1 fixes in; extractor 1.1.0 re-extraction (~1 h) then delta review.

## Current Git Context
See [PR_TRACKER](PR_TRACKER.md). Merges need an explicit per-PR owner instruction in chat; the harness blocked the standing-instruction merge.

## Files Under Development
`src/core_register/features/{registry,extract}.py`, `cli.py` (features), `scripts/{profile_spacy,feature_inspection_sample}.py`, `reports/{profiling,features}/`, `docs/feature_dictionary.md`, tests.

## Decisions to Preserve
D-01/D-02 adopted, D-03…D-12 and D-14 approved, D-13 blocked ([decisions](../decisions.md)); DEC-001…DEC-007 ([DECISIONS](DECISIONS.md)). No co-author trailers.

## Unresolved Problems
ISS-001 (complementary study PDF, #9/#11).

## Pending User Approvals
Merge of PR #21. Owner awareness: MATTR-500 missing for ~38% of documents (protocol-conformant). `/CLAUDE.md` line 3 wording (owner's file).

## Next Actions
1. When the v1.1.0 extraction finishes: run the inspection-sample script, regenerate reports, push, delta review, owner merge.
2. #20: B0–B2 (lexical) and then B3/B4 (with features) on dev.
3. Keep test results sealed.

## Resume Instructions
`git -C D:\SitRegPilot status --branch`; `& "C:\Program Files\GitHub CLI\gh.exe" pr list -R magsiabdulaziz/sitregpilot`; reconcile PR_TRACKER; `.venv\Scripts\python.exe -m pytest -m "not requires_corpus"` (fast) or a full run (~5 min with the corpus).
