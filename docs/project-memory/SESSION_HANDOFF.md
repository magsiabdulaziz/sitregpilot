# Session handoff

_Updated: 2026-11-05_

## Current Objective
M1 (Phase 2 data contracts): #5 → #6 → #7 → #8, plus #4 (independent recount) in parallel.

## Last Verified State
- `main` = `9f54304` (M0 complete; protected, DEC-006). Repo public (owner-confirmed).
- #5 implementation: ruff/mypy-strict clean; 19 unit tests pass; 5 corpus integration tests pass locally; CLI audit reproduces 48,452 rows / 455 sets / 460 raw strings / 60,153,840 whitespace words in ~11 s; raw hashes unchanged.

## Active Task
TASK-010 / #5: branch `feature/issue-5-ingest-validate` → draft PR → CI → independent review → Approval Report → owner decision.

## Current Git Context
See [PR_TRACKER](PR_TRACKER.md). Direct pushes to `main` are blocked by protection (also for the owner, via enforce_admins).

## Files Under Development
`src/core_register/{config.py,cli.py,data/*}`, `configs/data/core.yaml`, `tests/{conftest.py,unit/test_ingest.py,unit/test_audit_cli.py,integration/}`, README CLI section, memory files.

## Decisions to Preserve
D-01/D-02 adopted, D-03…D-12 approved, D-13 blocked ([decisions](../decisions.md)); DEC-001…DEC-006 ([DECISIONS](DECISIONS.md)). Test set sealed until Phase 5. No co-author trailers.

## Unresolved Problems
ISS-001 (complementary study PDF, #9/#11).

## Pending User Approvals
Merge of the #5 PR. `/CLAUDE.md` line 3 wording (owner's file).

## Next Actions
1. Finish #5 (PR, CI, review, report, owner decision).
2. #6 near-duplicate grouping (thresholds frozen in config first, D-07); #4 recount via a read-only agent.
3. #7 split manifests and test sealing; #8 gate-C suite.

## Resume Instructions
`git -C D:\SitRegPilot status --branch`; `& "C:\Program Files\GitHub CLI\gh.exe" pr list -R magsiabdulaziz/sitregpilot`; reconcile PR_TRACKER; run `.venv\Scripts\python.exe -m pytest`. Never merge without explicit owner approval of the exact head SHA (`--match-head-commit`).
