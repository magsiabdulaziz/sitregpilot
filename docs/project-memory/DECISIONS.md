# Engineering and process decisions (DEC-xxx)

The research-protocol decisions (D-01/D-02 adopted; D-03…D-12 approved by the owner on 2026-11-05; D-13 blocked) live in [`docs/decisions.md`](../decisions.md) and are not duplicated here.

## DEC-001: Markdown project memory under `docs/project-memory/`

**Date:** 2026-11-05
**Status:** Accepted (owner instruction, 2026-11-05)
**Related Task:** TASK-005
**Related PR:** none yet

### Context
The owner requires persistent cross-session memory. A methodological decision register (`docs/decisions.md`) and docs set already existed.

### Alternatives Considered
(a) Move D-xx into a new DECISIONS.md; (b) keep both, with separate scopes and cross-links.

### Decision
Option (b): D-xx stays canonical for the research protocol; DEC-xxx covers engineering and process.

### Rationale
Avoids rewriting owner-approved records and avoids duplication.

### Consequences
Two registers; CLAUDE.md and the memory README point to both.

### Implementation Impact
`/CLAUDE.md`, `docs/project-memory/*`.

## DEC-002: Pause Phase 2 implementation until the PR workflow is approved

**Date:** 2026-11-05
**Status:** Accepted (follows the owner instruction "do not modify the repository until I approve the plan")
**Related Task:** TASK-004, TASK-010

### Context
The owner approved the method gate, then asked for a PR-driven workflow before further repository changes.

### Decision
No package code is written and no commits are made until the workflow is approved. Already-created local, uncommitted files stay as they are.

### Consequences
Phase 2 is delayed by one approval round, but every implementation change is traceable through issues and PRs.

## DEC-003: Proposed GitHub workflow (summary)

**Date:** 2026-11-05
**Status:** Accepted (owner "approve all", 2026-11-05)
**Related Task:** TASK-004

### Decision
Protected-`main` trunk workflow; one issue → one branch (`<type>/issue-<n>-<slug>`) → one draft PR; independent AI review by a separate fresh-context agent; light GitHub Actions CI (ruff, mypy on core, pytest unit with synthetic fixtures; no corpus in CI); the owner alone merges. The full proposal was given in chat on 2026-11-05; once approved it will be written to `docs/DEVELOPMENT_WORKFLOW.md`.

_Amended by [DEC-005](#dec-005-merge-method-is-the-owners-choice) (merge method)._

### Resolved points (2026-11-05)
Repo `magsiabdulaziz/sitregpilot`, **private** (owner choice). Commit identity is the owner's GitHub noreply address, set repo-locally. Bootstrap commit straight to `main` approved as the single exception. The account plan is UNKNOWN (not visible to the token), so whether branch protection is enforceable on a private repo is tested in issue #3, with a documented fallback if not.

## DEC-004: Owner is the sole author of commits and PRs

**Date:** 2026-11-05
**Status:** Accepted (owner instruction)
**Related Task:** all

### Context
The bootstrap commit carried a `Co-Authored-By: Claude` trailer.

### Decision
No `Co-Authored-By` trailers or "Generated with Claude Code" footers on commits or PRs (rule in `/CLAUDE.md`). With the owner's explicit authorisation, the bootstrap commit was rewritten (`ac52d41` → `dac13cb`) and force-pushed with lease before branch protection existed.

### Consequences
AI assistance is disclosed in project docs (agent_inventory, development log), not in commit metadata. No further history rewrites without new authorisation.

## DEC-005: Merge method is the owner's choice

**Date:** 2026-11-05
**Status:** Accepted (owner merged PR #12, 2026-11-05). Amends DEC-003 (merge method only; control rules unchanged).
**Related PR:** #10

### Context
The workflow proposal presented in chat (2026-11-05), summarised as DEC-003, planned squash merges. PR #10 was merged with a merge commit by the owner's account (per `gh` output: the agent's squash attempt reported "already merged").

### Decision
The owner picks the merge method per PR. When an agent merges on the owner's explicit instruction, it squash-merges with `--match-head-commit` unless told otherwise.

### Consequences
`main` may contain merge commits. Traceability is unaffected (every merge references its PR).

## DEC-006: CI check roles and branch protection on `main`

**Date:** 2026-11-05
**Status:** Proposed (protection settings are applied under the approved workflow plan; the whole entry is accepted when the owner merges PR #13)
**Related Task:** TASK-003 · **Related PR:** #13

### Decision
- **Required checks:** `lint-type`, `test (ubuntu-latest)`, `test (windows-latest)`.
- **`pip-audit`:** runs as a separate job on every PR/push plus weekly, and is **not required**. A newly published CVE is shown but does not block unrelated PRs; a red `pip-audit` becomes a `type:fix` issue.
- **Protection on `main`:** PR required with **0** required approvals (agents act through the owner's account, and GitHub forbids self-approval); required checks strict (branch up to date); no force-push; no deletion; applies to admins as well, so the shared account cannot bypass it by accident.

### Result (issue #3 acceptance criterion)
**Enforced** on 2026-11-05 via `PUT /repos/magsiabdulaziz/sitregpilot/branches/main/protection` (possible because the repo is currently public, ISS-009). API response verified: checks `lint-type`, `test (ubuntu-latest)`, `test (windows-latest)`, strict; enforce_admins true; 0 approvals; force-push and deletion disabled. If the repo goes back to private on a free plan, re-check whether GitHub still enforces it; the fallback is DEVELOPMENT_WORKFLOW §10.

### Consequences
Even the owner cannot push directly to `main` while `enforce_admins` is on. The owner can switch it off in Settings → Branches if needed.
