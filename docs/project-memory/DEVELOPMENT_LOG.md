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

## 2026-11-05: PR #10 review round 2 and line-ending fix
- Round 2 (same independent reviewer, delta only): all 12 round-1 findings resolved (CLAUDE.md line 3 left for the owner, non-blocking). Ready for approval, with 2 new Minor findings: N1 CRLF/LF mixing, N2 JSON written with CRLF on Windows.
- Fixed in this PR: 17 tracked files normalised to LF; `.gitattributes` (`* text=auto eol=lf`, binaries marked); both scripts write JSON with `newline="\n"`.
- Verified: two fresh runs plus the committed files are byte-identical. **Current reference hashes:** `corpus_audit.json` d4bf57b7…bec8, `template_overlap_indicator.json` 660f9365…95fb (they supersede earlier Windows-CRLF hashes; content unchanged). 0 CR bytes in tracked files.

## 2026-11-05: PR #10 merged; issue #2 started
- Round-3 check of `ec6645c`: Ready for approval. PR marked ready; Approval Report posted.
- The owner said "merge #10". The owner merged it on GitHub (merge commit `6fba587`); the agent's squash attempt found it already merged. Verified: merged tree == approved head tree; issue #1 closed; local `main` fast-forwarded.
- Started issue #2 on `docs/issue-2-workflow`: `docs/DEVELOPMENT_WORKFLOW.md`, `CONTRIBUTING.md`, `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/{task,bug,config}.yml`, `README.md`; DEC-005.

## 2026-11-05: PR #12 review and revision
- Independent read-only review of `e3b7d9e`: Ready for approval; 0 Critical, 0 Major, 4 Minor, 3 Suggestions.
- Fixed: force-push/history-rewrite rule now covers all branches; merge command includes `--squash`; SESSION_HANDOFF DEC range; DEC-005 set to Proposed (accepted on merge of #12) with an amendment note on DEC-003; master-prompt reference clarified; PR template gains an owner-approval checkbox; #10 merge attribution and timezone labelled; owner-created issue #11 linked to TASK-007.

## 2026-11-05: PR #12 merged; issue #3 started
- The owner's account merged PR #12 (`f953420`) at the reviewed head `9910af8`, before the agent's Approval Report was posted. Issue #2 closed; DEC-005 accepted.
- Started #3 on `chore/issue-3-ci`: pyproject (setuptools, src layout, ruff/mypy/pytest config), `requirements/cpu.lock.txt` (pip freeze incl. dev tools and en_core_web_sm), package stub, 5 corpus-free unit tests, CI workflow (lint-type; test on ubuntu + windows; pip-audit on ubuntu).
- Verified locally: ruff clean (style rules E501/E741 waived only for the frozen `scripts/phase1_*`), mypy strict clean, pytest 5 passed; the lock installs into a fresh Windows venv and tests pass there; pip-audit: no known vulnerabilities (en_core_web_sm is not auditable, since it is not on PyPI).

## 2026-11-05: PR #13 review round 1 and revision
- CI run 41909923088 at `1bcc8f1`: lint-type, test (ubuntu), test (windows) all passed; pip-audit step: no known vulnerabilities.
- Independent read-only review: Changes required (Major: protection result not recorded). Revision: test fixes, setuptools>=77, CI hardening (SHA-pinned checkout/setup-python v7, persist-credentials false, lock-based lint, `pip check`, separate pip-audit job + weekly schedule), memory updates, DEC-006 (proposed).
- Observed: repo visibility is now public (ISS-009), not changed by agents.
- Branch protection on `main` applied and verified via API (DEC-006 result); CI run 41911110569 at `df05442` green incl. pip-audit.

## 2026-11-05: PR #13 merged (M0 complete); issue #5 started
- The owner said "merge #13". Agent squash-merged with `--match-head-commit c21d223` → `9f54304`; tree verified; issue #3 closed. DEC-006 accepted. The owner confirmed public visibility (ISS-009 resolved).
- #5 on `feature/issue-5-ingest-validate`: `config.py` (pydantic, extra=forbid, hash-pinning validation), `data/labels.py` (schema loader, set-semantics parsing), `data/validate.py` (sha256 before read), `data/ingest.py` (binary gzip, split on LF only, statuses OK/EMPTY_INPUT/UNKNOWN_CODE/MALFORMED), `data/audit.py`, `cli.py audit`, `configs/data/core.yaml` (incl. legend hash).
- Verified locally: ruff clean; mypy strict (8 files) clean; 19 unit tests pass; 5 corpus integration tests pass (counts equal the reference audit); CLI audit ~11 s; raw `.gz` hashes unchanged.

## 2026-11-05: PR #14 review round 1 and revision
- Draft PR #14 opened; CI run 41913381331 green. Independent read-only review: Ready for approval (0 Critical, 0 Major, 4 Minor, 4 Suggestions).
- Revision: empty-ID MALFORMED, whitespace-only EMPTY_INPUT (DEC-007, proposed), config combination checks (StrictBool, distinct files, no stray hashes), per-split audit code counts and label sets, stronger integration test, bare-CR and truncation fixtures, architecture Record contract aligned. Local: ruff, mypy clean; 31 tests pass incl. corpus integration.

## 2026-11-05: PR #14 merged; owner standing instructions; issue #6 started
- The owner said "merge #14"; agent squash-merged at `c371c47` → `7848760` (tree verified; #5 closed; DEC-007 accepted).
- **Owner instructions (verbatim):** "merge all future approved by me do not ask again" and, later, "do not ask for future start all allowed by me". Applied by the agent this session as: merge without asking only when the final independent review is Ready with no open Critical/Major findings, the required CI is green at that head, the merge uses `--match-head-commit`, and the PR changes no item that CLAUDE.md reserves for owner approval (labels, metrics, splits, exclusions, data sources, major dependencies, architecture, protocol decisions); start the next eligible issue without asking. `/CLAUDE.md` and `docs/DEVELOPMENT_WORKFLOW.md` §9 are **unchanged** (they still require explicit per-PR approval). Making the rule permanent was offered to the owner as a separate docs PR, with no answer yet. The harness blocked an edit that would have recorded the rule in the auto-memory index.
- Started #6 on `feature/issue-6-dedup`: `configs/data/dedup.yaml` (D-07 values frozen first), `DedupConfig`, `data/deduplicate.py`, `dedup` CLI, unit and corpus integration tests.

## 2026-11-05: #6 and #4 merged; #7 implemented
- PR #15 (dedup): corpus run 208 s; 12 exact + 19 near groups (31), 14 cross-split, 10 label conflicts; largest LSH bucket 8; manifest sha cd185863…. Merged `cddfe58` after the owner said "merge #15".
- PR #16 (H-001 recount, two parts): every methodology §2 number confirmed; §2 BOM wording corrected. Merged `38c9945` after the owner said "merge #16". The earlier auto-merge attempt was blocked by the harness classifier, so explicit per-PR approval remains required in practice.
- #7 on `feature/issue-7-splits`: `configs/data/splits.yaml`, `SplitConfig`, `data/splits.py`, `split` CLI. Corpus run 42 s. Assertions pass (rows accounted, group-disjoint, nothing moved). Controlled: train 33,870 / dev 4,843 / test 9,686; 53 excluded (17 empty, 14 cross-split, 10 train label-conflict, 12 within-train duplicates). Template-seen (controlled): dev 341/4,843, test 706/9,686. Sealed test-ID sha256: released 5b0f08d9…, controlled cc33a023….

## 2026-11-05: PR #17 merged; issue #8 started
- The owner confirmed "quarantine all" for train label-conflict groups (recorded as D-14), then said "merge #17" while the independent review was still running. Merged `c6eab9b` at `cf5469a` (tree verified, CI green, #7 closed); a PR comment records that the review was incomplete.
- Post-merge review: Ready. Independent recomputation matched all 48,452 manifest rows, all 56 per-label tables, the template flags and both sealed hashes. Minor findings (untested CLI refusal paths; stale memory) and suggestions (n/a bucket split; 60-word minimum in §5.3) are addressed on `test/issue-8-gate-c`. Formatting (`ruff format`) not adopted: CI does not enforce it.
- #8: 4 provenance tests (tampered dedup manifest, mismatched sources, failed assertion → no output); report-only n/a split; sealed manifest unchanged (sha verified).

## 2026-11-05: PR #18 merged; gate C approved; Phase 3 started (#19)
- The owner said "merge #18 and approve gate C". Merged `bb63f2a` at `f5845a0` (tree verified; #8 closed). M1 complete.
- Opened #19 (feature registry and extraction) and #20 (CPU baselines B0–B4).
- #19 profiling on 300 controlled-train docs (`reports/profiling/spacy_profile.json`): full pipeline 11.2 docs/s; NER disabled 13.9 docs/s (1 process, ~0.6 GB) or 14.6 docs/s (3 processes, ~1.0 GB). Chosen: NER disabled, 1 process (≈1 h for 48,435 windows). Windows multiprocessing needs a `__main__` guard (stdin scripts fail: ISS-010).
- Registry v1.0.0: 41 features in 8 families; counts and denominators stored; missing ≠ 0. 10 linguistic fixture tests. The cache-resume test found a torn-line bug (a row appended after an interrupted write was lost); fixed.

## 2026-11-05: #19 extraction v1.0.0 and review round 1
- v1.0.0 extraction: 48,435 parsed in 3,180 s, 0 failures. MATTR-500 missing in 38.7% of train and 37.3% of dev (flagged to the owner).
- PR #21 review round 1: Changes required. Majors: relative 'that'/'which' counted as demonstrative pronouns (41% of PRON demonstratives in a train sample were WDT); the §4 linguistic normalisation (NFC, control characters) was not applied; §6 items missing (SD of sentence length, possessive determiners, passive definition, nominalisation exclusion list, 60-doc inspection sample). Minors: '?' before a closing quote missed; hard-coded failure count; 'mine' (ADJ) missed; memory not updated.
- Fixes (registry 1.1.0, extractor 1.1.0): DT-tag requirement for demonstratives; NFC plus C0 control-character replacement with per-document counts; `sd_sent_len` (from n_sent_len_sq), `poss_det` (PRP$); passive = VBN heads with an auxpass/nsubjpass dependent; nominalisation exclusion list; closing-punctuation skip for questions; possessive pronouns tagged ADJ; curly 'll/'d; cache key now includes the spaCy version and disabled pipes; measured failure count; 60-doc train-only inspection sample (pending human review). 76 tests pass. Re-extraction running.

## 2026-11-05: #19 completion recorded (fixes the stale notes flagged in the #21 review); PR #21 merged
- v1.1.0 extraction finished: 48,435 parsed in 3,221 s, 0 failures, cache sha f7e7bb99…; 78 tests passed. Review round 2 Ready. The owner said "merge #21" → `6318d93` (tree verified; #19 closed).

## 2026-11-05: #20 CPU baselines B0–B4 (dev only)
- Run failures: (1) ISS-012 read-only memmap with liblinear; (2) silent exit 5 (probably native); (3) ISS-013 access violation in threaded fits after 12/48 settings. Fixed by sequential fits (`n_jobs: 1`); threaded results were also not reproducible. All failed runs carry FAILED.json.
- B0–B2 run `20261105T084605-5bb8e61` (clean commit): 48 settings, 1,595 s, peak 1.97 GB. Dev macro-F1: B1 LogReg 0.610 (200k, 1–2-grams, C 10, balanced), B2 SVM 0.605 (200k, 1–2-grams, C 1); B0 most-frequent set 0.077.
- B3/B4 run `20261105T091306-c9d153b` (clean commit): 5,514 s, peak 2.45 GB. B3 linguistic 0.479 (C 0.1); B4 combined 0.613 (α 0.5; α 0.5/1/2 give 0.6131/0.6131/0.6130; α = 2 took 55 min with no convergence warning).
- `reports/baselines/T1_dev_summary.md` is generated from the JSON reports. All dev numbers are optimistic (thresholds and selection both on dev). The test set was not touched.
- Observations for the owner: the B1/B2 optimum is at the edge of the D-09 grid (largest vocabulary); B3's strongest SP predictor is the MATTR missing indicator (a document-length signal).

## 2026-11-05: PR #22 merged; Phase 3b decisions
- The owner said "merge #22" → `f8c6ace` at `39385d3` (tree verified; #20 closed). Phase 3 baselines complete (dev only).
- Owner decisions: Phase 3b analyses (a), (b), (c) approved with explicit reporting caveats (D-15); D-09 amended with one 400k vocabulary candidate after a training-only pilot, stop rules declared in advance (D-16); Phase 4 deferred, GPU plan only (D-17); evaluation controls recorded with D-15–D-17.
- Opened #23–#26. Started #23 (decision records, `docs/phase4_gpu_plan.md`, experiment-plan status).

## 2026-11-05: PR #27 merged; D-16 pilot; work stopped
- PR #27 review round 1: Changes required (D-16 thresholds had been presented as owner-approved; setting count unclear). Fixed: thresholds labelled as the implementer's proposal, pending owner confirmation; 24 new settings (12 per model). Round 2 Ready. The owner said "merge #27" → `e2c0d74` (tree verified; #23 closed).
- A network outage (DNS failure for github.com) briefly blocked a push; retried successfully.
- A Claude Code restart occurred mid-session; the reviewer agent and pilot resumed.
- D-16 training-only pilot (`scripts/vocab_pilot.py`, commit `81a15a6`): 400k vs 200k: vectoriser fit 76.2 s vs 71.4 s (ratio 1.07), peak 1.86 GB vs 1.67 GB. The proposed rules say continue; **thresholds not yet confirmed**, so the 24 settings were not run.
- The owner asked to update memory and stop. The branch `feature/issue-24-vocab` was pushed without a PR. No processes left running.
