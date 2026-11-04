# Agent and tool inventory (Phase 0)

## 1. REA (`rea-agents`)

| Item | Evidence |
|---|---|
| Package identity | npm `rea-agents`, latest 6.8.0. Description: "Reverse engineer anything from your terminal or agent with one CLI and MCP server." Repo: `github.com/morluto/rea`, maintainer `morluto`. **This is the public reverse-engineering project, not a linguistics/data-science agent framework.** |
| How it got here | Earlier in this conversation (2026-11-04), at the user's request, the coordinator ran `npx rea-agents setup --client claude_code --yes`. That added an MCP server `rea` to `C:\Users\T15\.claude.json` (backup: `C:\Users\T15\.claude.json.rea.backup`) and installed the skill `~/.claude/skills/reverse-engineer-anything` (skill metadata version 42). |
| Pinned reference | `cmd.exe /d /c npx -y rea-agents@6.7.0 mcp` (6.7.0 came from the local npx cache) |
| Global install | `npm ls -g rea-agents` → empty; `rea` not on PATH |
| MCP health | `claude mcp list` → `rea … ✘ Failed to connect — connection timed out after 30000ms` |
| Exposed tools in this session | none (no `rea` tools loaded) |
| Doctor output at setup | `environment_healthy: false`; no analysis engines configured (Ghidra/IDA/JADX/Hopper absent) |
| Relevance to this project | **None.** Its own skill text says to skip REA for ordinary source analysis. It provides no linguistics, data, or testing agents. |

Decision (fallback, recorded in decisions.md D-01): REA is irrelevant, so the project uses native Claude Code subagents or one sequential session. I invented no `/rea` commands or specialist names. Reverse-engineering engines will not be installed.
The owner chose to **keep** the `rea` MCP registration (2026-11-05). It adds a connection timeout at session start and is not used here.

## 2. Native Claude Code agent types available in this session

Source: the Agent tool's agent-type list in this session (not inferred from documentation).

| Agent type | Tools (as listed) | Write access | Smoke test |
|---|---|---|---|
| `Explore` | all except Agent, Artifact*, ExitPlanMode, Edit, Write, NotebookEdit | No file-edit tools, **but Bash is included**, so it is not strictly read-only. Assignments must state "read-only". | untested |
| `Plan` | same as Explore | same caveat | untested |
| `general-purpose` | all | yes | untested |
| `claude` | all | yes | untested |
| `claude-code-guide`, `statusline-setup` | Claude-help / statusline only | — | not relevant |

There are no custom agent definitions (`.claude/agents` absent at project and user level).
Other mechanisms present: the `Workflow` tool (multi-agent scripts, which require explicit user opt-in) and skills `code-review`, `simplify`, `security-review`.
Invocation is the Agent tool with `subagent_type` set to the exact name above. There is no shell invocation. Subagents start without this conversation's context, so every handoff must be self-contained (docs/handoffs/).

## 3. Role → agent mapping (proposed)

| Role | Mapping | Notes |
|---|---|---|
| Coordinator | main session | owns schemas, configs, dependency files, decisions, merges |
| Research/data reviewer | `Explore` (read-only instruction) for source and corpus checks | an independent recount of audit numbers from raw files |
| Implementation worker | main session by default; `general-purpose` for bounded modules | one writer per module |
| Independent reviewer | fresh `general-purpose` agent with a read-only instruction, and/or the `code-review` skill | recomputes metrics from saved predictions; checks linguistic fixtures |

Concurrency is at most 2 workers. Phase 0/1 used **no subagents**: the coordinator did all of it sequentially. The independent recount of Phase 1 numbers is proposed as handoff H-001 after approval. Agreement between agents is not scientific evidence.
