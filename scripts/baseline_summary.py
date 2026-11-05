"""Render reports/baselines/T1_dev_summary.md from the committed B0-B2 and B3/B4 dev reports.

Every number is read from the JSON reports (themselves produced from saved run artifacts); nothing is typed by hand.
DEV results only: thresholds and model selection both use dev, so these scores are optimistic. Test is sealed.

Usage: .venv\\Scripts\\python.exe scripts/baseline_summary.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LEX = Path("reports/baselines/T1_dev_lexical.json")
LING = Path("reports/baselines/T1_dev_linguistic.json")
OUT = Path("reports/baselines/T1_dev_summary.md")
LABELS = ["SP", "LY", "IN", "IP", "OP", "NA", "HI", "ID"]


def row(name: str, rep: dict[str, Any], note: str = "") -> str:
    ap = rep.get("macro_ap")
    ap_s = "—" if ap is None else f"{ap:.3f}"
    return (f"| {name} | {rep['macro_f1']:.3f} | {rep['micro_f1']:.3f} | {rep['weighted_f1']:.3f} | "
            f"{rep['samples_f1']:.3f} | {rep['exact_set_accuracy']:.3f} | {ap_s} | {note} |")


def main() -> None:
    lex = json.loads(LEX.read_text(encoding="utf-8"))
    ling = json.loads(LING.read_text(encoding="utf-8")) if LING.is_file() else None
    models: list[tuple[str, dict[str, Any], str]] = [
        ("B0 prevalence (scores; 0.5 cut)", lex["B0"]["B0_prevalence_scores"], "AP reference"),
        ("B0 most-frequent label set", lex["B0"]["B0_most_frequent_set"], ""),
        ("B0 all-negative", lex["B0"]["B0_all_negative"], "diagnostic"),
    ]
    sel = dict(lex["selected"])
    if ling:
        sel.update(ling["selected"])
    names = {"logreg": "B1 word TF-IDF + LogReg", "svm": "B2 word TF-IDF + LinearSVC (margins)",
             "B3_linguistic_logreg": "B3 linguistic features + LogReg",
             "B4_combined_logreg": "B4 TF-IDF ⊕ α·linguistic + LogReg"}
    for key, label in names.items():
        if key in sel:
            models.append((label, sel[key]["dev_tuned"], json.dumps(sel[key]["params"], separators=(",", ":"))))
    lines = [
        "# T1 dev results: CPU baselines B0–B4",
        "",
        "**DEV ONLY.** Thresholds (global, then per-label shrunk 50%) and model selection both use the dev set,",
        "so these numbers are **optimistic** and are *not* the study's result. The controlled test set stays",
        "sealed until Phase 5.",
        "Task T1: 8 main registers, multilabel; functional cohort; controlled split. "
        f"Train n = {lex['run']['n_train']:,}, dev n = {lex['run']['n_dev']:,}.",
        "Conventions: zero_division = 0; samples-F1 counts empty-vs-empty as 1; AP = step-wise average precision.",
        "",
        "| Model | macro-F1 | micro-F1 | weighted-F1 | samples-F1 | exact set | macro-AP | selected settings |",
        "|---|---|---|---|---|---|---|---|",
        *[row(n, r, note) for n, r, note in models],
        "",
        "## Per-register F1 (dev, tuned thresholds)",
        "",
        "| Model | " + " | ".join(LABELS) + " |",
        "|---|" + "---|" * len(LABELS),
    ]
    for label, rep, _ in models[3:]:
        lines.append(f"| {label} | " + " | ".join(f"{rep['per_label'][lab]['f1']:.3f}" for lab in LABELS) + " |")
    lines.append("| *dev support* | " + " | ".join(str(models[3][1]["per_label"][lab]["support"]) for lab in LABELS)
                 + " |")
    lines += ["", "## Effect of threshold tuning (macro-F1, dev)", "",
              "| Model | default threshold | tuned |", "|---|---|---|"]
    for key, label in names.items():
        if key in sel:
            lines.append(f"| {label} | {sel[key]['dev_default_threshold']['macro_f1']:.3f} | "
                         f"{sel[key]['dev_tuned']['macro_f1']:.3f} |")
    lines += ["", "Default threshold = 0.5 for probabilities and 0.0 for SVM margins."]
    if ling and "B3_coefficients" in ling:
        lines += ["", "## B3: strongest linguistic associations per register (dev-selected model, fitted on train)", "",
                  "Logistic-regression weights on robust-scaled features (`missingindicator_*` = feature was missing).",
                  "These are **predictive associations given the other features**, not functional definitions of a",
                  "register. Correlated features share or trade weight; signs can flip under collinearity.", "",
                  "| Register | strongest positive | strongest negative |", "|---|---|---|"]
        for lab in LABELS:
            co = ling["B3_coefficients"][lab]
            ranked = sorted(co.items(), key=lambda kv: kv[1])
            neg = ", ".join(f"`{k}` {v:+.2f}" for k, v in ranked[:3])
            pos = ", ".join(f"`{k}` {v:+.2f}" for k, v in reversed(ranked[-3:]))
            lines.append(f"| {lab} | {pos} | {neg} |")
    lines += ["",
              "## Provenance", "",
              f"- B0–B2 run `{lex['run']['run_id']}` (commit `{lex['run']['git']['commit'][:7]}`, dirty "
              f"{lex['run']['git']['dirty']}), {lex['run']['timing']['seconds']} s, peak "
              f"{lex['run']['timing']['peak_rss_mb']} MB."]
    if ling:
        run = ling["run"]
        lines.append(f"- B3/B4 run `{run['run_id']}` (commit `{run['git']['commit'][:7]}`, dirty "
                     f"{run['git']['dirty']}), {run['timing']['seconds']} s, peak {run['timing']['peak_rss_mb']} MB; "
                     f"feature cache `{run['feature_cache']['sha256'][:12]}…`.")
    lines += ["- Model files and dev predictions: paths and sha256 in the JSON reports "
              "(git-ignored `artifacts/runs/`).",
              "- Save/load parity verified for every selected model.", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
