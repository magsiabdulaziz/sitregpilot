# SitRegPilot

An explainable, reproducible classifier for **English web registers** built on the Corpus of Online Registers of English (CORE), as released by Laippala et al. (2023, *Language Resources and Evaluation* 57:1045–1079, https://doi.org/10.1007/s10579-022-09624-1). It is PhD research software that compares lexical, grammatical, and combined representations, runs CPU-first, and works on Windows.

**Status:** Phase 0/1 complete (audit and approved protocol). Phase 2 (data contracts) is next. No classifier exists yet and no results are reported.

| Start here | |
|---|---|
| Research protocol | [`docs/methodology.md`](docs/methodology.md), [`docs/decisions.md`](docs/decisions.md) |
| Sources and evidence | [`docs/source_ledger.md`](docs/source_ledger.md), [`docs/compatibility.md`](docs/compatibility.md) |
| How to contribute | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/DEVELOPMENT_WORKFLOW.md`](docs/DEVELOPMENT_WORKFLOW.md) |
| Current state | [`docs/project-memory/PROJECT_STATE.md`](docs/project-memory/PROJECT_STATE.md) |

## Data
The corpus is not included. Clone https://github.com/TurkuNLP/CORE-corpus (commit `b57dbdb5ebee4b2688fa94889a2cbdb341d86ee7`) into `data/raw/CORE-corpus`. Expected SHA-256 hashes are in `reports/audit/corpus_audit.json` (`file_sha256`).

## Command line
Run from the repository root (after installing per [`CONTRIBUTING.md`](CONTRIBUTING.md)):
```
.venv\Scripts\python.exe -m core_register.cli audit --config configs/data/core.yaml [--out PATH]
```
`audit` verifies the pinned SHA-256 of every source file before reading, streams the corpus, and prints counts only (no text). It exits with code 2 if a hash does not match. Rows get a status: `OK`, `EMPTY_INPUT`, `UNKNOWN_CODE` or `MALFORMED`.

```
.venv\Scripts\python.exe -m core_register.cli dedup --config configs/data/core.yaml --dedup-config configs/data/dedup.yaml
```
`dedup` groups exact and verified near-duplicate documents using the frozen D-07 policy in `configs/data/dedup.yaml`. It writes a committed report (`reports/dedup/dedup_report.json`: counts, IDs and Jaccard values, no text) and a git-ignored group manifest (`artifacts/dedup/groups.csv`), whose SHA-256 the report records. It takes about 3.5 minutes on a 4-core laptop.

## Licensing
Code: Apache-2.0 ([`LICENSE`](LICENSE)). CORE annotations: CC BY-SA 4.0 (per the corpus repository). CORE web text carries no stated licence and is not redistributed here. Please cite Laippala et al. (2023) and the CORE compilation works listed in the corpus README.
