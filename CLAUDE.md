# CLAUDE.md: SitRegPilot (CORE register classifier)

Explainable, reproducible English web-register classifier for a Linguistics PhD (CS co-supervision). CPU-first, Windows. The full research protocol is in `docs/methodology.md`; approved methodological decisions D-01…D-13 are in `docs/decisions.md`.

## Session start (mandatory)
1. Read `docs/project-memory/PROJECT_STATE.md`, then `SESSION_HANDOFF.md`.
2. Check the active rows in `docs/project-memory/TASKS.md`, related decisions (`docs/decisions.md` D-xx = research protocol; `docs/project-memory/DECISIONS.md` DEC-xxx = engineering/process), and `ISSUES_AND_SOLUTIONS.md`.
3. Run `git status --branch` and compare with the documented state. When memory and the repo disagree, trust repository evidence and record the discrepancy.
4. Give a short continuation plan before editing.

## While working
- Update the task status in TASKS.md when starting, blocking, or finishing work. Statuses: TODO, IN_PROGRESS, BLOCKED, IN_REVIEW, AWAITING_APPROVAL, DONE, CANCELLED.
- Record significant decisions in DECISIONS.md. Never silently reverse an accepted decision; supersede it with a new entry.
- Record non-trivial problems in ISSUES_AND_SOLUTIONS.md, and check it before troubleshooting a recurring problem.
- Append meaningful activity to DEVELOPMENT_LOG.md (append-only; completed vs planned kept distinct).
- Update PR_TRACKER.md when a PR is opened, reviewed, or changes state. GitHub is authoritative for live PR status.
- Before ending a session or after a milestone, update SESSION_HANDOFF.md and PROJECT_STATE.md.

## Hard rules
- Never claim completion without evidence (tests or commands run, outputs observed). Mark unknowns `UNKNOWN` / `UNVERIFIED`.
- Never merge, enable auto-merge, bypass checks, force-push protected branches, or delete branches without the owner's explicit approval for that specific PR revision. AI review and green CI are not owner approval.
- Never modify `data/raw/` (source corpus). Never commit corpus text, secrets, or large artifacts.
- Pause for owner approval before changing labels, primary metrics, split policy, exclusions, data sources, major dependencies, or architecture.
- The owner is the sole author. Never add `Co-Authored-By` trailers or "Generated with Claude Code" footers to commits or PRs.
- Do not use REA tools for this project (D-01). Do not invent agent names or commands.
- Use `.venv\Scripts\python.exe` (Python 3.14.5). Stream gzip, use UTF-8 and pathlib, and keep document IDs as strings.
