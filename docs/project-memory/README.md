# Project memory

Markdown memory that lets any Claude Code session or agent resume work without relying on conversation history. The operating instructions are in [`/CLAUDE.md`](../../CLAUDE.md).

| File | Purpose | Update when |
|---|---|---|
| [PROJECT_STATE.md](PROJECT_STATE.md) | current status snapshot (kept short) | milestones, phase changes, new blockers |
| [SESSION_HANDOFF.md](SESSION_HANDOFF.md) | exact resume point | end of session, interruption, milestone |
| [TASKS.md](TASKS.md) | master task tracker (TASK-xxx) | task starts, changes status, finishes |
| [DECISIONS.md](DECISIONS.md) | engineering/process decisions (DEC-xxx) | a significant decision is proposed, accepted, or superseded |
| [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) | append-only chronological log | meaningful work completed |
| [ISSUES_AND_SOLUTIONS.md](ISSUES_AND_SOLUTIONS.md) | problem knowledge base (ISS-xxx) | non-trivial problem found or resolved |
| [PR_TRACKER.md](PR_TRACKER.md) | PR history (mirror of GitHub) | a PR is opened, reviewed, revised, approved, or merged |

Canonical records that live elsewhere (link to them; don't duplicate):
- Research-protocol decisions D-01…D-13: [`docs/decisions.md`](../decisions.md)
- Methodology / architecture / experiment plan: [`docs/methodology.md`](../methodology.md), [`docs/architecture.md`](../architecture.md), [`docs/experiment_plan.md`](../experiment_plan.md)
- Sources and evidence: [`docs/source_ledger.md`](../source_ledger.md), [`docs/compatibility.md`](../compatibility.md)
- Environment and agents: [`docs/environment.md`](../environment.md), [`docs/agent_inventory.md`](../agent_inventory.md)
- Agent task handoffs: `docs/handoffs/` (created when the first handoff is issued)

Single writer: the coordinating session owns these files. Subagents report back, and the coordinator reconciles their reports into memory.
