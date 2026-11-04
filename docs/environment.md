# Environment audit (Phase 0)

Audited 2026-11-04/05 by the coordinator session (Claude Code, single sequential session).
Status keys: **verified** (command run, output observed) · **absent** · **untested**.

## Host

| Item | Value | Status |
|---|---|---|
| OS | Windows 11 Pro 10.0.26300 (PowerShell 5.1.26100) | verified |
| CPU | Intel Core i5-10310U, 4 cores / 8 logical, 1.70 GHz | verified |
| RAM | 23.8 GB | verified |
| GPU | Intel UHD Graphics (integrated, ~1 GB shared). **No CUDA GPU.** | verified |
| Free disk | D: 107.4 GB, C: 14.0 GB | verified |
| Shell used by agent | Git Bash (POSIX) via Claude Code; PowerShell available | verified |

Implication: all Phase 2–3 work is CPU-only. C: has limited free space, so caches, venv, and artifacts stay on D:.

## Project root

- `D:\SitRegPilot`. It is **not a Git repository**. Run manifests need a commit hash and dirty state, so Phase 2 proposes `git init` with a `.gitignore` that excludes `data/raw`, `data/interim`, `artifacts/`, and `.venv/` (pending approval).
- Pre-existing user file: `s10579-022-09624-1.pdf` (primary article). Untouched.
- Added in this phase: `scripts/phase1_corpus_audit.py`, `scripts/phase1_template_overlap.py`, `reports/audit/*.json`, `docs/*.md`, `schemas/labels/label_schema_v0.draft.json`, `data/raw/CORE-corpus/` (clone).

## Toolchain

| Tool | Version | Status |
|---|---|---|
| Claude Code | 2.1.318 | verified |
| Python | 3.14.5 (`C:\Python314\python.exe`; the only interpreter `py -0p` lists) | verified |
| pip | 26.1.1 | verified |
| uv / conda | — | absent |
| Node / npm | v24.15.0 / 11.16.0 | verified |
| Git | 2.54.0.windows.1 | verified |
| `rea` on PATH | — | absent (see agent_inventory.md) |

No scientific Python packages are installed globally. On 2026-11-04, I checked that cp314 Windows binary wheels **exist** on PyPI for numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.1.1, pyarrow 26.0.1, and spacy 3.8.18. I downloaded them to a temp folder without installing.
**Verified 2026-11-05** in `.venv`: spaCy 3.8.18 + `en_core_web_sm` 3.8.0 install, load, and parse (tags/dependencies observed); scikit-learn 1.9.1, numpy 2.5.4, pydantic 2.14.2 import. Still **untested**: PyTorch cp314 wheels (needed only for Phase 4). No lock file yet (TASK-003).

Proposed environment (pending approval): `D:\SitRegPilot\.venv` (stdlib `venv`), dependency groups `cpu` (core) and `neural` (optional), and a frozen lock (`pip freeze` → `requirements/cpu.lock.txt`). Thread caps: `OMP_NUM_THREADS`/`MKL_NUM_THREADS` ≤ 4; spaCy `n_process` ≤ 3.

## Claude configuration

- `CLAUDE_CONFIG_DIR`: unset, so the active root is `C:\Users\T15\.claude` (user-level config in `C:\Users\T15\.claude.json`).
- `~/.claude/settings.json`: `autoUpdatesChannel`, `theme` only.
- `~/.claude/agents`, `~/.claude/commands`: absent. `~/.claude/skills/`: `reverse-engineer-anything` (REA skill).
- Project-level `.claude/`, `CLAUDE.md`, `.mcp.json`: absent.

## Source reachability (verified 2026-11-05)

| Source | Result |
|---|---|
| github.com/magsiabdulaziz/CORE-corpus | reachable; HEAD `b57dbdb5ebee4b2688fa94889a2cbdb341d86ee7` |
| github.com/TurkuNLP/CORE-corpus | reachable; HEAD `b57dbdb5…` (identical); fork has no extra commits |
| Primary article PDF | local copy read in full (35 pp.) |
| Complementary study 10.1007/s10579-020-09519-z | **not accessed**: Springer redirects automated requests to a login, and no local PDF exists. Needs a user-supplied PDF. |
| rea.tools / github.com/morluto/rea | npm metadata verified (`npm view`); site not fetched (not needed) |
