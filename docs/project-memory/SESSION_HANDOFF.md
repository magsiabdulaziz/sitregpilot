# Session handoff

_Updated: 2026-11-05. Work **stopped at the owner's request** after the D-16 pilot. No processes are running._

## Current Objective
Phase 3b (D-15–D-17): #24 bounded vocabulary expansion → #25 full-document TF-IDF → #26 ablation + template diagnostic. Dev only; Phase 4 deferred.

## Last Verified State
- `main` = `e2c0d74` (PRs #10, #12–#18, #21, #22, #27 merged). Decision records D-15–D-17 on main.
- D-16 **training-only pilot completed** (`reports/baselines/vocab_pilot_D16.json`, commit `81a15a6`, clean tree):
  - 200k: vectoriser fit 71.4 s, B1-best LogReg fit 102.9 s, peak 1,671 MB, nnz 19.9M
  - 400k: vectoriser fit 76.2 s (ratio **1.07**), LogReg fit 101.7 s, peak **1,863 MB**, nnz 21.4M; vocabulary filled to 400,000
  - Under the **proposed** thresholds the outcome is **CONTINUE**. But the thresholds are **not yet confirmed by the owner**, so the 24 new settings have **not** been run.

## Active Task
TASK-023 / #24 on `feature/issue-24-vocab` (pushed; `origin/main` merged in; pilot script and report committed; **no PR yet**). Blocked on owner confirmation of the D-16 stop thresholds.

## Current Git Context
Local branch `feature/issue-24-vocab`. See [PR_TRACKER](PR_TRACKER.md).

## Decisions to Preserve
D-01/D-02 adopted; D-03…D-12, D-14, D-15, D-17 approved; D-16 approved with thresholds pending; D-13 blocked ([decisions](../decisions.md)). DEC-001…DEC-007. No co-author trailers. Test sealed.

## Unresolved Problems
ISS-001 (2021 study PDF). ISS-013 root cause unknown (mitigated by sequential fits).

## Pending User Approvals
1. Confirm (or replace) the D-16 stop thresholds.
2. `/CLAUDE.md` line 3 wording (owner's file).

## Next Actions
1. On threshold confirmation: run the 24 new 400k settings (12 per model) with the `baselines` CLI on a config containing only `max_features: [400000]`; select over the union with the existing 48; record the D-16 outcome in `docs/decisions.md`; PR → review → owner merge.
2. #25 full-document TF-IDF: B1-best and B2-best settings, `window_words` unset; pilot memory first (full documents have about 42M train words); separate from #24.
3. #26 ablation (B3 settings fixed: C 0.1, no class weight) and template diagnostic (manifest `template_seen_controlled`; confounders reported).

## Resume Instructions
`git -C D:\SitRegPilot status --branch`; read this file and PROJECT_STATE; `& "C:\Program Files\GitHub CLI\gh.exe" pr list -R magsiabdulaziz/sitregpilot`; fast tests `.venv\Scripts\python.exe -m pytest -m "not requires_corpus"`. Never run anything on the test partition. Never merge without an explicit owner instruction for the exact head SHA.
