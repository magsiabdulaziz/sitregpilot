# Contributing

This is single-owner PhD research software. All changes follow [`docs/DEVELOPMENT_WORKFLOW.md`](docs/DEVELOPMENT_WORKFLOW.md); the short version is below.

1. **Start from an issue** with acceptance criteria (use the *Task* form).
2. **Branch** from an up-to-date `main`: `<type>/issue-<n>-<slug>`.
3. **Commit** in small Conventional-Commit steps that reference the issue. No `Co-Authored-By` or tool-attribution trailers.
4. **Open a draft PR** using the template (sections A–G) with `Closes #n`.
5. **Independent review**, then fixes on the same branch until no Critical or Major findings remain.
6. **Owner merges.** Nobody else merges, and an AI review is not approval.

## Ground rules
- Never modify `data/raw/` or commit corpus text, large artifacts, or secrets (`.gitignore` covers data and artifacts).
- Keep document IDs as strings; use UTF-8, pathlib, and LF line endings (`.gitattributes`).
- Changes to labels, metrics, split policy, exclusions, data sources, major dependencies, or architecture need owner approval first. Research decisions: [`docs/decisions.md`](docs/decisions.md).
- Update the project memory ([`docs/project-memory/`](docs/project-memory/README.md)) in the same PR.

## Environment
Windows, Python 3.14.5:
```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements/cpu.lock.txt
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\python.exe -m ruff check . && .venv\Scripts\python.exe -m mypy && .venv\Scripts\python.exe -m pytest
```
The lock (`requirements/cpu.lock.txt`) pins cpu + dev dependencies and the spaCy model. CI (`.github/workflows/ci.yml`) runs the same checks on Ubuntu and Windows.
