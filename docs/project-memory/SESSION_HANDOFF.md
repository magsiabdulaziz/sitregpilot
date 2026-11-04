# Session handoff

_Updated: 2026-11-05_

## Current Objective
Close M1 / Phase 2 with gate C (#8), then start Phase 3 (linguistic features and CPU baselines) after the owner reviews the gate C report.

## Last Verified State
- `main` = `c6eab9b` (PRs #10, #12–#17 merged; protected, DEC-006). Repo public.
- Data contracts on `main`: `audit`, `dedup`, `split` CLIs. Sealed split manifest `data/manifests/splits/split_manifest.csv` (sha in `reports/splits/split_report.json`); controlled train 33,870 / dev 4,843 / test 9,686; 53 excluded.
- **Test set is sealed: no model work may look at test results until Phase 5.**

## Active Task
TASK-013 / #8 on `test/issue-8-gate-c`: provenance tests, report n/a split, D-14, methodology §5.3, `reports/gates/gate_C.md`, memory sync.

## Current Git Context
See [PR_TRACKER](PR_TRACKER.md). Merges need an explicit per-PR owner instruction in chat; the harness blocked the standing-instruction merge.

## Files Under Development
`src/core_register/data/splits.py` (report only), `tests/unit/test_cli_provenance.py`, `reports/splits/split_report.json`, `reports/gates/gate_C.md`, `docs/decisions.md` (D-14), `docs/methodology.md` §5.3, memory files.

## Decisions to Preserve
D-01/D-02 adopted, D-03…D-12 and D-14 approved, D-13 blocked ([decisions](../decisions.md)); DEC-001…DEC-007 ([DECISIONS](DECISIONS.md)). No co-author trailers.

## Unresolved Problems
ISS-001 (complementary study PDF, #9/#11).

## Pending User Approvals
Merge of the #8 PR. Gate C sign-off before Phase 3. `/CLAUDE.md` line 3 wording (owner's file).

## Next Actions
1. Finish #8 (full test run, gate C report, PR, review, owner merge).
2. Open Phase 3 issues (M2): feature registry and extraction profiling (TASK-020), CPU baselines B0–B4 on dev (TASK-021).
3. Keep test results sealed.

## Resume Instructions
`git -C D:\SitRegPilot status --branch`; `& "C:\Program Files\GitHub CLI\gh.exe" pr list -R magsiabdulaziz/sitregpilot`; reconcile PR_TRACKER; `.venv\Scripts\python.exe -m pytest -m "not requires_corpus"` (fast) or a full run (~5 min with the corpus).
