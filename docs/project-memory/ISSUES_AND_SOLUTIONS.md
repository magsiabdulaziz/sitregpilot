# Issues and solutions

## ISS-001: Complementary study not retrievable
- **Symptom:** WebFetch of `link.springer.com/article/10.1007/s10579-020-09519-z` → 303 redirect to `idp.springer.com/authorize` (login).
- **Component:** source ledger. **Root cause:** confirmed: the publisher site requires a cookie/auth flow for automated clients.
- **Workaround:** cite only the claims reported in the primary article (ledger §D, D1). **Resolution:** pending a user-supplied PDF (TASK-007).

## ISS-002: `rea` MCP server fails to connect
- **Symptom:** `claude mcp list` → `rea … ✘ Failed to connect — MCP server "rea" connection timed out after 30000ms`.
- **Root cause:** UNVERIFIED (hypothesis: the `npx -y` start-up exceeds the 30 s timeout).
- **Resolution:** not pursued. REA is irrelevant to this project (D-01) and the owner chose to keep the registration.

## ISS-003: Audit combination count differed from the prior audit (460 vs 455)
- **Root cause:** confirmed: 460 distinct raw label strings, 455 distinct sets; 5 sets appear in two orders (e.g. `NA DP NE` / `NA NE DP`).
- **Resolution:** treat labels as sets; report both numbers. Evidence: audit re-run on 2026-11-05.

## ISS-004: pip warnings during install
- **Symptom:** "Cache entry deserialization failed" and a `ReadTimeoutError` on files.pythonhosted.org (preshed wheel metadata).
- **Resolution:** pip's automatic retry succeeded; the install completed and imports were verified. Watch for this if a clean-environment install is flaky in CI (retries/timeouts).

## ISS-005: Transient "auto mode classifier gave no verdict" on Write
- **Symptom:** two Write calls refused with no verdict. **Resolution:** an identical retry succeeded. No action needed.

## ISS-006: GitHub tooling appeared absent
- **Symptom:** `gh: command not found` in Git Bash; no git remote; no `user.name`/`user.email`.
- **Root cause:** confirmed: `gh` 2.103.3 was already installed at `C:\Program Files\GitHub CLI\gh.exe` and authenticated (keyring), but not on the Git Bash PATH.
- **Resolution:** call it by full path (or restart the shell). Identity set repo-locally; remote `origin` added.

## ISS-007: Unwanted co-author trailer on the bootstrap commit
- **Symptom:** commit `ac52d41` (pushed) contained `Co-Authored-By: Claude Opus 5.5`.
- **Root cause:** confirmed: the default assistant attribution was applied before the owner's sole-author rule existed.
- **Resolution:** the owner authorised a rewrite. `git commit --amend` + `git push --force-with-lease` → `dac13cb`; local and remote HEAD verified equal. Rule added to CLAUDE.md (DEC-004).

## ISS-008: Mixed CRLF/LF line endings and OS-dependent output hashes
- **Symptom:** the reviewer found that files edited via Python `write_text` on Windows had become CRLF; audit JSON hashes would differ on Linux/CI.
- **Root cause:** confirmed: Python text-mode writes translate `\n` → `\r\n` on Windows; no `.gitattributes`.
- **Resolution:** normalised to LF; `.gitattributes` with `eol=lf`; scripts write with `newline="\n"`. When editing files programmatically, use `write_bytes` or `newline="\n"`.
- **Verification:** 0 CR bytes in tracked files; re-run hashes identical (DEVELOPMENT_LOG 2026-11-05).

## ISS-009: Repository visibility changed from private to public
- **Symptom:** `gh api repos/magsiabdulaziz/sitregpilot` returned `"visibility":"public"` on 2026-11-05 during PR #13 review. At creation it was private (owner's choice; `gh repo view` showed `PRIVATE`).
- **Root cause:** UNKNOWN. No agent command changed visibility (none of the session's `gh` calls touch it). Presumably an owner action in the GitHub UI: UNVERIFIED.
- **Exposure:** code, docs, audit JSON (CORE doc IDs and labels; CC BY-SA 4.0 annotations), no corpus text.
- **Resolution:** the owner confirmed on 2026-11-05: **the repository stays public**. Agents do not change visibility.

## ISS-010: spaCy multiprocessing from a stdin script fails on Windows
- **Symptom:** `nlp.pipe(..., n_process=3)` from `python -` → `OSError: [Errno 22] Invalid argument: 'D:\SitRegPilot\<stdin>'` in spawned workers; the parent hung.
- **Root cause:** confirmed: Windows `spawn` re-imports the main module from a file path.
- **Resolution:** run multiprocessing code from a real file with an `if __name__ == "__main__":` guard (`scripts/profile_spacy.py`, `core_register.cli`).

## ISS-011: Torn final cache line swallowed the next row
- **Symptom:** after an interrupted write, the next appended row joined the torn line and became unparseable (found by `test_cache_is_resumable_and_tolerates_a_torn_line`).
- **Resolution:** before appending, `extract_to_cache` writes a newline if the file does not end in one. Test passes.
