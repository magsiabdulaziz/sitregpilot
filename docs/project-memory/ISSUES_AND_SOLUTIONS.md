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
