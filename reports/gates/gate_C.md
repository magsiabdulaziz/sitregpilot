# Gate C: data contracts (Phase 2)

**Status:** all criteria passed, with evidence below. **Approved by the owner on 2026-11-05** ("approve gate C"; PR #18 merged as `bb63f2a`).
Evidence generated 2026-11-05 on branch `test/issue-8-gate-c` (base `main` = `c6eab9b`), Windows, Python 3.14.5.

Gate C (master prompt §16): *hashes stable; all input rows accounted for; no group overlap in the controlled protocol; anomaly decisions logged.*

## Checklist

| # | Criterion | Result | Evidence |
|---|---|---|---|
| C1 | Source hashes stable | **PASS** | Recomputed sha256 = pinned values in `configs/data/core.yaml` and `reports/audit/corpus_audit.json`: train `6715944d…5b3`, dev `2a57492f…d95`, test `8fb92b68…ec5`, legend `33caf0a3…d1d`. Corpus clone at `b57dbdb5ebee4b2688fa94889a2cbdb341d86ee7` with a clean working tree. Every CLI command (`audit`, `dedup`, `split`) verifies these hashes before reading (tests: `test_hash_mismatch_is_refused_and_file_left_untouched`, `test_cli_writes_json_and_fails_on_hash_mismatch`). |
| C2 | All input rows accounted for | **PASS** | 48,452 physical lines → 48,452 records. Status counts sum to lines in every split (`test_split_counts_match_reference`). The split manifest has 48,452 unique 7-digit string IDs (`test_every_released_row_present_once`). Each row is kept in its released partition or excluded with a reason (table below). |
| C3 | No group overlap in `controlled_split` | **PASS** | `controlled_group_disjoint: true`, 0 violations; `no_record_moved_between_partitions: true` (`reports/splits/split_report.json`). Re-checked from the committed manifest in CI (`test_controlled_partitions_are_group_disjoint_and_never_moved`). Independently recomputed by the PR #17 reviewer: 0 mismatches on 48,452 rows. |
| C4 | Anomaly decisions logged | **PASS** | Row statuses: DEC-007. Duplicate policy: D-07 (`configs/data/dedup.yaml`). Split policy: D-07, plus D-14 (train label-conflict groups quarantined entirely, owner-confirmed). OTHER policy: D-04. Hierarchy (no closure; DP-without-IN kept): D-03. Empty texts: excluded and listed. U+FEFF mid-text (2 rows) and control characters documented in methodology §2. |
| C5 | Test set sealed before any fitting | **PASS** | `data/manifests/splits/split_manifest.csv` committed, sha256 `99246b79b0c743fc36924682d524af8ced7c7a23a06ed4706b4d439b4ad9c28b`. Sealed ID hashes: released test 9,692 IDs `5b0f08d9…7c19`; controlled test 9,686 IDs `cc33a023…b126`. Verified in CI (`test_sealed_test_hashes_recompute`) and rebuilt byte for byte from the corpus (`test_rebuild_reproduces_sealed_manifest`). No model has been fitted. |
| C6 | Provenance chain enforced | **PASS** | `split` refuses a dedup manifest whose hash differs from the dedup report, or a dedup report built from other sources (exit 2), and writes nothing if an assertion fails (exit 3). Tests in `tests/unit/test_cli_provenance.py`. Chain: sources → `reports/dedup/dedup_report.json` (sha `41a5276f…0fad`) → `artifacts/dedup/groups.csv` (sha `cd185863…3673`) → split manifest. |
| C7 | Data-contract tests (#8 list) | **PASS** | leading-zero ID round-trip (`test_leading_zero_id_stays_a_string`, manifest 7-digit check); malformed rows and unknown codes (`test_statuses_ok_empty_unknown_malformed`); empty input (`test_empty_id_is_malformed_and_whitespace_only_text_is_empty_input`); label order variants (`test_label_order_variants_parse_to_same_set_in_schema_order`); duplicate conflicts (`test_within_train_keeps_lowest_id_and_quarantines_conflicts`, `test_dev_and_test_duplicates_are_all_kept_and_share_a_group`); cross-split group overlap (`test_priority_test_over_dev_over_train`); manifest repeatability (`test_manifest_has_no_text_or_labels_and_is_deterministic`, `test_rebuild_reproduces_sealed_manifest`). |

## Full test run

`ruff check .`: all checks passed · `mypy` (strict, 10 files): no issues · `pytest`: **62 passed in 307 s**, including all 8 real-corpus integration tests. CI runs everything except the `requires_corpus` tests (the corpus is never downloaded in CI).

## controlled_split

| | train | dev | test | excluded |
|---|---|---|---|---|
| size | 33,870 | 4,843 | 9,686 | 53 |
| functional cohort (primary, D-04) | 33,463 | 4,785 | 9,569 | — |
| OTHER-only cohort | 407 | 58 | 117 | — |

| Exclusion reason | train | dev | test |
|---|---|---|---|
| empty text (`status_EMPTY_INPUT`) | 10 | 1 | 6 |
| cross-split duplicate (lower priority) | 13 | 1 | 0 |
| train label-conflict group (D-14) | 10 | — | — |
| within-train duplicate (non-representative) | 12 | — | — |

Main-register counts after control (train / dev / test / excluded): SP 513/76/146/4 · LY 475/68/135/3 · IN 8,867/1,272/2,537/15 · IP 1,399/207/402/5 · OP 7,436/1,053/2,129/8 · NA 14,900/2,128/4,264/14 · HI 1,433/203/411/0 · ID 2,410/349/686/9 · OTHER 407/58/117/0. The full 56-code tables are in `reports/splits/split_report.json`.

**Comparability note:** controlled test differs from released test only by its 6 empty texts. Controlled train loses 45 records (0.13%). Results on `released_split` remain reportable but are contaminated (6 exact and 8 further near-duplicate pairs cross splits).

**Template-flag note:** no dev or test document is shorter than 60 normalised words, so the report's `n/a_too_short` bucket is empty, not missing. Every `n/a` is `n/a_excluded`.

## Limitations carried forward
- Duplicate detection is text similarity, not provenance. Boilerplate-only overlap is not grouped (D-07); it is measured by the template-seen flag instead (controlled: dev 341, test 706 documents).
- No source-domain metadata exists, so a domain-held-out evaluation is impossible without an ID→URL mapping.
- The corpus integration tests run only where the corpus exists; CI checks the committed seal instead.

## Sign-off
- [x] Owner approves gate C (2026-11-05), allowing Phase 3 (features and CPU baselines on train/dev only; test stays sealed until Phase 5).
