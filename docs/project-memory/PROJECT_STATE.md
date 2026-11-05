# Project state

_Last updated: 2026-11-05 (coordinator session; work stopped at the owner's request)_

## Objective
Explainable, reproducible English web-register classifier on CORE, comparing lexical, grammatical, and combined representations. CPU-first on Windows. Details: [methodology](../methodology.md).

## Phase
- Phase 0/1 complete; method gate approved (D-03…D-12).
- **M0** complete (PRs #10, #12, #13). **M1 / Phase 2** complete; gate C approved (PR #18). Test set **sealed** (controlled test 9,686 IDs, sha256 `cc33a023…`).
- **M2 / Phase 3:** features (PR #21, registry v1.1.0) and baselines B0–B4 (PR #22, dev only) merged. Dev macro-F1: B1 0.610, B2 0.605, B3 0.479, B4 0.613 (optimistic).
- **Phase 3b** (D-15, D-16, D-17; PR #27 merged): #24 vocabulary expansion (pilot done, **blocked on threshold confirmation**), #25 full-document TF-IDF (not started), #26 ablation + template diagnostic (not started). **Phase 4 deferred** (D-17).

## Repository
- GitHub `magsiabdulaziz/sitregpilot`, **public** (ISS-009). `main` = `e2c0d74`. Protected (DEC-006): PR required, 3 required checks, enforce_admins, no force-push or deletion.
- `gh` at `C:\Program Files\GitHub CLI\gh.exe`. Sole author: the owner (DEC-004). Merges need an explicit per-PR owner instruction (the harness blocks others).
- Open issues: #9, #11 (2021 study PDF), #24, #25, #26. Branch in progress: `feature/issue-24-vocab` (pushed, no PR yet).

## Implemented on `main` (verified)
Audit/dedup/split/features/baselines/baselines-ling CLIs; sealed split manifest; feature cache v1.1.0 (git-ignored, sha in report); dev results in `reports/baselines/`; CI with 3 required checks.

## Constraints
No GPU; Python 3.14.5; no corpus text in Git; raw data read-only; test sealed until Phase 5; fits run sequentially (`n_jobs: 1`, ISS-012/013).

## Blockers
- #24: owner must confirm or replace the D-16 stop thresholds before the 24 new settings run.
- #9 / #11: complementary study PDF (ISS-001).

## Pending owner approvals
D-16 stop thresholds (proposed: peak RSS > 12 GB, or 400k vectoriser fit > 3× the 200k fit). `/CLAUDE.md` line 3 wording (owner's file).

## Next priorities
See [SESSION_HANDOFF](SESSION_HANDOFF.md).
