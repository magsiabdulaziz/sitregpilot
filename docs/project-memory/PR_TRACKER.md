# PR tracker

GitHub is authoritative for live status. Reconcile this file whenever GitHub access is available.
An AI review or green CI is **never** owner approval. Only the owner authorises merges, per PR revision.

| PR | Title | Issue / Task | Branch → base | CI | AI review | Owner approval | Merge |
|---|---|---|---|---|---|---|---|
| #10 | docs: Phase 0/1 records, approved protocol, and project memory | #1 / TASK-001, 002, 005 | `docs/issue-1-phase1-records` → `main` | none yet (CI arrives in #3) | 3 rounds → Ready for approval | owner approved `ec6645c` (2026-11-05) | **merged by owner** `6fba587` (merge commit) |
| #12 | docs: PR-driven development workflow, templates, and CONTRIBUTING | #2 / TASK-004 | `docs/issue-2-workflow` → `main` | none (pre-CI) | 2 rounds → Ready for approval | merged by owner account (no explicit chat approval; see entry) | **merged** `f953420` (merge commit) |
| #13 | chore: CI quality gates, pyproject, and dependency lock | #3 / TASK-003 | `chore/issue-3-ci` → `main` | green at every revision; final run 41911457779 (`c21d223`) | round 1 Changes required → fixed; round 2 Ready for approval | owner "merge #13" for `c21d223` | **squash-merged by agent on owner instruction** `9f54304` |

### PR #13: chore: CI quality gates, pyproject, and dependency lock
- Issue / Task: #3 / TASK-003 · Branch: `chore/issue-3-ci` → `main` (draft)
- Round 1 (`1bcc8f1`): Changes required. Major 1: branch-protection result not recorded → protection is attempted after the revision's CI run, and the result goes into DEC-006. Minor: unused `tmp_path` and `.pyc` written into the repo (fixed); "no .gitattributes" (**incorrect**: it has been on `main` since PR #10); setuptools floor (fixed, ≥77); this tracker entry (added). Suggestions adopted: SHA-pinned actions v7, `persist-credentials: false`, no cancelling on `main`, lint-type installs from the lock, `pip check`, separate non-required `pip-audit` job plus a weekly schedule.
- Round 2 (`c21d223`): Ready for approval; Approval Report posted (issuecomment-6641989952).
- Owner approval: "merge #13" (2026-11-05) for head `c21d223`.
- Merge: `gh pr merge 13 --squash --match-head-commit c21d223…` → `9f54304` (2026-11-04T21:01:27Z UTC); tree verified identical to `c21d223`; issue #3 closed. A first attempt aborted before merging due to a PowerShell `--jq` quoting error in the head-SHA guard (no state change).
| #14 | feat: package skeleton, typed config, streaming ingest/validate, audit CLI | #5 / TASK-010 | `feature/issue-5-ingest-validate` → `main` | run 41913381331 green at `76c1958` | round 1 Ready (4 Minor fixed); round 2 Ready for approval | owner "merge #14" for `c371c47` | **squash-merged on owner instruction** `7848760` |
| #15 | feat: exact and verified near-duplicate grouping (D-07) | #6 / TASK-011 | `feature/issue-6-dedup` → `main` | green at `8e22f76` | 2 rounds → Ready | owner "merge #15" for `8e22f76` | **squash-merged** `cddfe58` |
| #16 | test: record independent recount (H-001) | #4 / TASK-006 | `test/issue-4-recount` → `main` | green at `3a899be` | round 1 Changes required (coverage) → part 2; round 2 Ready | owner "merge #16" for `3a899be` | **squash-merged** `38c9945` |
| #17 | feat: released/controlled split and cohort manifests; seal test | #7 / TASK-012 | `feature/issue-7-splits` → `main` | green at `cf5469a` | review finished **after** merge: Ready (0 Critical, 0 Major, 2 Minor, 3 Suggestions; fixed in the #8 PR) | owner "merge #17" for `cf5469a`, **before review completed** | **squash-merged** `c6eab9b` |

### PR #15 / PR #16
- #15: round 1 at `5bf433a` Ready (the reviewer independently matched all 31 Jaccard values, the 12 exact groups and the manifest hash); 2 Minor + 1 Suggestion fixed in `d7986cc`; delta Ready. `origin/main` was merged in after #16 (head `8e22f76`, docs-only delta; CI green); merged on the owner's explicit instruction.
- #16: the agent's merge attempt under the standing instruction was **blocked by the Claude Code auto-mode classifier ("Merge Without Review")** and not executed. It was merged after the owner said "merge #16". Since then every merge needs an explicit per-PR owner approval in chat (unless the owner adds a permission rule).

### PR #14: feat: package skeleton, typed config, streaming ingest/validate, audit CLI
- Round 1 (`76c1958`): Ready for approval. The reviewer re-ran 24 tests and the CLI; binary scan of the corpus found 0 rows with bare CR or other line-separator characters, so there is no divergence from the reference. Minor findings fixed: empty ID → MALFORMED; whitespace-only text → EMPTY_INPUT (corpus has none; DEC-007); architecture Record contract aligned; config rejects duplicate file names, stray hashes, non-bool `verify_hashes`. Suggestions adopted: stronger integration test (per-split code counts, label sets, ws max, statuses = lines), bare-CR fixture, issue strings truncated to 80 chars, status precedence documented.
- Round 2 (`c371c47`): Ready for approval; Approval Report posted (issuecomment-6642339661).
- Merge: `--squash --match-head-commit c371c47…` → `7848760`; tree verified identical; issue #5 closed; DEC-007 accepted.

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
