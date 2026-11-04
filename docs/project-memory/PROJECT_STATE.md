# Project state

_Last updated: 2026-11-05 (coordinator session)_

## Objective
Explainable, reproducible English web-register classifier on CORE, comparing lexical, grammatical, and combined representations. CPU-first on Windows. Details: [methodology](../methodology.md).

## Phase
- Phase 0/1 complete; **method gate approved** 2026-11-05 ([decisions](../decisions.md) D-03…D-12).
- **M0 (bootstrap & governance) complete:** #1 (PR #10), #2 (PR #12), #3 (PR #13) merged.
- **M1 / Phase 2 in progress:** #5 (TASK-010) on `feature/issue-5-ingest-validate`.

## Repository
- GitHub: `magsiabdulaziz/sitregpilot`, **public** (owner-confirmed 2026-11-05, ISS-009). `main` = `9f54304`.
- `main` protected (DEC-006): PR required (0 approvals); required checks `lint-type`, `test (ubuntu-latest)`, `test (windows-latest)` (strict); enforce_admins; no force-push or deletion. `pip-audit` runs but is not required.
- `gh` at `C:\Program Files\GitHub CLI\gh.exe`. Sole author: the owner (DEC-004).
- Closed issues: #1–#3. Open: #4–#9, #11. PRs: see [PR_TRACKER](PR_TRACKER.md).

## Implemented (verified)
- On `main`: audit scripts + byte-reproducible outputs; draft label schema; pyproject; exact lock; CI; package stub.
- On the #5 branch (unmerged): config, label loader, hash verification, streaming ingest with statuses, package `audit` CLI. Reproduces the Phase 1 counts on the real corpus (integration test).

## Constraints
No GPU; Python 3.14.5; no corpus text in Git; raw data read-only; owner merges; owner is the sole author.

## Blockers
#9 / #11 / TASK-007: complementary study PDF (ISS-001).

## Pending owner approvals
Merge of the #5 PR (after CI, review, and the Approval Report). Owner's call: `/CLAUDE.md` line 3 wording (D-01…D-13 statuses).

## Next priorities
See [SESSION_HANDOFF](SESSION_HANDOFF.md).
