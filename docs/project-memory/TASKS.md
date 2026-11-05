# Tasks

Statuses: TODO · IN_PROGRESS · BLOCKED · IN_REVIEW · AWAITING_APPROVAL · DONE · CANCELLED.
DONE requires verification evidence and, once the PR workflow is active, an owner-approved merge. Tasks from before the workflow are marked AWAITING_APPROVAL until their files are committed through the first PR.

| ID | Title | Pri | Status | Issue | Depends | PR |
|---|---|---|---|---|---|---|
| TASK-001 | Phase 0 environment & agent audit | P0 | DONE | #1 | — | #10 |
| TASK-002 | Phase 1 corpus audit, source ledger, protocol | P0 | DONE | #1 | 001 | #10 |
| TASK-003 | Dev environment: git init, venv, deps, lock | P0 | DONE | #3 | 002 | #13 |
| TASK-004 | GitHub PR-driven workflow design | P0 | DONE | #2 | — | #12 |
| TASK-005 | Persistent project-memory system | P0 | DONE | #1 | — | #10 |
| TASK-006 | Independent recount of audit numbers (H-001) | P1 | DONE | #4 | 002 (#1) | — |
| TASK-007 | Obtain & ledger the complementary 2021 study | P2 | BLOCKED | #9, #11 | owner PDF | — |
| TASK-010 | Package skeleton, config, ingest/validate, `audit` CLI | P0 | DONE | #5 | 003, 004 | #14 |
| TASK-011 | Exact + MinHash near-duplicate grouping | P0 | DONE | #6 | 010 | #15 |
| TASK-012 | released/controlled split manifests, test sealing | P0 | DONE | #7 | 011 | #17 |
| TASK-013 | Data-contract test suite (Phase 2 gate C) | P0 | DONE | #8 | 010–012 | #18 |
| TASK-020 | Phase 3: linguistic feature registry & extraction | P0 | DONE | #19 | 013 | #21 |
| TASK-021 | Phase 3: CPU baselines B0–B4 on dev | P0 | IN_REVIEW | #20 | 013, 020 | #22 |

## Details

### TASK-001: Phase 0 environment & agent audit
Scope: hardware, toolchain, Claude config, REA identity, sources. Acceptance: capabilities recorded, with absent/untested distinguished. Evidence: [environment.md](../environment.md), [agent_inventory.md](../agent_inventory.md). **DONE:** merged in PR #10 (head `ec6645c`, merge `6fba587`, 2026-11-05 local +0500); issue #1 closed.

### TASK-002: Phase 1 corpus audit and protocol
Acceptance: counts reconcile; ledger written; protocol approved. Evidence: `reports/audit/corpus_audit.json` (row counts and hashes match the prior audit; 455 sets vs 460 strings explained), [source_ledger](../source_ledger.md), [methodology](../methodology.md). The owner approved the method gate on 2026-11-05. Independent recount pending (TASK-006). **DONE:** merged in PR #10 (`6fba587`); audit JSON byte-reproducible (d4bf57b7…, 660f9365…).

### TASK-003: Dev environment
Done: `git init` (branch `master`, renamed to `main`), `.gitignore`, `.venv`, `pip install -r requirements/cpu.in -r requirements/dev.in`, `en_core_web_sm` 3.8.0. Load test passed.
Done: repo-local git identity `magsiabdulaziz <65072637+magsiabdulaziz@users.noreply.github.com>`; branch `main`; bootstrap commit `dac13cb` (.gitignore, LICENSE Apache-2.0) pushed. **DONE:** pyproject, lock, package stub, tests, CI and branch protection merged in PR #13 (head `c21d223`, squash `9f54304`, owner-approved "merge #13", 2026-11-05).

### TASK-004: GitHub PR workflow design
Plan **approved** by the owner on 2026-11-05 (DEC-003). Done outside the repo: private repo `magsiabdulaziz/sitregpilot` created; 24 labels and milestones M0–M5 created; issues #1–#9 opened. **DONE:** merged by the owner's account in PR #12 (head `9910af8`, merge commit `f953420`, 2026-11-04T20:37:41Z UTC); issue #2 closed.

### TASK-005: Project-memory system
Files: `/CLAUDE.md`, `docs/project-memory/*`. Acceptance: files exist, links are valid, IDs are consistent, no secrets, the handoff matches the real state. Validation is recorded in DEVELOPMENT_LOG 2026-11-05. **DONE:** merged in PR #10 (`6fba587`).

### TASK-006: Independent recount (H-001)
Read-only `Explore` agent recomputes audit §2 numbers from the raw files. Acceptance: every mismatch reported or confirmed absent.

### TASK-007: Complementary study
Needs a PDF of Laippala, Egbert, Biber & Kyröläinen (2021), LRE 55(3):757–788. See ISS-001. GitHub: #9; the owner opened #11 (2026-11-05) for its acceptance criterion (the ledger section), treated as part of this task.

### TASK-010 – TASK-013: Phase 2 data contracts
Scope and acceptance criteria: [experiment_plan.md](../experiment_plan.md) P2-1…P2-4 and the master prompt Phase 2. Each becomes one GitHub issue and one PR.

### TASK-020 / TASK-021: Phase 3
Scope: [methodology §6–7](../methodology.md), [experiment_plan](../experiment_plan.md) B0–B6. Test-set results stay sealed until Phase 5.
