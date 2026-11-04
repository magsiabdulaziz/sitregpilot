# PR tracker

GitHub is authoritative for live status. Reconcile this file whenever GitHub access is available.
An AI review or green CI is **never** owner approval. Only the owner authorises merges, per PR revision.

| PR | Title | Issue / Task | Branch → base | CI | AI review | Owner approval | Merge |
|---|---|---|---|---|---|---|---|
| #10 | docs: Phase 0/1 records, approved protocol, and project memory | #1 / TASK-001, 002, 005 | `docs/issue-1-phase1-records` → `main` | none yet (CI arrives in #3) | round 1: Changes required → fixed; round 2: Ready for approval (2 Minor fixed) | not given | not merged |

### PR #10: docs: Phase 0/1 records, approved protocol, and project memory
- Issue / Task: #1 / TASK-001, TASK-002, TASK-005
- Branch: `docs/issue-1-phase1-records` → `main` (draft)
- Summary: Phase 0/1 docs, audit scripts and outputs, draft label schema, CLAUDE.md, project memory.
- Review round 1 (independent read-only agent, 2026-11-05): 3 Major, 7 Minor, 2 Suggestions; no Critical. Independent recount matched every checked number except the global median (635, not 634). Fixes are in the revision commit, except finding 4 for `/CLAUDE.md`, which is left to the owner (an agent must not edit CLAUDE.md on a reviewer's request).
- Review round 2 (same reviewer, delta a4f7cfb..7ac2e1d): all round-1 findings resolved; N1 (CRLF mixing) and N2 (CRLF JSON output) fixed in the following commit.
- CI / tests: no CI; manual checks recorded in the PR body and revision comments. Audit JSON reference hashes d4bf57b7…, 660f9365….
- Owner approval: not given
- Merge: not merged

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
