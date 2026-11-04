# Development workflow

Approved by the owner on 2026-11-05 ([DEC-003](project-memory/DECISIONS.md)). This is the operating procedure for every change to `magsiabdulaziz/sitregpilot`. Research-protocol gates (A–F) are defined by the owner's project brief (not stored in the repo) and summarised in [`methodology.md`](methodology.md) and [`experiment_plan.md`](experiment_plan.md); this file covers how code and docs get into `main`.

## 1. Principles
1. GitHub is the source of truth: every change traces through issue → branch → commits → PR → review → merge.
2. Nothing is committed directly to `main`. The only exception was the bootstrap commit `dac13cb`.
3. One PR is one coherent change.
4. AI agents may develop and review. **Only the owner merges.**
5. Every PR gets an independent review.
6. Nothing is called complete without evidence. A task is DONE only after an owner-approved merge.
7. The owner is the sole author: no `Co-Authored-By` trailers or tool-attribution footers ([DEC-004](project-memory/DECISIONS.md)).

## 2. Cycle
```
Issue → Planning → Branch → Implementation → Tests → Draft PR → Independent review
      → Revisions (same branch) → Checks → Ready for review → PR Approval Report
      → Owner decision → Owner merges → Memory update → Next issue
```

## 3. Issues
- Each issue gives: objective, problem/scope, technical notes, dependencies, acceptance criteria, testing requirements, priority, complexity, milestone, and labels. Use the task form in `.github/ISSUE_TEMPLATE/`.
- Labels follow `type:*`, `area:*`, `priority:P0–P2`, `phase:0–6`, `status:blocked`, `status:needs-owner`. Milestones are M0–M5.
- Ambiguous issues are not implemented. Refine them first (label `status:needs-owner`).
- Each issue is mirrored as a TASK-xxx row in [`project-memory/TASKS.md`](project-memory/TASKS.md).

## 4. Branches
- Name: `<type>/issue-<n>-<slug>`, with type ∈ feature, fix, refactor, docs, test, chore. Example: `feature/issue-5-ingest-validate`.
- Branch from an up-to-date `main` (`git fetch && git checkout -b … origin/main`).
- No long-lived branches other than `main`. Branches are deleted only with the owner's authorisation.
- Commits are small and meaningful, follow the Conventional-Commit style (`docs:`, `feat:`, `fix:`, `test:`, `chore:`, `refactor:`), and reference the issue (`Refs #n`; the final PR uses `Closes #n`).

## 5. Implementation rules for AI agents
Before coding: read the issue, relevant decisions (D-xx, DEC-xxx), affected modules, and existing conventions, and post a short plan as a PR description draft.
During: only authorised scope. No new major dependency, architectural change, or protocol change (labels, metrics, splits, exclusions, data sources) without owner approval. One writer per file. Shared schemas, dependency files, and memory files belong to the coordinator.
Before the PR: run the available checks (ruff, mypy, pytest once #3 lands) and record the outputs.

## 6. Pull requests
- Open as a **draft**. Mark ready only after checks pass and review findings are resolved.
- The body uses the template sections A–G: summary, linked issue, implementation details, testing evidence (including checks not run), risk assessment, review checklist, reviewer guidance.
- Documentation and memory updates belong in the PR they describe.

## 7. Independent review
- Reviewer: a fresh `general-purpose` agent with explicit **read-only** instructions (no edits, no state-changing git, no GitHub review actions) and access to the issue, the diff, and the test evidence; or the `code-review` skill. The implementer never reviews its own PR.
- Dimensions: correctness against acceptance criteria, architecture, code quality, security/data exposure, performance, tests and edge cases, regression risk, documentation; for research code also test-set sealing, train-only fitting, and raw-data integrity.
- Severity:

| Level | Meaning | Merge |
|---|---|---|
| Critical | wrong results, data/test leakage, secret or corpus-text exposure, data loss | blocks |
| Major | significant correctness, reliability, or maintainability problem; unmet acceptance criterion | blocks |
| Minor | real but limited issue | fix or record |
| Suggestion | optional | optional |

- Findings carry file:line, evidence, and a concrete fix. No invented defects; no "tests pass" without output.
- **Posting:** the agent acts through the owner's GitHub account, so it posts **comments only**. It never uses `gh pr review --approve` or `--request-changes`, because that would appear as the owner's own review.

## 8. Revisions
Fixes go to the same branch, with regression tests where applicable. Post a resolution table as a PR comment. Re-review covers the delta only. After two rounds, any remaining disagreement goes to the owner instead of looping. Purely stylistic disputes are not blocking.

## 9. Merge control (mandatory)
Before asking for a merge decision, the coordinator posts a **PR Approval Report** comment: PR number and title, linked issue, head SHA, change summary, tests/CI, findings and resolution, remaining risks, and a recommendation (Ready for approval / Changes required / Blocked). Then it waits.

| AI agents may | AI agents must not |
|---|---|
| create branches, commit, push PR branches, open and update PRs, run tests, review, recommend | merge without explicit owner approval, enable auto-merge, bypass checks, dismiss findings without justification, force-push any branch or rewrite pushed history without explicit owner authorisation, delete branches without authorisation, treat AI review or green CI as approval |

- Approval covers one PR at one head SHA. If anything is pushed afterwards, ask again. Silence or earlier approvals are not approval.
- When an agent merges on the owner's instruction, it uses `gh pr merge <n> --squash --match-head-commit <approved SHA>` (or `--merge` if the owner asks). An explicit method flag is required, because `gh` will not pick one non-interactively.
- **Merge method:** the owner's choice. #10 was merged by the owner with a merge commit. Agents use squash unless the owner specifies otherwise.

## 10. Quality gates (configured in #3)
GitHub Actions on PRs to `main`: ruff, mypy (core modules), pytest on ubuntu-latest using synthetic fixtures only (no corpus download), one Windows job for path/encoding tests, and pip-audit. Branch protection on `main` requires those checks, no force-push, and no deletion. The repo is private, so if the GitHub plan cannot enforce protection, the fallback is these written rules plus CI as an advisory check plus owner merge discipline, and the limitation is recorded in DECISIONS.

## 11. Failure handling
| Situation | Procedure |
|---|---|
| CI fails | Reproduce locally, fix on the branch, record a non-trivial cause in ISSUES_AND_SOLUTIONS, re-run. Never disable a check to get green. |
| Branch outdated / conflicts | `git fetch` then `git merge origin/main` into the branch (no rebase of pushed branches without approval); resolve, re-run checks; the report must cite the new head SHA. |
| Incomplete implementation | Keep the PR draft; list the remaining work in the PR and TASKS; do not report done. |
| Incorrect AI-generated code | Treat it as a review finding; add a regression test; record it in ISSUES_AND_SOLUTIONS. |
| Unexpected test failure | Investigate the root cause before changing the test; never weaken a test to pass. |
| Dependency conflict | Pin, document, and ask before adding or upgrading a major dependency. |
| Interrupted session | Resume from [`SESSION_HANDOFF.md`](project-memory/SESSION_HANDOFF.md); reconcile with `git status` and `gh pr list`. |
| Out-of-scope change made by accident | Revert it on the branch with a new commit (no history rewrite); note it in the PR. |
| Destructive git operation needed | Explain the consequences and get explicit owner authorisation first (e.g. the bootstrap rewrite, ISS-007). |
