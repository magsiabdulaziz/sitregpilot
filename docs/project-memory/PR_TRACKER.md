# PR tracker

GitHub is authoritative for live status. Reconcile this file whenever GitHub access is available.
An AI review or green CI is **never** owner approval. Only the owner authorises merges, per PR revision.

| PR | Title | Issue / Task | Branch → base | CI | AI review | Owner approval | Merge |
|---|---|---|---|---|---|---|---|
| #10 | docs: Phase 0/1 records, approved protocol, and project memory | #1 / TASK-001, 002, 005 | `docs/issue-1-phase1-records` → `main` | none yet (CI arrives in #3) | 3 rounds → Ready for approval | owner approved `ec6645c` (2026-11-05) | **merged by owner** `6fba587` (merge commit) |
| #12 | docs: PR-driven development workflow, templates, and CONTRIBUTING | #2 / TASK-004 | `docs/issue-2-workflow` → `main` | none (pre-CI) | 2 rounds → Ready for approval | merged by owner account (no explicit chat approval; see entry) | **merged** `f953420` (merge commit) |
| #13 | chore: CI quality gates, pyproject, and dependency lock | #3 / TASK-003 | `chore/issue-3-ci` → `main` | run 41909923088 green at `1bcc8f1`; re-run pending on revision | round 1: Changes required (1 Major, 4 Minor) → fixes pushed | not given | not merged |

### PR #13: chore: CI quality gates, pyproject, and dependency lock
- Issue / Task: #3 / TASK-003 · Branch: `chore/issue-3-ci` → `main` (draft)
- Round 1 (`1bcc8f1`): Changes required. Major 1: branch-protection result not recorded → protection is attempted after the revision's CI run, and the result goes into DEC-006. Minor: unused `tmp_path` and `.pyc` written into the repo (fixed); "no .gitattributes" (**incorrect**: it has been on `main` since PR #10); setuptools floor (fixed, ≥77); this tracker entry (added). Suggestions adopted: SHA-pinned actions v7, `persist-credentials: false`, no cancelling on `main`, lint-type installs from the lock, `pip check`, separate non-required `pip-audit` job plus a weekly schedule.
- Owner approval: not given · Merge: not merged

### PR #10: docs: Phase 0/1 records, approved protocol, and project memory
- Issue / Task: #1 / TASK-001, TASK-002, TASK-005
- Branch: `docs/issue-1-phase1-records` → `main` (draft)
- Summary: Phase 0/1 docs, audit scripts and outputs, draft label schema, CLAUDE.md, project memory.
- Review round 1 (independent read-only agent, 2026-11-05): 3 Major, 7 Minor, 2 Suggestions; no Critical. Independent recount matched every checked number except the global median (635, not 634). Fixes are in the revision commit, except finding 4 for `/CLAUDE.md`, which is left to the owner (an agent must not edit CLAUDE.md on a reviewer's request).
- Review round 2 (same reviewer, delta a4f7cfb..7ac2e1d): all round-1 findings resolved; N1 (CRLF mixing) and N2 (CRLF JSON output) fixed in the following commit.
- CI / tests: no CI; manual checks recorded in the PR body and revision comments. Audit JSON reference hashes d4bf57b7…, 660f9365….
- Review round 3 (`ec6645c`): Ready for approval. Approval Report posted (issuecomment-6641319488).
- Owner approval: "merge #10" for head `ec6645c` (2026-11-05).
- Merge: merge commit `6fba587` at 2026-11-04T20:28:49Z UTC (= 2026-11-05 01:28 +0500 local) by account `magsiabdulaziz`. Agents act through the same account, so the API cannot tell who clicked; per the agent session log, the agent's `--squash --match-head-commit` attempt ran afterwards and `gh` reported "already merged", so the agent did not perform the merge. The merged tree equals `ec6645c`'s tree (`359c954`). Issue #1 closed. Branch `docs/issue-1-phase1-records` kept (deletion not authorised).

### PR #12: docs: PR-driven development workflow, templates, and CONTRIBUTING
- Issue / Task: #2 / TASK-004
- Branch: `docs/issue-2-workflow` → `main`
- Review round 1 (`e3b7d9e`): Ready; 0 Critical, 0 Major, 4 Minor, 3 Suggestions → fixed in `9910af8`. Round 2 (delta): Ready for approval.
- Merge: the owner's account marked it ready (20:37:32Z) and merged it (20:37:41Z UTC, merge commit `f953420`) while the agent was preparing the Approval Report, which was posted afterwards (issuecomment-6641522151). The agent performed no merge action on #12. The merged head `9910af8` equals the reviewed head; trees verified equal. DEC-005 accepted by this merge.

Template for each PR entry:

### PR #n: title
- Issue / Task: #i / TASK-xxx
- Branch: `type/issue-i-slug` → `main`
- Summary:
- Review findings (Critical/Major/Minor/Suggestion) and resolution:
- CI / tests (commit SHA):
- Revisions requested:
- Owner approval: (revision SHA, date) / not given
- Merge: (merge SHA, date) / not merged
