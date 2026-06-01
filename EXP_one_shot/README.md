# EXP_one_shot

Analysis pipeline for the **OneShot** distributional-learning experiment.

Participants estimate a hidden frequency distribution `[1, 1, 4, 6]` across four
items (12 items total) over four phases:

`Blind Prior → Icon Prior → Trial 1 (exposure + feedback) → Trial 2`

The primary dependent variable is **SAD** (Sum of Absolute Deviations from the
true distribution; range 0 = perfect to 22 = worst).

## Files

| File | Purpose |
|------|---------|
| `oneshot_analysis_v27.py` | Main analysis script. `run_analysis(source, output_dir, ...)` runs the full pipeline and returns `df, summary_df, results, figures`, writing figures, an email-style report, a markdown report, a PDF, and a results CSV. |
| `_run_v27_smoke.py` | Quick end-to-end smoke test. |
| `sample_data/` | One sample subject CSV for smoke testing. |

## Key analyses

- **Q5 (primary)** — Blind → T2 total learning (paired permutation, Wilcoxon, Cliff's delta).
- **Q_icon_t2** — Icon → T2 exposure learning: tests learning from the two
  exposures relative to the icon prior (paired permutation two-sided, Wilcoxon,
  Cliff's delta, direction counts). Rendered as **Panel 3.2b** in Figure 3,
  mirroring the Panel 3.2 layout.
- **q_blind_t1** — Blind → T1 combined icon + first-exposure effect.
- Prior classification, Friedman omnibus, item-level and feedback analyses.

## Requirements

```
python >= 3.8
pandas
numpy
matplotlib
scipy
```

## Running

```bash
# Uses ./sample_data by default
python _run_v27_smoke.py

# Or point at your own data (directory or glob)
python _run_v27_smoke.py /path/to/Subjects
ONESHOT_DATA="/path/to/oneshot_subject_*.csv" python _run_v27_smoke.py
```

> Note: paired statistics require at least two valid subjects; running against a
> single subject will report "Insufficient data" for those comparisons.

## v27 changes

- Added Icon vs T2 comparison (`Q_icon_t2`): paired permutation + Wilcoxon +
  Cliff's delta. Tests learning from two exposures relative to the icon prior.
- Panel 3.2b: Icon vs T2 paired dot plot (mirrors the 3.2 layout).
- Panel 7.9 (Improvement by Feedback Band): per-band Wilcoxon signed-rank test
  vs 0 (significance star per bar) + continuous Spearman rho (T1 SAD vs
  improvement). Both flagged exploratory (regression-to-the-mean caveat).
