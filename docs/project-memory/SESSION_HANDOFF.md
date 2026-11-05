# Session handoff

_Updated: 2026-11-05_

## Current Objective
Phase 3b (D-15–D-17): #23 decision records → #24 vocabulary pilot/expansion → #25 full-document TF-IDF → #26 ablation + template diagnostic. Dev only; Phase 4 deferred.

## Last Verified State
- `main` = `f8c6ace` (PRs #10, #12–#18, #21, #22 merged; protected, DEC-006). Repo public. Gate C approved. Features v1.1.0 and baselines B0–B4 on main.
- Data contracts on `main`: `audit`, `dedup`, `split` CLIs. Sealed split manifest `data/manifests/splits/split_manifest.csv` (sha in `reports/splits/split_report.json`); controlled train 33,870 / dev 4,843 / test 9,686; 53 excluded.
- **Test set is sealed: no model work may look at test results until Phase 5.**

## Active Task
TASK-022 / #23 on `docs/issue-23-phase3b-decisions`; then #24 (pilot first; stop if > 12 GB or > 3× fit time).

## Current Git Context
See [PR_TRACKER](PR_TRACKER.md). Merges need an explicit per-PR owner instruction in chat; the harness blocked the standing-instruction merge.

## Files Under Development
PR #22: `src/core_register/{evaluation,models,training,preprocessing}/`, `data/tasks.py`, `cli.py` (baselines, baselines-ling), `configs/experiments/cpu_baselines.yaml`, `reports/baselines/`, `scripts/baseline_summary.py`, tests.

## Decisions to Preserve
D-01/D-02 adopted, D-03…D-12 and D-14 approved, D-13 blocked ([decisions](../decisions.md)); DEC-001…DEC-007 ([DECISIONS](DECISIONS.md)). No co-author trailers.

## Unresolved Problems
ISS-001 (complementary study PDF, #9/#11).

## Pending User Approvals
Merge of PR #27 (decision records). Confirmation of the proposed D-16 stop thresholds (12 GB peak RSS; 3× vectoriser fit time). `/CLAUDE.md` line 3 wording (owner's file).

## Next Actions
1. #23 PR → review → owner merge.
2. #24 pilot (training-only, measurement only). Proposed stop thresholds (12 GB, 3× fit) are **pending owner confirmation**; if it passes and the owner confirms, run the 24 new settings (12 per model); record the D-16 outcome.
3. #25, then #26. Test stays sealed; every run is logged, failures included.

## Resume Instructions
`git -C D:\SitRegPilot status --branch`; `& "C:\Program Files\GitHub CLI\gh.exe" pr list -R magsiabdulaziz/sitregpilot`; reconcile PR_TRACKER; `.venv\Scripts\python.exe -m pytest -m "not requires_corpus"` (fast) or a full run (~5 min with the corpus).
