# Architecture (v1.0, approved with the method gate 2026-11-05)

The src-layout follows the master prompt §8 unchanged, except for the deltas noted. Nothing below is implemented yet beyond `scripts/phase1_*.py`.

## Data flow

```
data/raw/CORE-corpus/*.tsv.gz  (read-only, sha256-pinned)
  └─ data.ingest  (streaming gzip, split on first 2 tabs, keep raw text; record file,line,id(str),raw_labels,sha256(raw),fingerprint)
      └─ data.validate  (schema/legend check → status: OK | EMPTY_INPUT | UNKNOWN_CODE | MALFORMED)
          └─ data.deduplicate  (exact raw/normalised hashes; MinHash-LSH + exact Jaccard verification → group_id)
              └─ data.splits  (released_split; controlled_split manifests; group-disjointness assertions)
                  → data/manifests/{records,groups,exclusions,splits}/*.parquet + *.sha256
  └─ data.labels  (label schema → analysis_labels per task T1/T2/T3x; cohort manifests)
  └─ preprocessing.text (per-representation views; window=first N words, truncation flag)
      ├─ features.lexical  (sklearn TfidfVectorizer inside Pipeline)
      └─ features.extract → features.morphosyntax/complexity (spaCy; cache keyed by sha256(text_window)+extractor_version+model_version)
                → artifacts/features/<extractor_version>/*.parquet (counts + denominators)
training.fit  (Pipeline: [vectorise|impute+scale|ColumnTransformer] → OneVsRest(LR|LinearSVC))
  └─ training.search (declared grid, dev selection, threshold tuning)
  └─ training.tracking (run manifest: commit, hashes, config, seeds, timings, peak RSS)
      → artifacts/runs/<RUN_ID>/{manifest.json, model.joblib, label_encoder.json, dev_predictions.parquet}
evaluation.* (metrics from saved predictions only; bootstrap; error tables; plots)
inference.predict (single/batch; outputs id, status, raw_scores, score_type, threshold, labels)
```

## Key interfaces (to be frozen at the data gate)

- **Record** (implemented in `data/ingest.py`, PR #14): `doc_id: str`, `split` (the *released* split), `source_file`, `line_no`, `raw_labels: str`, `labels: tuple[str, ...]` (these are the source labels: set semantics, schema order), `unknown_codes`, `text`, `text_sha256`, `n_ws_words`, `status` (MALFORMED > UNKNOWN_CODE > EMPTY_INPUT > OK), `issue`. The normalised fingerprint (`norm_sha256`) is added by deduplication (#6); `analysis_labels` are derived per task, never stored on the Record.
- **Prediction row**: `run_id`, `doc_id`, `task`, `split`, `cohort`, `status`, `scores: list[float]` (schema order), `score_type: {probability, svm_margin, prevalence}`, `threshold(s)`, `pred_labels`, `gold_labels` (evaluation files only; never in inference input).
- **Config**: pydantic v2 models with `extra="forbid"`, plus validators for invalid combinations (e.g. `score_type=svm_margin` with calibration metrics).

## Deltas vs. the master prompt's layout

- `scripts/phase1_corpus_audit.py` and `phase1_template_overlap.py` stay stdlib-only reference audits. The package's `audit` CLI must reproduce their counts (an integration test).
- `requirements/` holds `cpu.in`, `cpu.lock.txt`, `neural.in`. `pyproject.toml` declares optional groups `[neural]` and `[dev]`.
- Storage format: Parquet via pyarrow. Corpus text never goes into `reports/`.

## Licensing plan (to document in LICENSE / data card)

| Asset | Terms |
|---|---|
| Our code | Apache-2.0 (D-12, approved; `LICENSE`) |
| CORE annotations (labels) | CC BY-SA 4.0 (LICENSE.txt), with attribution and share-alike for derived label files |
| CORE web text | **no license grant found**, so it is not redistributed; retrieval instructions plus hashes only |
| Primary article | CC BY 4.0 (cited, not redistributed) |
| Trained models | not published by default. Derived from unlicensed text and SA annotations, so this needs review before release. |
