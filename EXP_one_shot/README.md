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

## v_2_2 changes (current — `oneshot_analysis_v_2_2.py`)

Built on the `v_2_x` role-based series (not the `v29` line). Adds **rare-mean
companion panels** alongside the existing rare-min/rare-max panels — originals are
left untouched.

The two true-rare items (true count = 1) were previously split into `rare_min` and
`rare_max` (min/max of the two estimates). That split is an **order statistic**: across
participants `E[rare_max] > E[rare_min]` purely by construction, which made the Icon-phase
`rare_max` bar look misleadingly high. The companion panels collapse the two rare items
into a single `rare_mean` slot (3 role slots: Rare-mean / Medium / Dominant), removing the
artifact.

New panels:

| Figure | New panel | Mirrors | Position |
|--------|-----------|---------|----------|
| 2 (now 3×3) | 2.4m Blind vs Icon Prior (rare-mean) | 2.4 | `[2,0]` |
| 2 | 2.5m Prior Shift (rare-mean) | 2.5 | `[2,1]` |
| 3 (4×3) | 3.3m Mean Response by Phase (rare-mean) | 3.3 | `[3,1]` |
| 4 (now 4×3) | 4.1m Final Estimates vs True (rare-mean) | 4.1 | `[3,0]` |
| 4 | 4.2m Role Error by Phase (rare-mean) | 4.2 | `[3,1]` |
| 4 | 4.7m Estimation Bias (rare-mean) | 4.7 | `[3,2]` |

Panel 4.3 already aggregates the two rare items into one bar, so it has no companion.
A new blind-phase column `sorted_est_rare_mean = mean(pos1, pos2)` provides the collapsed
rare slot for the shape-aligned blind phase.

Run with `_run_v2_2_smoke.py` (uses `./sample_data`, subjects 101 + 218).

## v29 changes (`oneshot_analysis_v29.py`)

- Saved subfigures no longer cropped: each panel gets a clean white margin of
  6.5% of its width (each side) and 5% of its height (top/bottom).
- Panel 1.3 (heatmap): the 0-12 estimate-scale colorbar is now merged into the
  saved subfigure instead of being written as a separate file. Twin/secondary
  axes (e.g. Panel 4.6 KS line) are merged into their parent panel too.

## v27 changes

- Added Icon vs T2 comparison (`Q_icon_t2`): paired permutation + Wilcoxon +
  Cliff's delta. Tests learning from two exposures relative to the icon prior.
- Panel 3.2b: Icon vs T2 paired dot plot (mirrors the 3.2 layout).
- Panel 7.9 (Improvement by Feedback Band): Jonckheere-Terpstra trend test across
  the ordered feedback bands + continuous Spearman rho (T1 SAD vs improvement).
  Both flagged exploratory (regression-to-the-mean caveat).
