# Development log (append-only)

Times are not reliably recorded; dates are from the session environment.

## 2026-11-04: REA setup (owner request)
- Ran `npx rea-agents setup --client claude_code --yes` (rea-agents 6.7.0 from the npx cache). This added MCP server `rea` to `C:\Users\T15\.claude.json` (backup `.claude.json.rea.backup`) and the skill `reverse-engineer-anything`. Outside the repository.

## 2026-11-05: Phase 0/1 (TASK-001, TASK-002)
- Completed: verified fork and upstream HEAD `b57dbdb5…`; cloned to `data/raw/CORE-corpus`; SHA-256 of the 3 TSVs match the prior audit.
- Completed: `scripts/phase1_corpus_audit.py` (≈52 s) → `reports/audit/corpus_audit.json`; `scripts/phase1_template_overlap.py` → `template_overlap_indicator.json`.
- Discoveries: 455 label sets vs 460 raw strings (5 order variants); DP is the only sub that appears without its Table-1 parent (293 rows); site-template prefix/suffix groups strongly label-homogeneous (shortcut risk); paragraph breaks flattened.
- Read the primary article in full (local PDF). Could not access the complementary study (ISS-001).
- Wrote docs: environment, agent_inventory, source_ledger, compatibility, methodology, architecture, decisions, experiment_plan; draft label schema.
- The owner kept the `rea` registration and approved all of D-03…D-12.

## 2026-11-05: Environment (TASK-003)
- Completed: `git init` (branch `master`, `core.autocrlf=false`), `.gitignore`, `.venv`, installed `requirements/cpu.in` + `dev.in`, `en_core_web_sm` 3.8.0. Verified: spaCy 3.8.18 parses a test sentence; sklearn 1.9.1, numpy 2.5.4, pydantic 2.14.2 import.
- Not done: lock file, pyproject, first commit.

## 2026-11-05: Workflow and memory requests (TASK-004, TASK-005)
- The owner requested a GitHub PR-driven workflow (proposal only, no repo changes until approved) and a persistent memory system (to be established).
- Phase 2 paused (DEC-002). Discovery: `gh` not installed; no remote; no git identity; no commits.
- Created `/CLAUDE.md` and `docs/project-memory/*` (uncommitted). Workflow proposal delivered in chat.

## 2026-11-05: GitHub setup (TASK-003, TASK-004)
- The owner approved the workflow plan ("approve all") and chose a **private** repo.
- Completed: found the existing authenticated `gh` (ISS-006); repo-local identity (noreply); branch renamed `master`→`main`; bootstrap commit; created private repo `magsiabdulaziz/sitregpilot`, pushed `main`.
- Completed: 24 labels (GitHub defaults removed), milestones M0–M5 (#1–#6), issues #1–#9.
- Completed: rewrote the bootstrap commit to drop the co-author trailer at the owner's request (`ac52d41`→`dac13cb`, force-with-lease; ISS-007, DEC-004).
- Verified: both Phase 1 audit scripts reproduce `reports/audit/*.json` byte-for-byte (sha256 7c2272…, d0f789…).
- Planned: branch `docs/issue-1-phase1-records` → draft PR for issue #1.

## 2026-11-05: PR #10 review round 1 and revision
- Draft PR #10 opened (closes #1). An independent read-only `general-purpose` agent reviewed it: Changes required (3 Major, 7 Minor, 2 Suggestions, 0 Critical).
- Revision: approved-status wording (methodology, architecture, schema status), PR_TRACKER/TASKS reconciled, undefined AUD-* refs replaced with JSON keys, corpus-wide median corrected to 635 (independently verified), template-homogeneity wording quantified, D-09 count clarified; scripts: POSIX `source_dir`, robust split/`max(default=0)`/CRLF strip, invisible Unicode literals escaped.
- `reports/audit/corpus_audit.json` regenerated: only `source_dir` changed (`data\raw\…` → `data/raw/…`); new sha256 a61bb0c9…; template JSON unchanged (d0f789a0…); both byte-reproducible on re-run.
- Not changed: `/CLAUDE.md` finding 4 (left for the owner).
