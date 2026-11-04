# Project state

_Last updated: 2026-11-05 (coordinator session)_

## Objective
Explainable, reproducible English web-register classifier on CORE, comparing lexical, grammatical, and combined representations. CPU-first on Windows. Details: [methodology](../methodology.md).

## Phase
- Phase 0/1 complete; **method gate approved** 2026-11-05 ([decisions](../decisions.md) D-03…D-12).
- GitHub PR workflow **approved** (DEC-003). Milestone M0 in progress: #1 (PR #10) and #2 (PR #12) merged; #3 in review.
- Phase 2 (M1) not started; no package code exists.

## Repository
- GitHub: `magsiabdulaziz/sitregpilot` (**private**), default branch `main` = `f953420` (PRs #10, #12 merged). Not yet protected (issue #3).
- `gh` at `C:\Program Files\GitHub CLI\gh.exe` (not on the Git Bash PATH). Commit identity is the owner (sole author, DEC-004).
- Issues #1, #2 closed. Open: #3–#9, #11 (M0: #3; M1: #4–#9; #11 owner-created, part of TASK-007). PRs: see [PR_TRACKER](PR_TRACKER.md).

## Implemented (verified)
Audit scripts + byte-reproducible outputs; draft label schema; `.venv` (spaCy + en_core_web_sm verified). No lock file yet.

## Constraints
No GPU; Python 3.14.5; no corpus text in Git; raw data read-only; owner merges; owner is the sole author.

## Blockers
#9 / TASK-007: complementary study PDF (ISS-001).

## Pending owner approvals
Merge of the issue-#3 PR (after CI, review, and the Approval Report). Owner's call: `/CLAUDE.md` line 3 wording (D-01…D-13 statuses).

## Next priorities
See [SESSION_HANDOFF](SESSION_HANDOFF.md).
