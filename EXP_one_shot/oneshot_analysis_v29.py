# -*- coding: utf-8 -*-
"""
OneShot Experiment - Comprehensive Analysis (Version 13.0, v29)
==========================================================
Analysis script for the OneShot distributional learning experiment.

EXPERIMENT OVERVIEW:
  - Participants estimate a distribution [1, 1, 4, 6] across 4 items (N=12 total)
  - 4 phases: Blind Prior -> Icon Prior -> Trial 1 (exposure+feedback) -> Trial 2
  - Primary DV: SAD (Sum of Absolute Deviations from true distribution)
  - Secondary DVs: Shannon Entropy, Gini-Simpson diversity index
  - SAD range: 0 (perfect) to 22 (worst), always even for N=12

v29 CHANGES:
  - save_individual_panels(): expanded per-panel margins so saved subfigures are
    no longer cropped - each panel bbox is padded by 6.5% of its width on each
    side and 5% of its height top and bottom (replaces the fixed 0.1in pad).
  - save_individual_panels(): companion axes (colorbars + twin/secondary axes)
    are now merged into their parent panel's saved image instead of being written
    as separate stray PNGs. Fixes Panel 1.3 (heatmap) whose 0-12 estimate scale
    (colorbar) was previously saved as its own file.

v27 CHANGES:
  - Added Icon vs T2 comparison (Q_icon_t2): paired permutation + Wilcoxon +
    Cliff's delta. Tests learning from two exposures relative to icon prior.
  - Panel 3.2b: Icon vs T2 paired dot plot (mirrors 3.2 layout).
  - Panel 7.9 (Improvement by Feedback Band): added a Jonckheere-Terpstra trend
    test across the ordered feedback bands (new jonckheere_terpstra_test() helper:
    JT statistic, normal-approx z, two-sided permutation p) plus the continuous
    Spearman rho (T1 SAD vs improvement) annotation. Both labeled exploratory
    (regression-to-the-mean caveat). Stored in results['feedback']['jt_trend'].

v26 CHANGES:
  - Added Blind vs T1 comparison (q_blind_t1): paired permutation (two-sided) +
    Wilcoxon + Cliff's delta. Tests the combined icon + first-exposure effect
    relative to the uninformed blind prior. Wired into console, ResultsSummary
    CSV, email report, markdown report, and (via markdown) the PDF.
  - Panel 3.1 (SAD Learning Curve): added significance brackets for all pairwise
    comparisons (Blind-Icon, Icon-T1, T1-T2 adjacent; Blind-T1, Blind-T2 span),
    each labeled with stars or n.s. via new add_bracket_labeled() helper. Heights
    staggered; y-limit raised to fit.
  - Added save_figures flag to run_analysis(): when False, figures are created in
    memory but not saved to disk (figure objects still returned). Default: True.
  - Added save_subfigures flag to run_analysis(): when True, each panel/subplot is
    saved as a separate PNG under a subfigures/ subdirectory via
    save_individual_panels(). Independent of save_figures. Default: False.
  - Added Icon vs T2 comparison (Q_icon_t2): paired permutation + Wilcoxon +
    Cliff's delta. Tests learning from two exposures relative to icon prior.
  - Panel 3.2b: Icon vs T2 paired dot plot (mirrors 3.2 layout). Figure 3 expanded
    from 2x3 to 3x3 to accommodate it.
  - Panels 3.2c / 3.2d / 3.2e: paired dot plots for Blind->T1 (q_blind_t1),
    Icon->T1 (q3), and T1->T2 (q4), all mirroring the 3.2 layout via a shared
    helper. Figure 3 expanded from 3x3 to 4x3 to accommodate them.

v24 CHANGES:
  - Added Icon Prior Multinomial Simulation Test (P2a): same test as blind prior
    but on icon phase data. Tests if icon prior is also more uniform than chance.
  - Added Cohen's h effect size for proportion comparisons (P4, P6):
    h = 2*arcsin(sqrt(p1)) - 2*arcsin(sqrt(p2)). Reported for all significant
    per-category classification tests. Ref: Cohen (1988).
  - Cohen's h interpretation: |h| < 0.2 small, 0.2-0.5 small-medium,
    0.5-0.8 medium-large, > 0.8 large.

RESEARCH QUESTIONS:
  Q1: What is the population prior distribution? (+ reference distribution comparison)
  Q2: Does seeing item shapes change the prior? (Blind -> Icon)
  Q3: Does single exposure produce learning? (Icon -> Trial 1)
  Q4: Does repetition improve learning? (Trial 1 -> Trial 2)
  Q5: What is the total learning magnitude? (Blind -> Trial 2)  [PRIMARY]
  Q5b: Does prior quality predict test performance? (Prior-Test correlation)
  Q6: Which items are learned better: dominant or rare?
  Q7: Do self-reported strategies match behavior?

ANALYSIS FLOW (descriptives-first, experiment-chronological):
  1. Load + Preprocess + Validate
  2. Comprehensive Descriptives (Figure 1)
  3. Q1: Prior characterization + 5 reference distribution shape classification
  4. Friedman omnibus test (4-phase trajectory) + Bonferroni post-hoc
  5. Q2-Q5: Pairwise phase comparisons (chronological order)
  5b. Prior-Test correlation (combined Blind+Icon SAD vs T1+T2 SAD)
  6. Q6: Item-specific learning (dominant vs rare)
  7. Timing: RT + Completion + Deliberation decomposition
  8. Q7: Self-report validation (5 questionnaire items, Figure 6)

FIGURE STRUCTURE:
  Figure 1: Descriptive Overview (table + violin + heatmap + diversity)
  Figure 2: Prior Analysis Q1 + Exact Match Rates (4 panels)
  Figure 3: Learning Trajectory Q2-Q5, Q5b (6 panels)
  Figure 4: Item Estimation Q6 (4 panels)
  Figure 5: Timing Analysis (2 panels)
  Figure 6: Self-Report Validation Q7 (6 panels, Hebrew RTL)

STATISTICAL APPROACH:
  - Non-parametric methods: Friedman omnibus, permutation tests, Wilcoxon
  - Effect size: Cliff's delta (Romano et al., 2006), Cohen's h for proportions (Cohen, 1988)
  - Diversity: Shannon Entropy (bits) + Gini-Simpson (probability scale)
  - Confidence intervals: Bootstrap (10,000 resamples)
  - Multiple comparisons: Bonferroni correction for pairwise follow-ups
  - Hebrew RTL: Built-in manual bidi renderer (no external package needed)

USAGE:
  # In Spyder:
  from oneshot_analysis_v11 import run_analysis
  df, summary_df, results, figures = run_analysis(source="data.csv")

  # Command line:
  py oneshot_analysis_v11.py data.csv -o results

Author: Paz Lab, Weizmann Institute
Date: April 2026
Version: 10.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch, FancyBboxPatch
from matplotlib.lines import Line2D
from scipy import stats
from scipy.special import gammaln
from pathlib import Path
from datetime import datetime
import os
import sys
import textwrap
import warnings
warnings.filterwarnings('ignore')

# Hebrew RTL support
try:
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False

# Optional: GUI file dialog
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False


# ============================================================================
# CONFIGURATION - Experiment parameters defining the analysis targets
# ============================================================================

# The distribution participants must learn: [1, 1, 4, 6] out of 12 items.
# Item roles for Q6 (item-specific learning): rare(1), medium(4), dominant(6).
TRUE_DISTRIBUTION = [1, 1, 4, 6]
TRUE_DISTRIBUTION_DICT = {'item1': 1, 'item2': 1, 'item3': 4, 'item4': 6}
UNIFORM_DISTRIBUTION = [3, 3, 3, 3]  # Null hypothesis for Q1 (prior = no info)
N_SIMULATIONS = 1000  # Monte Carlo simulation runs for null distribution tests
TOTAL_ITEMS = 12

# SAD = primary DV for Q1-Q5. Lower = better.
# Uniform SAD = 8 serves as baseline: if learning occurred, T2 SAD < 8.
MAX_SAD = 22
MIN_SAD = 0
UNIFORM_SAD = 8

# Q6 item roles: grouped by true frequency for dominant vs rare comparison
ITEM_ROLES = {1: 'rare', 4: 'medium', 6: 'dominant'}

# Experiment phases in chronological order.
# Q2: Blind->Icon | Q3: Icon->T1 | Q4: T1->T2 | Q5: Blind->T2
PHASE_ORDER = ['blind_prior', 'prior_icon', 'exposure_gen_1', 'exposure_gen_2']
PHASE_LABELS = {
    'blind_prior': 'Blind Prior',     # No shape info, no exposure (Q1 prior)
    'prior_icon': 'Icon Prior',        # See shapes, no distribution info
    'exposure_gen_1': 'Trial 1',       # After 1st exposure + feedback
    'exposure_gen_2': 'Trial 2'        # After 2nd exposure + feedback
}
PHASE_SHORT = {
    'blind_prior': 'Blind',
    'prior_icon': 'Icon',
    'exposure_gen_1': 'T1',
    'exposure_gen_2': 'T2'
}

# Q1 reference distributions: sorted ascending, all sum to 12.
# Used to classify each participant's prior shape (sorted blind response
# compared to each reference via SAD). Sorting removes position identity
# since blind phase uses gray squares with no item identity.
REFERENCE_DISTRIBUTIONS = {
    'Uniform':           [3, 3, 3, 3],  # Flat, no differentiation
    'Unimodal-mild':     [1, 2, 3, 6],  # One moderate peak, graded
    'Unimodal-extreme':  [0, 1, 2, 9],  # One strong peak
    'Bimodal-symmetric': [1, 1, 5, 5],  # Two equal peaks
    'J-shaped (True)':   [1, 1, 4, 6],  # Matches true distribution shape
}

# Colorblind-accessible, print-distinguishable scheme.
# Phase colors: cool->warm->green (temporal progression).
# Role colors: frequency-semantic (rare=alert red, dominant=green).
COLORS = {
    'blind_prior': '#9370DB',
    'prior_icon': '#6495ED',
    'exposure_gen_1': '#FF8C00',
    'exposure_gen_2': '#2E8B57',
    'dominant': '#2E8B57',
    'medium': '#4682B4',
    'rare': '#DC143C',
    'true': '#1E90FF',
    'uniform': '#808080',
    'perfect': '#32CD32',
    'poor': '#DC143C',
    'learning': '#2E8B57',
    'no_learning': '#DC143C',
}
PHASE_COLORS = {phase: COLORS[phase] for phase in PHASE_ORDER}


# ============================================================================
# REPORT LOGGING - Dual output: console + saved text file
# ============================================================================

REPORT_LINES = []

def report(text=""):
    """Print to console and accumulate for text file output."""
    print(text)
    REPORT_LINES.append(text)

def clear_report():
    """Reset for fresh run (called automatically by run_analysis)."""
    global REPORT_LINES
    REPORT_LINES = []


# ============================================================================
# HEBREW RTL UTILITIES - For Figure 3 question text display
# ============================================================================
# Uses python-bidi if available, otherwise falls back to manual reversal.
# Manual reversal handles pure Hebrew and mixed Hebrew+ASCII strings
# by splitting into character-type runs and reversing appropriately.

def _is_hebrew(char):
    """Check if character is in Hebrew Unicode block (U+0590-U+05FF)."""
    return '\u0590' <= char <= '\u05FF'

# Mirrored brackets for RTL display
_MIRROR = {'(': ')', ')': '(', '[': ']', ']': '[', '{': '}', '}': '{'}

def _manual_bidi(text):
    """
    Manual RTL display for matplotlib (no bidi package needed).
    Splits text into Hebrew and non-Hebrew runs, reverses Hebrew runs,
    mirrors brackets, and reverses overall run order so matplotlib's
    LTR rendering produces visually correct RTL output.
    """
    if not text:
        return ''
    text = str(text)

    # Check if text contains any Hebrew at all
    if not any(_is_hebrew(c) for c in text):
        return text

    # Split into runs of same directionality
    runs = []
    current_run = text[0]
    current_is_heb = _is_hebrew(text[0])

    for char in text[1:]:
        char_is_heb = _is_hebrew(char)
        # Neutral chars (spaces, digits, punctuation) stay with current run
        char_is_neutral = char in ' .,;:!?0123456789' or char in _MIRROR

        if char_is_heb == current_is_heb or (char_is_neutral and not char_is_heb):
            current_run += char
        else:
            runs.append((current_run, current_is_heb))
            current_run = char
            current_is_heb = char_is_heb

    runs.append((current_run, current_is_heb))

    # Process each run
    processed = []
    for run_text, is_heb in runs:
        if is_heb or any(_is_hebrew(c) for c in run_text):
            # Reverse Hebrew run and mirror brackets
            mirrored = ''.join(_MIRROR.get(c, c) for c in run_text)
            processed.append(mirrored[::-1])
        else:
            processed.append(run_text)

    # Reverse run order for RTL base direction
    processed.reverse()

    return ''.join(processed)

def hebrew_display(text):
    """Convert Hebrew text for correct RTL display in matplotlib."""
    if not text or pd.isna(text):
        return ''
    text = str(text)
    if HAS_BIDI:
        return get_display(text)
    return _manual_bidi(text)

def hebrew_wrap(text, width=40):
    """Wrap Hebrew text and apply RTL display for matplotlib."""
    if not text or pd.isna(text):
        return ''
    text = str(text)
    lines = textwrap.wrap(text, width=width)
    return '\n'.join(hebrew_display(line) for line in lines)

def truncate_hebrew(text, max_len=30):
    """Truncate text with ellipsis, then apply RTL display."""
    if not text or pd.isna(text):
        return ''
    text = str(text)
    if len(text) > max_len:
        text = text[:max_len] + '...'
    return hebrew_display(text)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
# Safe wrappers: handle missing data and small N gracefully.
# Core metrics: SAD (primary DV for Q1-Q5), entropy (response uncertainty).
# Effect size: Cliff's delta (non-parametric, bounded [-1,1]).
# Statistical tests: all non-parametric (permutation, Wilcoxon, Friedman)
#   to accommodate small N and non-normal SAD distributions.
# ============================================================================

# ---- SAFE WRAPPERS (N-robust, NaN-tolerant) ----
# All functions return NaN or 0 for insufficient data rather than crashing.
# safe_std uses ddof=1 (sample SD, not population) throughout.

def safe_sem(data):
    """Standard Error of Mean, returns 0 if N < 2."""
    if isinstance(data, pd.Series):
        clean = data.dropna().values
    else:
        clean = np.array(data, dtype=float)
        clean = clean[~np.isnan(clean)]
    if len(clean) < 2:
        return 0
    return stats.sem(clean)

def safe_mean(series):
    """Mean, returns NaN if no valid data."""
    clean = series.dropna() if isinstance(series, pd.Series) else pd.Series(series).dropna()
    return clean.mean() if len(clean) > 0 else np.nan

def safe_median(series):
    """Median, returns NaN if no valid data."""
    clean = series.dropna() if isinstance(series, pd.Series) else pd.Series(series).dropna()
    return clean.median() if len(clean) > 0 else np.nan

def safe_std(data, ddof=1):
    """Sample standard deviation (ddof=1 by default). Returns NaN if N < 2."""
    if isinstance(data, pd.Series):
        clean = data.dropna().values
    else:
        clean = np.array(data, dtype=float)
        clean = clean[~np.isnan(clean)]
    if len(clean) < 2:
        return np.nan
    return np.std(clean, ddof=ddof)

def safe_mad(data):
    """Median Absolute Deviation. Robust dispersion measure."""
    if isinstance(data, pd.Series):
        clean = data.dropna().values
    else:
        clean = np.array(data, dtype=float)
        clean = clean[~np.isnan(clean)]
    if len(clean) < 1:
        return np.nan
    median_val = np.median(clean)
    return np.median(np.abs(clean - median_val))

def safe_mode(data):
    """Mode (most common value). Returns first mode if tie."""
    if isinstance(data, pd.Series):
        clean = data.dropna().values
    else:
        clean = np.array(data, dtype=float)
        clean = clean[~np.isnan(clean)]
    if len(clean) < 1:
        return np.nan
    mode_result = stats.mode(clean, keepdims=True)
    return mode_result.mode[0]

def safe_iqr(data):
    """Interquartile Range."""
    if isinstance(data, pd.Series):
        clean = data.dropna().values
    else:
        clean = np.array(data, dtype=float)
        clean = clean[~np.isnan(clean)]
    if len(clean) < 4:
        return np.nan
    return np.percentile(clean, 75) - np.percentile(clean, 25)

def interpret_p_value(p):
    """Convert p-value to significance stars."""
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return "n.s."


# ---- CORE METRICS (SAD, Entropy, Gini-Simpson) ----
# SAD: primary DV. Measures distance from true distribution. Used in Q1-Q5.
# Shannon Entropy: measures response uncertainty in bits. Higher = more uniform.
# Gini-Simpson: probability that two randomly drawn items differ. Complements
#   entropy with a probability-scale diversity measure (Simpson, 1949).

def calculate_sad(estimates, true_dist=None):
    """
    Sum of Absolute Deviations (SAD).
    Range: 0 (perfect) to 22 (worst) for N=12.
    """
    if true_dist is None:
        true_dist = TRUE_DISTRIBUTION
    return int(np.sum(np.abs(np.array(estimates) - np.array(true_dist))))

def calculate_entropy(distribution):
    """
    Shannon entropy in bits (Shannon, 1948).
    Range: 0 (all mass on one item) to 2.0 (uniform over 4 items).
    """
    dist = np.array(distribution, dtype=float)
    if dist.sum() == 0:
        return 0.0
    dist = dist / dist.sum()
    dist = dist[dist > 0]
    return float(-np.sum(dist * np.log2(dist)))

def calculate_gini_simpson(distribution):
    """
    Gini-Simpson diversity index: 1 - sum(pi^2) (Simpson, 1949).
    Probability that two items drawn at random (with replacement) differ.
    Range: 0 (all mass on one category) to 0.75 (uniform over 4 categories).
    True distribution [1,1,4,6] -> pi = [1/12, 1/12, 4/12, 6/12] -> GS = 0.528.
    Uniform [3,3,3,3] -> pi = [0.25]*4 -> GS = 0.75.
    """
    dist = np.array(distribution, dtype=float)
    if dist.sum() == 0:
        return 0.0
    dist = dist / dist.sum()
    return float(1.0 - np.sum(dist ** 2))


# ---- EFFECT SIZE ----
# Cliff's delta: preferred over Cohen's d for non-normal distributions.
# Thresholds from Romano et al. (2006, Behavior Research Methods):
# |d| < 0.147 negligible, < 0.33 small, < 0.474 medium, >= 0.474 large.
# Vectorized via numpy broadcasting for efficiency at large N.

def cliffs_delta(x, y):
    """
    Cliff's delta (vectorized).
    Interpretation: |d| < 0.147 negligible, < 0.33 small, < 0.474 medium, >= 0.474 large.
    (Romano et al., 2006, Behavior Research Methods)
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0 or len(y) == 0:
        return np.nan
    # Vectorized: compare all pairs using broadcasting
    diff_matrix = x[:, None] - y[None, :]
    more = np.sum(diff_matrix > 0)
    less = np.sum(diff_matrix < 0)
    return (more - less) / (len(x) * len(y))

def interpret_cliffs_delta(d):
    """Interpret Cliff's delta magnitude."""
    d = abs(d)
    if d < 0.147:
        return "negligible"
    elif d < 0.33:
        return "small"
    elif d < 0.474:
        return "medium"
    else:
        return "large"


def cohens_h(p1, p2):
    """Cohen's h effect size for comparing two proportions.
    h = 2*arcsin(sqrt(p1)) - 2*arcsin(sqrt(p2))
    Benchmarks: |h| < 0.2 = small, 0.2-0.5 = small-medium, 0.5-0.8 = medium-large, > 0.8 = large
    Reference: Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.).
    """
    import math
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def interpret_cohens_h(h):
    """Interpret Cohen's h magnitude."""
    h = abs(h)
    if h < 0.2:
        return "small"
    elif h < 0.5:
        return "small-medium"
    elif h < 0.8:
        return "medium-large"
    else:
        return "large"


# ---- STATISTICAL TESTS (all non-parametric) ----
# Paired permutation test: used for all within-subject phase comparisons (Q2-Q5).
# One-sample permutation: tests if prior differs from uniform (Q1), T2 < baseline.
# Bootstrap CI: 95% CIs for mean estimates (Q1 item CIs, Q5 improvement CI).
# Friedman test: omnibus test for 4-phase trajectory (precedes pairwise Q2-Q5).

def permutation_test_paired(x, y, n_permutations=10000, alternative='two-sided'):
    """
    Paired permutation test for mean difference.
    Non-parametric alternative to paired t-test.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = ~(np.isnan(x) | np.isnan(y))
    x, y = x[valid], y[valid]
    if len(x) < 2:
        return np.nan, np.nan

    diff = x - y
    observed_diff = np.mean(diff)

    # Vectorized: generate all sign-flip matrices at once
    rng = np.random.default_rng(42)
    signs = rng.choice([-1, 1], size=(n_permutations, len(diff)))
    null_diffs = np.mean(diff[None, :] * signs, axis=1)

    if alternative == 'two-sided':
        p_value = np.mean(np.abs(null_diffs) >= np.abs(observed_diff))
    elif alternative == 'greater':
        p_value = np.mean(null_diffs >= observed_diff)
    else:
        p_value = np.mean(null_diffs <= observed_diff)

    return observed_diff, p_value

def permutation_test_one_sample(x, null_value=0, n_permutations=10000, alternative='two-sided'):
    """One-sample permutation test against a null value."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return np.nan, np.nan

    diff = x - null_value
    observed_mean = np.mean(diff)

    rng = np.random.default_rng(42)
    signs = rng.choice([-1, 1], size=(n_permutations, len(diff)))
    null_means = np.mean(diff[None, :] * signs, axis=1)

    if alternative == 'two-sided':
        p_value = np.mean(np.abs(null_means) >= np.abs(observed_mean))
    elif alternative == 'greater':
        p_value = np.mean(null_means >= observed_mean)
    else:
        p_value = np.mean(null_means <= observed_mean)

    return observed_mean, p_value

def bootstrap_ci(data, statistic=np.mean, n_bootstrap=10000, ci=0.95):
    """Bootstrap confidence interval."""
    data = np.asarray(data, dtype=float)
    data = data[~np.isnan(data)]
    if len(data) < 2:
        return np.nan, np.nan, np.nan

    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(data), size=(n_bootstrap, len(data)))
    boot_stats = np.array([statistic(data[idx]) for idx in indices])

    alpha = 1 - ci
    lower = np.percentile(boot_stats, 100 * alpha / 2)
    upper = np.percentile(boot_stats, 100 * (1 - alpha / 2))
    return statistic(data), lower, upper

def friedman_test(data_matrix):
    """
    Friedman test: non-parametric repeated-measures ANOVA.
    Tests whether distributions of K related samples differ.

    Parameters
    ----------
    data_matrix : array-like, shape (n_subjects, k_conditions)

    Returns
    -------
    statistic, p_value
    """
    data_matrix = np.asarray(data_matrix, dtype=float)
    # Remove rows with any NaN
    valid_rows = ~np.any(np.isnan(data_matrix), axis=1)
    data_matrix = data_matrix[valid_rows]
    if data_matrix.shape[0] < 3:
        return np.nan, np.nan
    result = stats.friedmanchisquare(*[data_matrix[:, i] for i in range(data_matrix.shape[1])])
    return result.statistic, result.pvalue


# ============================================================================
# DATA LOADING - Supports single file, multiple files, or GUI selection
# ============================================================================
# Each CSV has 4 rows per subject (one per phase). Required columns:
# subject_nr, trial_type, gen_est_item1-4, gen_sad.

def select_files_gui():
    """Open GUI file dialog to select CSV files."""
    if not HAS_TKINTER:
        print("tkinter not available. Use command line arguments instead.")
        return []
    root = tk.Tk()
    root.withdraw()
    filepaths = filedialog.askopenfilenames(
        title="Select OneShot CSV file(s)",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    root.destroy()
    return list(filepaths)

def load_single_file(filepath):
    """Load a single CSV file with validation."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(filepath, encoding='utf-8-sig')

    required_cols = ['subject_nr', 'trial_type', 'gen_est_item1', 'gen_est_item2',
                     'gen_est_item3', 'gen_est_item4', 'gen_sad']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df

def load_multiple_files(filepaths):
    """Load and combine multiple CSV files."""
    dfs = []
    for fp in filepaths:
        try:
            df = load_single_file(fp)
            dfs.append(df)
            print(f"  Loaded: {Path(fp).name} ({len(df)} rows)")
        except Exception as e:
            print(f"  Error loading {fp}: {e}")
    if not dfs:
        raise ValueError("No valid files loaded")
    combined = pd.concat(dfs, ignore_index=True)
    print(f"  Combined: {len(combined)} total rows from {len(dfs)} files")
    return combined

def load_data(source=None, use_gui=False):
    """Load data from file path(s), list, or GUI."""
    if source is None:
        if use_gui:
            filepaths = select_files_gui()
            if not filepaths:
                raise ValueError("No files selected")
            source = filepaths
        else:
            raise ValueError("No source provided. Use source= or use_gui=True")

    if isinstance(source, str):
        return load_single_file(source)
    elif isinstance(source, (list, tuple)):
        return load_single_file(source[0]) if len(source) == 1 else load_multiple_files(source)
    else:
        raise ValueError(f"Invalid source type: {type(source)}")


# ============================================================================
# PREPROCESSING - Derive analysis-ready columns from raw CSV
# ============================================================================
# Key derived columns:
#   distance_from_true  - SAD from [1,1,4,6], primary DV for Q1-Q5
#   distance_from_uniform - SAD from [3,3,3,3], used in Q1 to test prior
#   response_entropy    - response spread, secondary DV
#   deliberation_time   - completion_time minus RT, used in timing analysis
#   item_role           - maps each gen_est_itemN to rare/medium/dominant for Q6

def preprocess_data(df):
    """Add derived columns: distances, entropy, item roles, phase order."""
    df = df.copy()

    numeric_cols = ['gen_est_item1', 'gen_est_item2', 'gen_est_item3', 'gen_est_item4',
                    'gen_abs_error_item1', 'gen_abs_error_item2', 'gen_abs_error_item3',
                    'gen_abs_error_item4', 'gen_sad', 'gen_rt', 'gen_completion_time',
                    'gen_est_total', 'post_q3_task_understanding']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Distance from true
    def calc_dist_true(row):
        est = [row['gen_est_item1'], row['gen_est_item2'],
               row['gen_est_item3'], row['gen_est_item4']]
        return np.nan if any(pd.isna(est)) else calculate_sad(est, TRUE_DISTRIBUTION)

    df['distance_from_true'] = df.apply(calc_dist_true, axis=1)

    # Distance from uniform
    def calc_dist_uniform(row):
        est = [row['gen_est_item1'], row['gen_est_item2'],
               row['gen_est_item3'], row['gen_est_item4']]
        return np.nan if any(pd.isna(est)) else calculate_sad(est, UNIFORM_DISTRIBUTION)

    df['distance_from_uniform'] = df.apply(calc_dist_uniform, axis=1)

    # Response entropy
    def calc_entropy(row):
        est = [row['gen_est_item1'], row['gen_est_item2'],
               row['gen_est_item3'], row['gen_est_item4']]
        if any(pd.isna(est)) or sum(est) == 0:
            return np.nan
        return calculate_entropy(est)

    df['response_entropy'] = df.apply(calc_entropy, axis=1)

    # Gini-Simpson diversity index
    def calc_gini_simpson(row):
        est = [row['gen_est_item1'], row['gen_est_item2'],
               row['gen_est_item3'], row['gen_est_item4']]
        if any(pd.isna(est)) or sum(est) == 0:
            return np.nan
        return calculate_gini_simpson(est)

    df['response_gini_simpson'] = df.apply(calc_gini_simpson, axis=1)

    # Item roles
    def parse_item_roles(row):
        if pd.isna(row.get('count_mapping', '')):
            return {}
        try:
            mapping_str = row['count_mapping']
            item_counts = {}
            for pair in mapping_str.split():
                item_id, count = pair.split(':')
                item_counts[item_id] = int(count)
            roles = {}
            for i in range(1, 5):
                pos_col = f'gen_pos{i}_item'
                if pos_col in row.index:
                    item_id = str(row[pos_col])
                    if item_id in item_counts:
                        count = item_counts[item_id]
                        roles[f'item{i}'] = ITEM_ROLES.get(count, 'unknown')
                        roles[f'item{i}_true_count'] = count
            return roles
        except Exception:
            return {}

    role_data = df.apply(parse_item_roles, axis=1)
    for col in ['item1', 'item2', 'item3', 'item4']:
        df[f'{col}_role'] = role_data.apply(lambda x: x.get(col, 'unknown'))
        df[f'{col}_true_count'] = role_data.apply(lambda x: x.get(f'{col}_true_count', np.nan))

    # Deliberation time
    if 'gen_completion_time' in df.columns and 'gen_rt' in df.columns:
        df['deliberation_time'] = df['gen_completion_time'] - df['gen_rt']

    # Phase order index
    df['phase_order'] = df['trial_type'].map({
        'blind_prior': 0, 'prior_icon': 1, 'exposure_gen_1': 2, 'exposure_gen_2': 3
    })

    return df


def validate_data(df):
    """Validate data structure and report issues."""
    report("\n" + "=" * 70)
    report("DATA VALIDATION")
    report("=" * 70)

    validation = {'n_subjects': 0, 'rows_per_subject': {},
                  'missing_phases': [], 'invalid_totals': [],
                  'invalid_sad': [], 'warnings': []}

    subjects = df['subject_nr'].unique()
    validation['n_subjects'] = len(subjects)
    report(f"\nSubjects found: {len(subjects)}")

    for subj in subjects:
        subj_df = df[df['subject_nr'] == subj]
        n_rows = len(subj_df)
        validation['rows_per_subject'][subj] = n_rows
        if n_rows != 4:
            validation['warnings'].append(f"Subject {subj}: {n_rows} rows (expected 4)")
        phases = set(subj_df['trial_type'].unique())
        missing = set(PHASE_ORDER) - phases
        if missing:
            validation['missing_phases'].append((subj, missing))

    row_counts = list(validation['rows_per_subject'].values())
    report(f"Rows per subject: mean={np.mean(row_counts):.1f}, range={min(row_counts)}-{max(row_counts)}")

    if validation['warnings']:
        report(f"\nWarnings ({len(validation['warnings'])}):")
        for w in validation['warnings'][:5]:
            report(f"  - {w}")

    # Check gen_est_total
    if 'gen_est_total' in df.columns:
        invalid_total = df[df['gen_est_total'] != TOTAL_ITEMS]
        if len(invalid_total) > 0:
            validation['invalid_totals'] = invalid_total.index.tolist()
            report(f"\nInvalid totals (not {TOTAL_ITEMS}): {len(invalid_total)} rows")

    # Check SAD parity
    for phase in ['exposure_gen_1', 'exposure_gen_2']:
        phase_df = df[df['trial_type'] == phase]
        if 'gen_sad' in phase_df.columns:
            sad_vals = phase_df['gen_sad'].dropna()
            odd_sad = sad_vals[sad_vals % 2 != 0]
            if len(odd_sad) > 0:
                report(f"Odd SAD in {PHASE_LABELS[phase]}: {len(odd_sad)}")

    report("\nValidation complete.")
    return validation


def get_subject_summary(df):
    """Create one-row-per-subject summary with all key metrics."""
    summaries = []
    for subj in df['subject_nr'].unique():
        subj_df = df[df['subject_nr'] == subj].sort_values('phase_order')
        summary = {'subject_nr': subj}

        # Demographics
        for col in ['demo_age', 'demo_gender', 'demo_handedness', 'demo_color_vision']:
            if col in subj_df.columns:
                summary[col] = subj_df[col].iloc[0]

        # Per-phase metrics
        for phase in PHASE_ORDER:
            phase_row = subj_df[subj_df['trial_type'] == phase]
            if len(phase_row) > 0:
                row = phase_row.iloc[0]
                prefix = PHASE_SHORT[phase]
                for i in range(1, 5):
                    summary[f'{prefix}_est{i}'] = row[f'gen_est_item{i}']
                summary[f'{prefix}_sad'] = row.get('distance_from_true', np.nan)
                summary[f'{prefix}_entropy'] = row.get('response_entropy', np.nan)
                summary[f'{prefix}_gini_simpson'] = row.get('response_gini_simpson', np.nan)
                summary[f'{prefix}_rt'] = row.get('gen_rt', np.nan)
                if 'gen_completion_time' in row.index:
                    summary[f'{prefix}_completion_time'] = row.get('gen_completion_time', np.nan)

        # Learning metrics
        blind_sad = summary.get('Blind_sad', np.nan)
        t2_sad = summary.get('T2_sad', np.nan)
        if not pd.isna(blind_sad) and not pd.isna(t2_sad):
            summary['total_learning'] = blind_sad - t2_sad

        # Questionnaire
        for q in ['post_q1_blind_prior_approach', 'post_q2_icon_prior_approach',
                   'post_q3_task_understanding', 'post_q4_update_strategy',
                   'post_q5_update_between_trials']:
            if q in subj_df.columns:
                summary[q] = subj_df[q].iloc[0]

        summaries.append(summary)
    return pd.DataFrame(summaries)


# ============================================================================
# DESCRIPTIVES - Run BEFORE any inferential tests
# ============================================================================
# Purpose: Full characterization of data before hypothesis testing.
# Reports: SAD (M, Mdn, Mode, SD, MAD, IQR), Entropy (M, SD),
#   RT/Completion/Deliberation per phase, response vectors, quality checks.
# Output: Figure 0, Descriptives CSV, report text.

def run_descriptives(df, summary_df):
    """Phase 0: Comprehensive descriptives by phase. Runs before inferential tests."""
    report("\n" + "=" * 70)
    report("DESCRIPTIVE STATISTICS")
    report("=" * 70)

    results = {
        'n_subjects': len(summary_df),
        'by_phase': {},
        'demographics': {},
        'quality_checks': {}
    }

    # --- Demographics ---
    report("\n--- Demographics ---")
    if 'demo_age' in summary_df.columns:
        ages = summary_df['demo_age'].dropna()
        results['demographics']['age'] = {
            'mean': ages.mean(), 'sd': safe_std(ages),
            'range': (ages.min(), ages.max()), 'n': len(ages)
        }
        report(f"Age: M={ages.mean():.1f}, SD={safe_std(ages):.1f}, range={ages.min():.0f}-{ages.max():.0f}")

    if 'demo_gender' in summary_df.columns:
        gender_counts = summary_df['demo_gender'].value_counts()
        results['demographics']['gender'] = gender_counts.to_dict()
        report(f"Gender: {dict(gender_counts)}")

    # --- Per-Phase Descriptives (full table) ---
    report("\n--- Descriptives by Phase ---")
    report(f"{'Phase':<8} {'SAD_M':>6} {'SAD_SD':>7} {'SAD_Mdn':>8} {'SAD_MAD':>8} "
           f"{'SAD_Mod':>8} {'SAD_IQR':>8} {'Ent_M':>6} {'Ent_SD':>7} "
           f"{'GS_M':>6} {'RT_M':>7} {'RT_SD':>7} {'RT_Mdn':>7}")
    report("-" * 110)

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        phase_stats = {}

        # SAD
        sad_vals = phase_df['distance_from_true'].dropna()
        if len(sad_vals) > 0:
            phase_stats['sad'] = {
                'mean': sad_vals.mean(), 'median': sad_vals.median(),
                'mode': safe_mode(sad_vals), 'sd': safe_std(sad_vals),
                'mad': safe_mad(sad_vals), 'iqr': safe_iqr(sad_vals),
                'min': sad_vals.min(), 'max': sad_vals.max(),
                'sem': safe_sem(sad_vals), 'n': len(sad_vals)
            }

        # Entropy
        ent_vals = phase_df['response_entropy'].dropna()
        if len(ent_vals) > 0:
            phase_stats['entropy'] = {
                'mean': ent_vals.mean(), 'sd': safe_std(ent_vals),
                'median': ent_vals.median()
            }

        # Gini-Simpson
        gs_vals = phase_df['response_gini_simpson'].dropna()
        if len(gs_vals) > 0:
            phase_stats['gini_simpson'] = {
                'mean': gs_vals.mean(), 'sd': safe_std(gs_vals),
                'median': gs_vals.median()
            }

        # RT
        if 'gen_rt' in phase_df.columns:
            rt_vals = phase_df['gen_rt'].dropna()
            if len(rt_vals) > 0:
                phase_stats['rt'] = {
                    'mean': rt_vals.mean(), 'median': rt_vals.median(),
                    'sd': safe_std(rt_vals), 'iqr': safe_iqr(rt_vals),
                    'mad': safe_mad(rt_vals)
                }

        # Completion time
        if 'gen_completion_time' in phase_df.columns:
            comp_vals = phase_df['gen_completion_time'].dropna()
            if len(comp_vals) > 0:
                phase_stats['completion'] = {
                    'mean': comp_vals.mean(), 'median': comp_vals.median(),
                    'sd': safe_std(comp_vals)
                }

        # Deliberation time (completion - RT)
        if 'deliberation_time' in phase_df.columns:
            delib_vals = phase_df['deliberation_time'].dropna()
            if len(delib_vals) > 0:
                phase_stats['deliberation'] = {
                    'mean': delib_vals.mean(), 'median': delib_vals.median(),
                    'sd': safe_std(delib_vals)
                }

        # RT proportion (RT / completion)
        if 'gen_rt' in phase_df.columns and 'gen_completion_time' in phase_df.columns:
            rt_v = phase_df['gen_rt'].dropna()
            comp_v = phase_df.loc[rt_v.index, 'gen_completion_time'].dropna()
            vi = rt_v.index.intersection(comp_v.index)
            if len(vi) > 0:
                props = (rt_v.loc[vi] / comp_v.loc[vi]).replace([np.inf, -np.inf], np.nan).dropna()
                if len(props) > 0:
                    phase_stats['rt_proportion'] = {
                        'mean': props.mean(), 'sd': safe_std(props)
                    }

        # Item estimates
        for i in range(1, 5):
            col = f'gen_est_item{i}'
            if col in phase_df.columns:
                vals = phase_df[col].dropna()
                phase_stats[f'est_item{i}'] = {
                    'mean': vals.mean(), 'sd': safe_std(vals),
                    'median': vals.median()
                }

        results['by_phase'][phase] = phase_stats

        # Print formatted row (reordered: M, SD, Mdn, MAD, Mode, IQR, Ent, GS, RT)
        s = phase_stats.get('sad', {})
        e = phase_stats.get('entropy', {})
        g = phase_stats.get('gini_simpson', {})
        r = phase_stats.get('rt', {})
        report(f"{label:<8} {s.get('mean',0):>6.1f} {s.get('sd',0):>7.2f} "
               f"{s.get('median',0):>8.1f} {s.get('mad',0):>8.2f} "
               f"{s.get('mode',0):>8.1f} {s.get('iqr',0):>8.2f} "
               f"{e.get('mean',0):>6.3f} {e.get('sd',0):>7.3f} "
               f"{g.get('mean',0):>6.3f} "
               f"{r.get('mean',0)/1000:>7.1f} {r.get('sd',0)/1000:>7.1f} {r.get('median',0)/1000:>7.1f}")

    # --- Mean response vectors ---
    report("\n--- Mean Response Vectors ---")
    report(f"True distribution: {TRUE_DISTRIBUTION}")
    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        means = [phase_df[f'gen_est_item{i}'].mean() for i in range(1, 5)]
        label = PHASE_SHORT[phase]
        report(f"  {label}: [{means[0]:.1f}, {means[1]:.1f}, {means[2]:.1f}, {means[3]:.1f}]")

    # --- Quality checks ---
    report("\n--- Quality Checks ---")

    if 'post_q3_task_understanding' in summary_df.columns:
        understanding = summary_df['post_q3_task_understanding'].dropna()
        results['quality_checks']['task_understanding'] = {
            'mean': understanding.mean(), 'sd': safe_std(understanding),
            'distribution': understanding.value_counts().to_dict()
        }
        report(f"Task understanding (1-6): M={understanding.mean():.2f}, SD={safe_std(understanding):.2f}")
        report(f"  Distribution: {dict(understanding.value_counts().sort_index())}")

    # Uniform responders
    uniform_count = 0
    for _, row in summary_df.iterrows():
        is_uniform = all(
            all(row.get(f'{prefix}_est{i}', np.nan) == 3
                for i in range(1, 5) if not pd.isna(row.get(f'{prefix}_est{i}', np.nan)))
            for prefix in ['Blind', 'Icon', 'T1', 'T2']
        )
        if is_uniform:
            uniform_count += 1
    results['quality_checks']['uniform_responders'] = uniform_count
    report(f"Uniform responders (all [3,3,3,3]): {uniform_count}")

    # Non-learners
    if 'total_learning' in summary_df.columns:
        non_learners = int((summary_df['total_learning'] <= 0).sum())
        results['quality_checks']['non_learners'] = non_learners
        report(f"Non-learners (T2 SAD >= Blind SAD): {non_learners}")

    # Perfect T2
    t2_perfect = int((summary_df.get('T2_sad', pd.Series()) == 0).sum())
    results['quality_checks']['perfect_t2'] = t2_perfect
    report(f"Perfect final response (T2 SAD = 0): {t2_perfect}")

    return results


# ============================================================================
# Q1: POPULATION PRIOR - What do people expect before any exposure?
# ============================================================================
# Analyses: (a) Test blind prior against uniform [3,3,3,3] via permutation.
#   (b) Bootstrap CIs per item to identify systematic biases.
#   (c) Classify each participant's sorted prior shape against 5 reference
#       distributions (Uniform, Unimodal-mild, Unimodal-extreme, Bimodal,
#       J-shaped). Sorting removes position identity (blind = gray squares).
# Key output: shape classification distribution, distance from uniform.

def analyze_population_prior(df, summary_df):
    """Q1: Characterize population prior and classify shape vs references."""
    report("\n" + "=" * 70)
    report("Q1: POPULATION PRIOR ANALYSIS")
    report("=" * 70)

    results = {}
    blind = df[df['trial_type'] == 'blind_prior'].copy()
    if len(blind) == 0:
        report("No blind prior data found!")
        return results

    # --- Descriptive ---
    report("\n--- Descriptive Statistics ---")
    mean_response = [blind[f'gen_est_item{i}'].mean() for i in range(1, 5)]
    median_response = [blind[f'gen_est_item{i}'].median() for i in range(1, 5)]
    sd_response = [safe_std(blind[f'gen_est_item{i}']) for i in range(1, 5)]
    results['mean_response'] = mean_response
    results['median_response'] = median_response
    results['sd_response'] = sd_response
    report(f"Mean response: [{mean_response[0]:.2f}, {mean_response[1]:.2f}, "
           f"{mean_response[2]:.2f}, {mean_response[3]:.2f}]")
    report(f"Median response: [{median_response[0]:.0f}, {median_response[1]:.0f}, "
           f"{median_response[2]:.0f}, {median_response[3]:.0f}]")

    # Modal response pattern
    response_patterns = blind.apply(
        lambda r: tuple([r[f'gen_est_item{i}'] for i in range(1, 5)]), axis=1)
    pattern_counts = response_patterns.value_counts()
    results['modal_response'] = list(pattern_counts.index[0])
    results['modal_count'] = int(pattern_counts.iloc[0])
    results['n_unique_patterns'] = len(pattern_counts)
    report(f"Modal response: {list(pattern_counts.index[0])} (n={pattern_counts.iloc[0]})")
    report(f"Unique patterns: {len(pattern_counts)}")

    # Entropy
    entropy_vals = blind['response_entropy'].dropna()
    results['mean_entropy'] = entropy_vals.mean()
    results['sd_entropy'] = safe_std(entropy_vals)
    report(f"Response entropy: M={entropy_vals.mean():.2f}, SD={safe_std(entropy_vals):.2f}")
    report(f"  (Uniform [3,3,3,3] entropy = {calculate_entropy([3, 3, 3, 3]):.2f})")

    # Gini-Simpson
    gs_vals = blind['response_gini_simpson'].dropna()
    results['mean_gini_simpson'] = gs_vals.mean()
    results['sd_gini_simpson'] = safe_std(gs_vals)
    report(f"Gini-Simpson: M={gs_vals.mean():.3f}, SD={safe_std(gs_vals):.3f}")
    report(f"  (Uniform GS = {calculate_gini_simpson([3, 3, 3, 3]):.3f}, "
           f"True GS = {calculate_gini_simpson(TRUE_DISTRIBUTION):.3f})")

    # Distance from uniform
    distances = blind['distance_from_uniform'].dropna()
    results['mean_distance_from_uniform'] = distances.mean()
    report(f"Distance from uniform: M={distances.mean():.2f}, SD={safe_std(distances):.2f}")

    # --- Test: Prior vs Uniform (v15: simulation-based null) ---
    report("\n--- Hypothesis Test: Prior vs Uniform ---")
    n_participants = len(distances)
    observed_mean_sad = distances.mean()

    # CORRECT TEST: Simulate null under Multinomial(12, [0.25, 0.25, 0.25, 0.25])
    # H0: Participants draw from a uniform multinomial. Any non-uniformity is sampling noise.
    # Test: Is the observed mean SAD larger than expected under this null?
    rng_sim = np.random.default_rng(42)
    n_simulations = N_SIMULATIONS
    null_mean_sads = np.zeros(n_simulations)
    uniform_probs = [0.25, 0.25, 0.25, 0.25]

    for sim in range(n_simulations):
        # Simulate n_participants responses from Multinomial(12, uniform)
        sim_responses = rng_sim.multinomial(12, uniform_probs, size=n_participants)
        # Compute SAD from [3,3,3,3] for each
        sim_sads = np.sum(np.abs(sim_responses - 3), axis=1)
        null_mean_sads[sim] = np.mean(sim_sads)

    # Expected SAD under null
    expected_sad_null = np.mean(null_mean_sads)
    sd_null = np.std(null_mean_sads)

    # TWO-TAILED p-value: is observed DIFFERENT from null in either direction?
    # Deviation from null center
    obs_deviation = abs(observed_mean_sad - expected_sad_null)
    null_deviations = np.abs(null_mean_sads - expected_sad_null)
    p_two_tailed = np.mean(null_deviations >= obs_deviation)

    # Also compute one-tailed for reference
    p_greater = np.mean(null_mean_sads >= observed_mean_sad)  # more non-uniform
    p_less = np.mean(null_mean_sads <= observed_mean_sad)     # more uniform

    # Determine direction (descriptive only, no interpretation)
    if observed_mean_sad > expected_sad_null:
        direction = 'observed > null'
    elif observed_mean_sad < expected_sad_null:
        direction = 'observed < null'
    else:
        direction = 'observed = null'

    results['uniform_test'] = {
        'mean_diff': observed_mean_sad,
        'p_value': p_two_tailed,
        'p_two_tailed': p_two_tailed,
        'p_greater': p_greater,
        'p_less': p_less,
        'expected_null_sad': expected_sad_null,
        'sd_null': sd_null,
        'obs_deviation': obs_deviation,
        'direction': direction,
        'n_simulations': n_simulations,
        'test_type': 'multinomial_simulation_two_tailed',
    }
    report(f"  Observed mean SAD from uniform: {observed_mean_sad:.2f}")
    report(f"  Expected mean SAD under Multinomial(12, uniform) null: {expected_sad_null:.2f} (SD={sd_null:.2f})")
    report(f"  Deviation from null: |{observed_mean_sad:.2f} - {expected_sad_null:.2f}| = {obs_deviation:.2f}")
    report(f"")
    report(f"  TWO-TAILED test (is observed DIFFERENT from null?): p = {p_two_tailed:.4f} {interpret_p_value(p_two_tailed)}")
    report(f"  Direction: {direction}")
    report(f"  One-tailed (more non-uniform): p = {p_greater:.4f}")
    report(f"  One-tailed (more uniform):     p = {p_less:.4f}")
    report(f"")
    if p_two_tailed < 0.05:
        if observed_mean_sad > expected_sad_null:
            report(f"  CONCLUSION: Reject H0. Data inconsistent with multinomial noise.")
            report(f"  Direction: observed mean SAD was higher than null expectation.")
        else:
            report(f"  CONCLUSION: Reject H0. Data inconsistent with multinomial noise.")
            report(f"  Direction: observed mean SAD was lower than null expectation.")
    else:
        report(f"  CONCLUSION: Fail to reject H0. Data consistent with multinomial sampling noise.")

    # OLD TEST (sign-flipping, kept for reference but deprecated)
    mean_diff_old, p_value_old = permutation_test_one_sample(
        distances.values, null_value=0, alternative='greater')
    results['uniform_test_old_signflip'] = {'mean_diff': mean_diff_old, 'p_value': p_value_old}
    report(f"\n  [Deprecated] Sign-flip test vs 0: mean={mean_diff_old:.2f}, p={p_value_old:.4f}")

    # --- Icon Prior: same multinomial simulation test (v24) ---
    # P2a: Is the icon prior also more uniform than random multinomial draws?
    report("\n--- Icon Prior vs Uniform (Multinomial Simulation, v24) ---")
    icon_phase = df[df['trial_type'] == 'prior_icon'].copy()
    if len(icon_phase) > 0:
        icon_distances = icon_phase['distance_from_uniform'].dropna().values
        n_icon = len(icon_distances)
        observed_icon_mean_sad = np.mean(icon_distances)

        # Reuse same null model: Multinomial(12, [.25,.25,.25,.25])
        rng_icon = np.random.default_rng(43)  # different seed from blind
        null_icon_means = np.zeros(N_SIMULATIONS)
        for sim in range(N_SIMULATIONS):
            sim_responses = rng_icon.multinomial(12, uniform_probs, size=n_icon)
            sim_sads = np.sum(np.abs(sim_responses - 3), axis=1)
            null_icon_means[sim] = np.mean(sim_sads)

        expected_icon_null = np.mean(null_icon_means)
        sd_icon_null = np.std(null_icon_means)

        # Two-tailed p-value
        icon_obs_dev = abs(observed_icon_mean_sad - expected_icon_null)
        icon_null_devs = np.abs(null_icon_means - expected_icon_null)
        p_icon_two_tailed = np.mean(icon_null_devs >= icon_obs_dev)

        # One-tailed for reference
        p_icon_greater = np.mean(null_icon_means >= observed_icon_mean_sad)
        p_icon_less = np.mean(null_icon_means <= observed_icon_mean_sad)

        # Direction
        if observed_icon_mean_sad > expected_icon_null:
            icon_direction = 'observed > null'
        elif observed_icon_mean_sad < expected_icon_null:
            icon_direction = 'observed < null'
        else:
            icon_direction = 'observed = null'

        results['icon_simulation_test'] = {
            'observed_mean_sad': observed_icon_mean_sad,
            'expected_null_sad': expected_icon_null,
            'sd_null': sd_icon_null,
            'p_value': p_icon_two_tailed,
            'p_two_tailed': p_icon_two_tailed,
            'p_greater': p_icon_greater,
            'p_less': p_icon_less,
            'direction': icon_direction,
            'n': n_icon,
            'n_simulations': N_SIMULATIONS,
            'test_type': 'multinomial_simulation_two_tailed',
        }
        report(f"  Icon prior: n={n_icon}")
        report(f"  Observed mean SAD from uniform: {observed_icon_mean_sad:.2f}")
        report(f"  Expected under null: {expected_icon_null:.2f} (SD={sd_icon_null:.2f})")
        report(f"  TWO-TAILED: p = {p_icon_two_tailed:.4f} {interpret_p_value(p_icon_two_tailed)}")
        report(f"  Direction: {icon_direction}")
        if p_icon_two_tailed < 0.05:
            report(f"  CONCLUSION: Reject H0 for icon prior.")
        else:
            report(f"  CONCLUSION: Fail to reject H0 for icon prior.")
    else:
        report("  No icon prior data found.")

    # --- Bootstrap CIs per item ---
    report("\n--- Bootstrap CIs for Mean Response ---")
    for i in range(4):
        col = f'gen_est_item{i + 1}'
        mean_val, ci_low, ci_high = bootstrap_ci(blind[col].values)
        results[f'item{i + 1}_bootstrap_ci'] = (ci_low, ci_high)
        sig_marker = " ** Significantly different from 3.0 **" if (ci_low > 3 or ci_high < 3) else ""
        report(f"Item {i + 1}: M={mean_val:.2f}, 95% CI [{ci_low:.2f}, {ci_high:.2f}]{sig_marker}")

    # --- Reference Distribution Comparison ---
    report("\n--- Reference Distribution Comparison (sorted shapes) ---")

    def _chi_square_distance(observed, expected):
        """Chi-square distance: sum((O-E)^2/E). Secondary tiebreaker for SAD ties."""
        obs, exp = np.array(observed, dtype=float), np.array(expected, dtype=float)
        exp_safe = np.maximum(exp, 0.5)  # avoid division by zero
        return float(np.sum((obs - exp) ** 2 / exp_safe))

    # For each participant, sort their response and compute SAD to each reference
    ref_distances = {name: [] for name in REFERENCE_DISTRIBUTIONS}
    classifications = []
    tie_log = []  # Track all tie events

    for row_idx, (_, row) in enumerate(blind.iterrows()):
        response = sorted([row[f'gen_est_item{i}'] for i in range(1, 5)])
        if any(pd.isna(response)):
            classifications.append('unknown')
            continue

        # Step 1: Compute SAD to all references
        sad_scores = {}
        for name, ref in REFERENCE_DISTRIBUTIONS.items():
            d = calculate_sad(response, ref)
            ref_distances[name].append(d)
            sad_scores[name] = d

        min_sad = min(sad_scores.values())
        tied_names = [n for n, d in sad_scores.items() if d == min_sad]

        if len(tied_names) == 1:
            # No tie: clear winner
            classifications.append(tied_names[0])
        else:
            # Step 2: Break tie with chi-square distance (secondary)
            chi2_scores = {}
            for name in tied_names:
                ref = REFERENCE_DISTRIBUTIONS[name]
                chi2_scores[name] = _chi_square_distance(response, ref)

            min_chi2 = min(chi2_scores.values())
            chi2_winners = [n for n, d in chi2_scores.items() if abs(d - min_chi2) < 1e-10]

            if len(chi2_winners) == 1:
                # Chi-square resolved the tie
                classifications.append(chi2_winners[0])
                tie_log.append({
                    'subject_idx': row_idx, 'response': response,
                    'tied_refs': tied_names, 'sad': min_sad,
                    'resolved_by': 'chi-square', 'winner': chi2_winners[0],
                    'chi2_scores': chi2_scores
                })
            else:
                # Step 3: Still tied after chi-square -> "Mixed" composite category
                composite = ' + '.join(sorted(chi2_winners))
                classifications.append(composite)
                tie_log.append({
                    'subject_idx': row_idx, 'response': response,
                    'tied_refs': tied_names, 'sad': min_sad,
                    'resolved_by': 'mixed', 'winner': composite,
                    'chi2_scores': chi2_scores
                })

    results['ref_distances'] = {name: np.mean(vals) if vals else np.nan
                                 for name, vals in ref_distances.items()}
    results['classifications'] = classifications
    results['tie_log'] = tie_log
    results['n_ties'] = len(tie_log)
    results['n_ties_resolved'] = sum(1 for t in tie_log if t['resolved_by'] == 'chi-square')
    results['n_ties_mixed'] = sum(1 for t in tie_log if t['resolved_by'] == 'mixed')

    # Report distances
    report(f"  {'Reference':<22} {'Mean SAD':>8}  {'Median SAD':>10}")
    report("  " + "-" * 44)
    for name, vals in ref_distances.items():
        if vals:
            report(f"  {name:<22} {np.mean(vals):>8.2f}  {np.median(vals):>10.1f}")

    # Report classifications
    from collections import Counter
    class_counts = Counter(classifications)
    results['classification_counts'] = dict(class_counts)
    report(f"\n  Shape classifications (best-fitting reference):")
    for name, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(classifications)
        report(f"    {name}: {count} ({pct:.0f}%)")

    # Report tie statistics
    n_valid = len([c for c in classifications if c != 'unknown'])
    report(f"\n  Tie statistics:")
    report(f"    Total participants: {n_valid}")
    report(f"    Ties detected: {len(tie_log)} ({100*len(tie_log)/n_valid:.0f}%)" if n_valid > 0 else "")
    report(f"    Resolved by chi-square tiebreaker: {results['n_ties_resolved']}")
    report(f"    Remaining as Mixed: {results['n_ties_mixed']}")
    if tie_log:
        report(f"    Tie details:")
        for t in tie_log:
            report(f"      Response {t['response']}: SAD={t['sad']} tied [{', '.join(t['tied_refs'])}] "
                   f"-> {t['resolved_by']}: {t['winner']}")

    # ================================================================
    # CLASSIFICATION SIGNIFICANCE TESTS (v19)
    # ================================================================
    # Tests whether observed classification proportions differ from what
    # Multinomial(12, uniform) noise would produce.
    report("\n--- Classification Significance Tests ---")

    n_valid_class = len([c for c in classifications if c != 'unknown'])
    if n_valid_class >= 3:
        # Simulate null classification proportions
        rng_class = np.random.default_rng(42)
        n_class_sims = N_SIMULATIONS
        ref_names = list(REFERENCE_DISTRIBUTIONS.keys())
        null_class_counts = {name: np.zeros(n_class_sims) for name in ref_names}
        null_class_counts['Mixed'] = np.zeros(n_class_sims)

        for sim_idx in range(n_class_sims):
            sim_classifications = []
            for _ in range(n_valid_class):
                # Generate one response from Multinomial(12, uniform)
                sim_resp = list(rng_class.multinomial(12, [0.25]*4))
                sim_sorted = sorted(sim_resp)

                # Classify using same 3-tier system
                sad_scores = {}
                for name, ref in REFERENCE_DISTRIBUTIONS.items():
                    sad_scores[name] = calculate_sad(sim_sorted, ref)
                min_sad = min(sad_scores.values())
                tied = [n for n, d in sad_scores.items() if d == min_sad]

                if len(tied) == 1:
                    sim_classifications.append(tied[0])
                else:
                    chi2_s = {n: _chi_square_distance(sim_sorted, REFERENCE_DISTRIBUTIONS[n]) for n in tied}
                    min_chi2 = min(chi2_s.values())
                    chi2_winners = [n for n, d in chi2_s.items() if abs(d - min_chi2) < 1e-10]
                    if len(chi2_winners) == 1:
                        sim_classifications.append(chi2_winners[0])
                    else:
                        sim_classifications.append('Mixed')

            # Count per category
            for name in ref_names:
                null_class_counts[name][sim_idx] = sim_classifications.count(name)
            null_class_counts['Mixed'][sim_idx] = sum(1 for c in sim_classifications if c not in ref_names)

        # Store for figure reuse
        results['null_class_counts'] = {k: v.copy() for k, v in null_class_counts.items()}

        # Store individual simulated response classifications for histogram (reuse, no new simulation)
        # Collect SAD + category for N_SIMULATIONS individual responses
        rng_ind = np.random.default_rng(99)
        individual_sads_by_cat = {}
        for _ in range(n_class_sims):
            sim_resp = list(rng_ind.multinomial(12, [0.25]*4))
            sim_sorted = sorted(sim_resp)
            sad_val = sum(abs(s - 3) for s in sim_resp)
            sad_scores_i = {}
            for name, ref in REFERENCE_DISTRIBUTIONS.items():
                sad_scores_i[name] = calculate_sad(sim_sorted, ref)
            min_sad_i = min(sad_scores_i.values())
            tied_i = [n for n, d in sad_scores_i.items() if d == min_sad_i]
            if len(tied_i) == 1:
                cat = tied_i[0]
            else:
                chi2_i = {n: _chi_square_distance(sim_sorted, REFERENCE_DISTRIBUTIONS[n]) for n in tied_i}
                min_c = min(chi2_i.values())
                cw = [n for n, d in chi2_i.items() if abs(d - min_c) < 1e-10]
                cat = cw[0] if len(cw) == 1 else 'Mixed'
            if cat not in individual_sads_by_cat:
                individual_sads_by_cat[cat] = []
            individual_sads_by_cat[cat].append(sad_val)
        results['null_individual_sads_by_cat'] = individual_sads_by_cat

        # Observed counts
        from collections import Counter
        obs_counts = Counter(classifications)
        all_categories = ref_names + ['Mixed']

        # (1) Per-category simulation test
        report(f"\n  Per-category test (is each proportion surprising under H0?):")
        report(f"  {'Category':<22} {'Obs':>4} {'Obs%':>6} {'Null%':>7} {'p_value':>8} {'Sig':>5}")
        report(f"  " + "-" * 56)
        results['classification_significance'] = {}
        n_cat_tests = len([c for c in all_categories if obs_counts.get(c, 0) > 0 or c in ref_names])
        bonf_alpha_cat = 0.05 / max(n_cat_tests, 1)

        for cat in all_categories:
            obs_n = obs_counts.get(cat, 0)
            obs_pct = 100 * obs_n / n_valid_class
            null_counts_cat = null_class_counts.get(cat, np.zeros(n_class_sims))
            null_pct = 100 * np.mean(null_counts_cat) / n_valid_class

            # Two-tailed: is observed count significantly different from null?
            null_dev = np.abs(null_counts_cat - np.mean(null_counts_cat))
            obs_dev = abs(obs_n - np.mean(null_counts_cat))
            p_val = np.mean(null_dev >= obs_dev)

            sig = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'n.s.'
            # Cohen's h effect size for proportion comparison (v24)
            obs_prop = obs_n / n_valid_class
            null_prop = np.mean(null_counts_cat) / n_valid_class
            h_val = cohens_h(obs_prop, null_prop) if (obs_prop > 0 or null_prop > 0) else 0.0
            results['classification_significance'][cat] = {
                'observed_n': obs_n, 'observed_pct': obs_pct,
                'null_mean_pct': null_pct, 'p_value': p_val,
                'null_mean_n': float(np.mean(null_counts_cat)),
                'null_sd_n': float(np.std(null_counts_cat)),
                'cohens_h': h_val,
                'cohens_h_interp': interpret_cohens_h(h_val),
            }
            h_str = f" h={h_val:.2f}" if p_val < 0.05 else ""
            report(f"  {cat:<22} {obs_n:>4} {obs_pct:>5.0f}% {null_pct:>6.1f}% {p_val:>8.4f} {sig:>5}{h_str}")

        # (2) Binary test: Uniform vs Non-uniform
        report(f"\n  Binary test (Uniform vs Non-uniform):")
        obs_uniform = obs_counts.get('Uniform', 0)
        null_uniform = null_class_counts.get('Uniform', np.zeros(n_class_sims))
        null_dev_u = np.abs(null_uniform - np.mean(null_uniform))
        obs_dev_u = abs(obs_uniform - np.mean(null_uniform))
        p_binary = np.mean(null_dev_u >= obs_dev_u)
        results['classification_binary'] = {
            'obs_uniform': obs_uniform, 'obs_pct': 100 * obs_uniform / n_valid_class,
            'null_mean_pct': 100 * np.mean(null_uniform) / n_valid_class,
            'p_value': p_binary,
        }
        report(f"    Uniform: {obs_uniform}/{n_valid_class} ({100*obs_uniform/n_valid_class:.0f}%) "
               f"vs null {100*np.mean(null_uniform)/n_valid_class:.1f}%, p = {p_binary:.4f} {interpret_p_value(p_binary)}")

        # (3) Test for observed 2-category split (Uniform + Unimodal-mild)
        obs_top2 = obs_counts.get('Uniform', 0) + obs_counts.get('Unimodal-mild', 0)
        null_top2 = null_class_counts.get('Uniform', np.zeros(n_class_sims)) + \
                    null_class_counts.get('Unimodal-mild', np.zeros(n_class_sims))
        null_dev_t2 = np.abs(null_top2 - np.mean(null_top2))
        obs_dev_t2 = abs(obs_top2 - np.mean(null_top2))
        p_top2 = np.mean(null_dev_t2 >= obs_dev_t2)
        results['classification_top2'] = {
            'obs_n': obs_top2, 'obs_pct': 100 * obs_top2 / n_valid_class,
            'null_mean_pct': 100 * np.mean(null_top2) / n_valid_class,
            'p_value': p_top2,
        }
        report(f"    Uniform + Unimodal-mild: {obs_top2}/{n_valid_class} ({100*obs_top2/n_valid_class:.0f}%) "
               f"vs null {100*np.mean(null_top2)/n_valid_class:.1f}%, p = {p_top2:.4f} {interpret_p_value(p_top2)}")

        # (4) Model comparison: k=5,4,3,2,1
        report(f"\n  Model comparison (stepwise category reduction):")
        report(f"  {'k':>3} {'Categories':>40} {'Chi2':>8} {'p_value':>8} {'Sig':>5}")
        report(f"  " + "-" * 68)
        results['model_comparison'] = {}

        # Build observed and null vectors for different k levels
        # k=5: all 5 references
        # k=4: merge two least frequent
        # k=3: merge three least frequent
        # k=2: Uniform vs rest
        # k=1: all same (trivially fits)

        obs_sorted = sorted(obs_counts.items(), key=lambda x: -x[1])
        for k in [5, 4, 3, 2]:
            if k >= len(obs_sorted):
                # Keep top k-1 categories, merge rest into "Other"
                top_cats = [c for c, _ in obs_sorted[:k-1]]
            else:
                top_cats = [c for c, _ in obs_sorted[:k-1]]

            # Observed: top k-1 categories + "Other"
            obs_vec = [obs_counts.get(c, 0) for c in top_cats]
            obs_other = n_valid_class - sum(obs_vec)
            obs_vec.append(obs_other)

            # Null expected: same grouping
            null_vecs = []
            for sim_idx in range(n_class_sims):
                nv = [null_class_counts.get(c, np.zeros(n_class_sims))[sim_idx] for c in top_cats]
                nv.append(n_valid_class - sum(nv))
                null_vecs.append(nv)
            null_expected = np.mean(null_vecs, axis=0)

            # Chi-square GoF (avoid zero expected)
            null_safe = np.maximum(null_expected, 0.5)
            chi2_val = np.sum((np.array(obs_vec) - null_expected) ** 2 / null_safe)

            # Simulation p: proportion of null chi2 >= observed chi2
            null_chi2s = []
            for nv in null_vecs:
                nv = np.array(nv)
                nc2 = np.sum((nv - null_expected) ** 2 / null_safe)
                null_chi2s.append(nc2)
            p_model = np.mean(np.array(null_chi2s) >= chi2_val)

            cat_labels = top_cats + ['Other']
            cat_str = ', '.join(cat_labels[:k])
            sig = '***' if p_model < 0.001 else '**' if p_model < 0.01 else '*' if p_model < 0.05 else 'n.s.'
            results['model_comparison'][k] = {
                'categories': cat_labels, 'chi2': chi2_val,
                'p_value': p_model, 'observed': obs_vec, 'expected': null_expected.tolist()
            }
            report(f"  {k:>3} {cat_str:>40} {chi2_val:>8.3f} {p_model:>8.4f} {sig:>5}")

    # ================================================================
    # ITEM-LEVEL PHASE TESTS (new v12)
    # ================================================================
    report("\n--- Item-Level Phase Tests ---")

    # (A) Per-item Wilcoxon: Blind vs Icon (4 tests, Bonferroni alpha=0.0125)
    report("\n  (A) Blind vs Icon per item (Wilcoxon, Bonferroni alpha=0.0125):")
    results['item_blind_icon'] = {}
    n_item_tests = 4
    bonf_alpha = 0.05 / n_item_tests

    for item_idx in range(1, 5):
        role = ['rare', 'rare', 'medium', 'dominant'][item_idx - 1]
        true_val = TRUE_DISTRIBUTION[item_idx - 1]
        blind_vals, icon_vals = [], []
        for _, row in summary_df.iterrows():
            b = row.get(f'Blind_est{item_idx}', np.nan)
            ic = row.get(f'Icon_est{item_idx}', np.nan)
            if not (pd.isna(b) or pd.isna(ic)):
                blind_vals.append(b)
                icon_vals.append(ic)
        blind_arr, icon_arr = np.array(blind_vals), np.array(icon_vals)

        if len(blind_arr) >= 3:
            # Remove tied pairs (Wilcoxon cannot handle all-zero differences)
            diffs = icon_arr - blind_arr
            non_zero = diffs[diffs != 0]
            if len(non_zero) >= 1:
                try:
                    w_stat, w_p = stats.wilcoxon(blind_arr, icon_arr)
                except ValueError:
                    w_stat, w_p = np.nan, np.nan
            else:
                w_stat, w_p = 0, 1.0  # All identical

            bonf_p = min(w_p * n_item_tests, 1.0)
            shift = np.mean(icon_arr) - np.mean(blind_arr)
            results['item_blind_icon'][item_idx] = {
                'w_stat': w_stat, 'p_uncorrected': w_p, 'p_bonferroni': bonf_p,
                'mean_shift': shift, 'n': len(blind_arr),
                'blind_mean': np.mean(blind_arr), 'icon_mean': np.mean(icon_arr),
                'role': role, 'true': true_val
            }
            sig = '***' if bonf_p < 0.001 else '**' if bonf_p < 0.01 else '*' if bonf_p < 0.05 else 'n.s.'
            report(f"    Item {item_idx} ({role}, true={true_val}): "
                   f"Blind M={np.mean(blind_arr):.2f} -> Icon M={np.mean(icon_arr):.2f} "
                   f"(shift={shift:+.2f}), W={w_stat:.1f}, p_raw={w_p:.4f}, p_bonf={bonf_p:.4f} {sig}")
        else:
            report(f"    Item {item_idx} ({role}): insufficient data (n={len(blind_arr)})")

    # (B) Per-item Friedman across ALL 4 phases (4 tests, Bonferroni)
    report("\n  (B) Per-item Friedman across 4 phases (Bonferroni alpha=0.0125):")
    results['item_friedman_4phase'] = {}
    phase_prefixes = ['Blind', 'Icon', 'T1', 'T2']

    for item_idx in range(1, 5):
        role = ['rare', 'rare', 'medium', 'dominant'][item_idx - 1]
        matrix = []
        for _, row in summary_df.iterrows():
            vals = [row.get(f'{prefix}_est{item_idx}', np.nan) for prefix in phase_prefixes]
            if not any(pd.isna(v) for v in vals):
                matrix.append(vals)
        matrix = np.array(matrix)

        if matrix.shape[0] >= 3:
            chi2, p = stats.friedmanchisquare(*[matrix[:, i] for i in range(4)])
            bonf_p = min(p * n_item_tests, 1.0)
            means = [np.mean(matrix[:, i]) for i in range(4)]
            results['item_friedman_4phase'][item_idx] = {
                'chi2': chi2, 'p_uncorrected': p, 'p_bonferroni': bonf_p,
                'n': matrix.shape[0], 'phase_means': means, 'role': role
            }
            sig = '***' if bonf_p < 0.001 else '**' if bonf_p < 0.01 else '*' if bonf_p < 0.05 else 'n.s.'
            report(f"    Item {item_idx} ({role}): chi2={chi2:.3f}, p_raw={p:.4f}, p_bonf={bonf_p:.4f} {sig} "
                   f"(means: {' -> '.join(f'{m:.2f}' for m in means)})")
        else:
            report(f"    Item {item_idx} ({role}): insufficient data")

    # (C) Interaction: Friedman on Blind-to-Icon shift across 4 items
    report("\n  (C) Interaction: does shift magnitude differ by item? (Friedman on Icon-Blind shifts):")
    shift_matrix = []
    for _, row in summary_df.iterrows():
        shifts = []
        valid = True
        for item_idx in range(1, 5):
            b = row.get(f'Blind_est{item_idx}', np.nan)
            ic = row.get(f'Icon_est{item_idx}', np.nan)
            if pd.isna(b) or pd.isna(ic):
                valid = False
                break
            shifts.append(ic - b)
        if valid:
            shift_matrix.append(shifts)
    shift_matrix = np.array(shift_matrix)

    if shift_matrix.shape[0] >= 3:
        chi2_int, p_int = stats.friedmanchisquare(*[shift_matrix[:, i] for i in range(4)])
        results['interaction_shift'] = {
            'chi2': chi2_int, 'p_value': p_int, 'n': shift_matrix.shape[0],
            'mean_shifts': [np.mean(shift_matrix[:, i]) for i in range(4)]
        }
        report(f"    Friedman on shifts: chi2={chi2_int:.3f}, p={p_int:.4f} {interpret_p_value(p_int)}")
        report(f"    Mean shifts: " + ', '.join(
            f"Item {i+1}({['rare','rare','medium','dominant'][i]})={np.mean(shift_matrix[:,i]):+.2f}"
            for i in range(4)))
    else:
        report(f"    Insufficient data (n={shift_matrix.shape[0]})")

    return results


# ============================================================================
# FRIEDMAN OMNIBUS - Is there ANY change across the 4 phases?
# ============================================================================
# Non-parametric repeated-measures test on SAD across all 4 phases.
# Runs BEFORE pairwise Q2-Q5 to justify follow-up comparisons.
# Post-hoc: Wilcoxon signed-rank for all 6 pairs, Bonferroni-corrected.
# Rationale: controls family-wise error rate for the 4 pairwise tests.

def run_friedman_omnibus(summary_df):
    """Friedman test on 4-phase SAD trajectory + Bonferroni post-hoc."""
    report("\n" + "=" * 70)
    report("FRIEDMAN OMNIBUS TEST (4-phase SAD trajectory)")
    report("=" * 70)

    results = {}

    # Build data matrix: N x 4
    sad_cols = ['Blind_sad', 'Icon_sad', 'T1_sad', 'T2_sad']
    available = [c for c in sad_cols if c in summary_df.columns]
    if len(available) < 4:
        report("Not enough phase data for Friedman test.")
        return results

    data_matrix = summary_df[sad_cols].dropna().values
    n_valid = data_matrix.shape[0]
    results['n_valid'] = n_valid

    if n_valid < 3:
        report(f"Insufficient subjects with complete data (n={n_valid}, need >= 3)")
        return results

    chi2, p_value = friedman_test(data_matrix)
    results['statistic'] = chi2
    results['p_value'] = p_value
    report(f"\nFriedman chi-square({3}) = {chi2:.3f}, p = {p_value:.4f} {interpret_p_value(p_value)}")
    report(f"N = {n_valid} (subjects with complete data across all 4 phases)")

    # Post-hoc pairwise Wilcoxon with Bonferroni correction
    report("\n--- Post-hoc Pairwise Wilcoxon (Bonferroni-corrected) ---")
    n_comparisons = 6  # 4 choose 2
    pairwise_results = []

    pairs = [
        ('Blind_sad', 'Icon_sad', 'Blind vs Icon'),
        ('Blind_sad', 'T1_sad', 'Blind vs T1'),
        ('Blind_sad', 'T2_sad', 'Blind vs T2'),
        ('Icon_sad', 'T1_sad', 'Icon vs T1'),
        ('Icon_sad', 'T2_sad', 'Icon vs T2'),
        ('T1_sad', 'T2_sad', 'T1 vs T2'),
    ]

    valid_df = summary_df[sad_cols].dropna()

    for col1, col2, label in pairs:
        x = valid_df[col1].values
        y = valid_df[col2].values
        diff = x - y
        nonzero = diff[diff != 0]

        if len(nonzero) > 0:
            w_stat, w_p = stats.wilcoxon(x, y)
            bonf_p = min(w_p * n_comparisons, 1.0)
        else:
            w_stat, w_p, bonf_p = np.nan, np.nan, np.nan

        pairwise_results.append({
            'comparison': label, 'W': w_stat,
            'p_uncorrected': w_p, 'p_bonferroni': bonf_p,
            'mean_diff': np.mean(diff)
        })
        report(f"  {label:<16}: diff={np.mean(diff):+.2f}, W={w_stat:.1f}, "
               f"p={w_p:.4f}, p_bonf={bonf_p:.4f} {interpret_p_value(bonf_p)}")

    results['pairwise'] = pairwise_results
    return results


# ============================================================================
# Q2: SHAPE EFFECT - Does seeing item shapes change the prior?
# ============================================================================
# Comparison: Blind Prior vs Icon Prior (within-subject).
# Tests whether visual shape appearance triggers frequency biases
# independent of distributional exposure.
# Stats: two-sided permutation + Wilcoxon + Cliff's delta.

def analyze_shape_effect(df, summary_df):
    """Q2: Blind -> Icon paired comparison."""
    report("\n" + "=" * 70)
    report("Q2: SHAPE EFFECT (BLIND -> ICON)")
    report("=" * 70)

    results = {}
    blind_sad = summary_df['Blind_sad'].values
    icon_sad = summary_df['Icon_sad'].values
    valid = ~(np.isnan(blind_sad) | np.isnan(icon_sad))
    blind_v, icon_v = blind_sad[valid], icon_sad[valid]

    if len(blind_v) < 2:
        report("Insufficient data"); return results

    results['n_valid'] = len(blind_v)
    diff = blind_v - icon_v

    report(f"\n--- Paired Comparison (n={len(blind_v)}) ---")
    report(f"Blind prior: M={np.mean(blind_v):.2f}, SD={safe_std(blind_v):.2f}")
    report(f"Icon prior:  M={np.mean(icon_v):.2f}, SD={safe_std(icon_v):.2f}")
    report(f"Difference (Blind - Icon): M={np.mean(diff):.2f}, SD={safe_std(diff):.2f}")
    results['mean_diff'] = np.mean(diff)

    report("\n--- Statistical Tests ---")
    obs, p = permutation_test_paired(blind_v, icon_v, alternative='two-sided')
    results['permutation_test'] = {'observed_diff': obs, 'p_value': p}
    report(f"Paired permutation test: diff={obs:.2f}, p={p:.4f} {interpret_p_value(p)}")

    nonzero = diff[diff != 0]
    if len(nonzero) > 0:
        w, wp = stats.wilcoxon(blind_v, icon_v)
        results['wilcoxon_test'] = {'statistic': w, 'p_value': wp}
        report(f"Wilcoxon signed-rank: W={w:.1f}, p={wp:.4f} {interpret_p_value(wp)}")

    d = cliffs_delta(blind_v, icon_v)
    results['cliffs_delta'] = d
    report(f"Cliff's delta: {d:.3f} ({interpret_cliffs_delta(d)})")

    improved = int(np.sum(diff > 0))
    worsened = int(np.sum(diff < 0))
    no_change = int(np.sum(diff == 0))
    results['direction'] = {'improved': improved, 'worsened': worsened, 'no_change': no_change}
    report(f"Direction: {improved} improved, {worsened} worsened, {no_change} no change")

    return results


# ============================================================================
# Q_BLIND_T1: PRIOR TO FIRST TEST - Combined icon + first-exposure effect
# ============================================================================
# Comparison: Blind Prior vs Trial 1 (within-subject, two-tailed).
# Captures the COMBINED effect of seeing item shapes (icon) plus the first
# array exposure + feedback, relative to the uninformed blind prior.
# Same pattern as Q2 (two-sided permutation + Wilcoxon + Cliff's delta).

def analyze_blind_vs_t1(df, summary_df):
    """Q_blind_t1: Blind -> Trial 1 paired comparison (two-tailed)."""
    report("\n" + "=" * 70)
    report("Q_BLIND_T1: PRIOR TO FIRST TEST (BLIND -> TRIAL 1)")
    report("=" * 70)

    results = {}
    blind_sad = summary_df['Blind_sad'].values
    t1_sad = summary_df['T1_sad'].values
    valid = ~(np.isnan(blind_sad) | np.isnan(t1_sad))
    blind_v, t1_v = blind_sad[valid], t1_sad[valid]

    if len(blind_v) < 2:
        report("Insufficient data"); return results

    results['n_valid'] = len(blind_v)
    diff = blind_v - t1_v

    report(f"\n--- Paired Comparison (n={len(blind_v)}) ---")
    report(f"Blind prior: M={np.mean(blind_v):.2f}, SD={safe_std(blind_v):.2f}")
    report(f"Trial 1:     M={np.mean(t1_v):.2f}, SD={safe_std(t1_v):.2f}")
    report(f"Difference (Blind - T1): M={np.mean(diff):.2f}, SD={safe_std(diff):.2f}")
    results['mean_diff'] = np.mean(diff)

    report("\n--- Statistical Tests ---")
    obs, p = permutation_test_paired(blind_v, t1_v, alternative='two-sided')
    results['permutation_test'] = {'observed_diff': obs, 'p_value': p}
    report(f"Paired permutation test: diff={obs:.2f}, p={p:.4f} {interpret_p_value(p)}")

    nonzero = diff[diff != 0]
    if len(nonzero) > 0:
        w, wp = stats.wilcoxon(blind_v, t1_v)
        results['wilcoxon_test'] = {'statistic': w, 'p_value': wp}
        report(f"Wilcoxon signed-rank: W={w:.1f}, p={wp:.4f} {interpret_p_value(wp)}")

    d = cliffs_delta(blind_v, t1_v)
    results['cliffs_delta'] = d
    report(f"Cliff's delta: {d:.3f} ({interpret_cliffs_delta(d)})")

    improved = int(np.sum(diff > 0))
    worsened = int(np.sum(diff < 0))
    no_change = int(np.sum(diff == 0))
    results['direction'] = {'improved': improved, 'worsened': worsened, 'no_change': no_change}
    report(f"Direction: {improved} improved, {worsened} worsened, {no_change} no change")

    return results


# ============================================================================
# Q3: EXPOSURE EFFECT - Does a single exposure produce learning?
# ============================================================================
# Comparison: Icon Prior vs Trial 1 (within-subject, one-tailed).
# Core "one-shot learning" question. After seeing the array once and
# receiving SAD feedback, do estimates improve?
# Also benchmarks T1 against uniform baseline (SAD=8).

def analyze_exposure_effect(df, summary_df):
    """Q3: Icon -> Trial 1 paired comparison (one-tailed: Icon > T1)."""
    report("\n" + "=" * 70)
    report("Q3: EXPOSURE EFFECT (ICON -> TRIAL 1)")
    report("=" * 70)

    results = {}
    icon_sad = summary_df['Icon_sad'].values
    t1_sad = summary_df['T1_sad'].values
    valid = ~(np.isnan(icon_sad) | np.isnan(t1_sad))
    icon_v, t1_v = icon_sad[valid], t1_sad[valid]

    if len(icon_v) < 2:
        report("Insufficient data"); return results

    results['n_valid'] = len(icon_v)
    diff = icon_v - t1_v  # Positive = improvement

    report(f"\n--- Paired Comparison (n={len(icon_v)}) ---")
    report(f"Icon prior: M={np.mean(icon_v):.2f}, SD={safe_std(icon_v):.2f}")
    report(f"Trial 1:    M={np.mean(t1_v):.2f}, SD={safe_std(t1_v):.2f}")
    report(f"Improvement (Icon - T1): M={np.mean(diff):.2f}, SD={safe_std(diff):.2f}")
    results['mean_diff'] = np.mean(diff)

    report("\n--- Statistical Tests ---")
    obs, p = permutation_test_paired(icon_v, t1_v, alternative='greater')
    results['permutation_test'] = {'observed_diff': obs, 'p_value': p}
    report(f"Icon > T1 (one-tailed): diff={obs:.2f}, p={p:.4f} {interpret_p_value(p)}")

    d = cliffs_delta(icon_v, t1_v)
    results['cliffs_delta'] = d
    report(f"Cliff's delta: {d:.3f} ({interpret_cliffs_delta(d)})")

    # Benchmark: T1 vs uniform
    t1_diff, t1_p = permutation_test_one_sample(t1_v, null_value=UNIFORM_SAD, alternative='less')
    results['t1_vs_uniform'] = {'mean_diff': t1_diff, 'p_value': t1_p}
    report(f"\n--- Benchmark: T1 vs Uniform (SAD=8) ---")
    report(f"T1 < Uniform: diff={t1_diff:.2f}, p={t1_p:.4f} {interpret_p_value(t1_p)}")

    improved = int(np.sum(diff > 0))
    worsened = int(np.sum(diff < 0))
    results['direction'] = {'improved': improved, 'worsened': worsened}
    report(f"Direction: {improved} improved, {int(np.sum(diff < 0))} worsened")

    return results


# ============================================================================
# Q4: REPETITION EFFECT - Does a second exposure improve learning?
# ============================================================================
# Comparison: Trial 1 vs Trial 2 (within-subject, one-tailed).
# Tests whether additional exposure refines estimates beyond one-shot.
# Includes ceiling-effect check (excludes perfect T1 responders).

def analyze_repetition_effect(df, summary_df):
    """Q4: T1 -> T2 paired comparison (one-tailed: T1 > T2)."""
    report("\n" + "=" * 70)
    report("Q4: REPETITION EFFECT (TRIAL 1 -> TRIAL 2)")
    report("=" * 70)

    results = {}
    t1_sad = summary_df['T1_sad'].values
    t2_sad = summary_df['T2_sad'].values
    valid = ~(np.isnan(t1_sad) | np.isnan(t2_sad))
    t1_v, t2_v = t1_sad[valid], t2_sad[valid]

    if len(t1_v) < 2:
        report("Insufficient data"); return results

    results['n_valid'] = len(t1_v)
    diff = t1_v - t2_v

    report(f"\n--- Paired Comparison (n={len(t1_v)}) ---")
    report(f"Trial 1: M={np.mean(t1_v):.2f}, SD={safe_std(t1_v):.2f}")
    report(f"Trial 2: M={np.mean(t2_v):.2f}, SD={safe_std(t2_v):.2f}")
    report(f"Improvement (T1 - T2): M={np.mean(diff):.2f}, SD={safe_std(diff):.2f}")
    results['mean_diff'] = np.mean(diff)

    report("\n--- Statistical Tests ---")
    obs, p = permutation_test_paired(t1_v, t2_v, alternative='greater')
    results['permutation_test'] = {'observed_diff': obs, 'p_value': p}
    report(f"T1 > T2 (one-tailed): diff={obs:.2f}, p={p:.4f} {interpret_p_value(p)}")

    d = cliffs_delta(t1_v, t2_v)
    results['cliffs_delta'] = d
    report(f"Cliff's delta: {d:.3f} ({interpret_cliffs_delta(d)})")

    # Ceiling check
    non_perfect = t1_v > 0
    if np.sum(non_perfect) > 1:
        report(f"\n--- Excluding Perfect T1 (n={int(np.sum(~non_perfect))}) ---")
        t1_np, t2_np = t1_v[non_perfect], t2_v[non_perfect]
        report(f"Non-perfect: T1 M={np.mean(t1_np):.2f}, T2 M={np.mean(t2_np):.2f}, "
               f"Improvement: {np.mean(t1_np - t2_np):.2f}")

    improved = int(np.sum(diff > 0))
    worsened = int(np.sum(diff < 0))
    no_change = int(np.sum(diff == 0))
    results['direction'] = {'improved': improved, 'worsened': worsened, 'no_change': no_change}
    report(f"Direction: {improved} improved, {worsened} worsened, {no_change} no change")

    return results


# ============================================================================
# Q5: TOTAL LEARNING [PRIMARY] - Full learning magnitude across experiment
# ============================================================================
# Comparison: Blind Prior vs Trial 2 (within-subject, one-tailed).
# Primary outcome: captures the complete learning trajectory.
# Reports: permutation test, Wilcoxon, Cliff's delta, bootstrap CI,
#   percent improvement, T2 vs uniform benchmark, perfect learner count.

def analyze_total_learning(df, summary_df):
    """Q5 [PRIMARY]: Blind -> T2 total learning with full statistics."""
    report("\n" + "=" * 70)
    report("Q5: TOTAL LEARNING (BLIND -> TRIAL 2) [PRIMARY]")
    report("=" * 70)

    results = {}
    blind_sad = summary_df['Blind_sad'].values
    t2_sad = summary_df['T2_sad'].values
    valid = ~(np.isnan(blind_sad) | np.isnan(t2_sad))
    blind_v, t2_v = blind_sad[valid], t2_sad[valid]

    if len(blind_v) < 2:
        report("Insufficient data"); return results

    results['n_valid'] = len(blind_v)
    improvement = blind_v - t2_v

    report(f"\n--- Total Learning (n={len(blind_v)}) ---")
    report(f"Blind prior: M={np.mean(blind_v):.2f}, SD={safe_std(blind_v):.2f}")
    report(f"Trial 2:     M={np.mean(t2_v):.2f}, SD={safe_std(t2_v):.2f}")
    report(f"Improvement: M={np.mean(improvement):.2f}, SD={safe_std(improvement):.2f}")
    results['mean_improvement'] = np.mean(improvement)

    pct = (improvement / np.where(blind_v > 0, blind_v, np.nan)) * 100
    pct = pct[~np.isnan(pct) & ~np.isinf(pct)]
    results['pct_improvement'] = np.mean(pct) if len(pct) > 0 else np.nan
    report(f"Mean % change: M={np.mean(pct):.1f}%")

    # Direction counts
    n_improved = int(np.sum(improvement > 0))
    n_worsened = int(np.sum(improvement < 0))
    n_no_change = int(np.sum(improvement == 0))
    results['n_improved'] = n_improved
    results['n_worsened'] = n_worsened
    results['n_no_change'] = n_no_change
    report(f"Direction: {n_improved} improved, {n_worsened} worsened, {n_no_change} no change")

    report("\n--- Statistical Tests ---")
    obs, p = permutation_test_paired(blind_v, t2_v, alternative='greater')
    results['permutation_test'] = {'observed_diff': obs, 'p_value': p}
    report(f"Blind > T2 (one-tailed): diff={obs:.2f}, p={p:.4f} {interpret_p_value(p)}")

    nonzero = improvement[improvement != 0]
    if len(nonzero) > 0:
        w, wp = stats.wilcoxon(blind_v, t2_v, alternative='greater')
        results['wilcoxon_test'] = {'statistic': w, 'p_value': wp}
        report(f"Wilcoxon signed-rank: W={w:.1f}, p={wp:.4f} {interpret_p_value(wp)}")

    d = cliffs_delta(blind_v, t2_v)
    results['cliffs_delta'] = d
    report(f"Cliff's delta: {d:.3f} ({interpret_cliffs_delta(d)})")

    # Bootstrap CI for improvement
    _, ci_low, ci_high = bootstrap_ci(improvement)
    results['improvement_ci'] = (ci_low, ci_high)
    report(f"95% Bootstrap CI for improvement: [{ci_low:.2f}, {ci_high:.2f}]")

    # Benchmarks
    report("\n--- Benchmarks ---")
    t2_diff, t2_p = permutation_test_one_sample(t2_v, null_value=UNIFORM_SAD, alternative='less')
    results['t2_vs_uniform'] = {'mean_diff': t2_diff, 'p_value': t2_p}
    report(f"T2 < Uniform (SAD=8): diff={t2_diff:.2f}, p={t2_p:.4f} {interpret_p_value(t2_p)}")

    perfect = int(np.sum(t2_v == 0))
    results['perfect_learners'] = perfect
    report(f"Perfect final (SAD=0): {perfect} ({100 * perfect / len(t2_v):.1f}%)")

    # Full trajectory
    report("\n--- Full Trajectory ---")
    for prefix, label in [('Blind', 'Blind'), ('Icon', 'Icon'), ('T1', 'Trial 1'), ('T2', 'Trial 2')]:
        col = f'{prefix}_sad'
        if col in summary_df.columns:
            vals = summary_df[col].dropna()
            report(f"  {label}: M={vals.mean():.2f} (SD={safe_std(vals):.2f})")

    return results


# ============================================================================
# Q_icon_t2: ICON -> TRIAL 2 - Learning from two exposures relative to icon prior
# ============================================================================
# Mirrors Q5 (analyze_total_learning) but uses the Icon prior as the baseline
# instead of the Blind prior, isolating the gain attributable to the two array
# exposures + feedback (over and above the icon-shape information).

def analyze_icon_vs_t2(df, summary_df):
    """Q_icon_t2: Icon -> T2 exposure learning with full statistics (two-tailed)."""
    report("\n" + "=" * 70)
    report("ICON vs T2 (EXPOSURE LEARNING)")
    report("=" * 70)

    results = {}
    icon_sad = summary_df['Icon_sad'].values
    t2_sad = summary_df['T2_sad'].values
    valid = ~(np.isnan(icon_sad) | np.isnan(t2_sad))
    icon_v, t2_v = icon_sad[valid], t2_sad[valid]

    if len(icon_v) < 2:
        report("Insufficient data"); return results

    results['n_valid'] = len(icon_v)
    improvement = icon_v - t2_v

    report(f"\n--- Exposure Learning (n={len(icon_v)}) ---")
    report(f"Icon prior: M={np.mean(icon_v):.2f}, SD={safe_std(icon_v):.2f}")
    report(f"Trial 2:    M={np.mean(t2_v):.2f}, SD={safe_std(t2_v):.2f}")
    report(f"Improvement: M={np.mean(improvement):.2f}, SD={safe_std(improvement):.2f}")
    results['mean_improvement'] = np.mean(improvement)

    pct = (improvement / np.where(icon_v > 0, icon_v, np.nan)) * 100
    pct = pct[~np.isnan(pct) & ~np.isinf(pct)]
    results['pct_improvement'] = np.mean(pct) if len(pct) > 0 else np.nan
    report(f"Mean % change: M={np.mean(pct):.1f}%")

    # Direction counts (improved = T2 < Icon)
    n_improved = int(np.sum(improvement > 0))
    n_worsened = int(np.sum(improvement < 0))
    n_no_change = int(np.sum(improvement == 0))
    results['n_improved'] = n_improved
    results['n_worsened'] = n_worsened
    results['n_no_change'] = n_no_change
    report(f"Direction: {n_improved} improved, {n_worsened} worsened, {n_no_change} no change")

    report("\n--- Statistical Tests ---")
    obs, p = permutation_test_paired(icon_v, t2_v, alternative='two-sided')
    results['permutation_test'] = {'observed_diff': obs, 'p_value': p}
    report(f"Icon vs T2 (two-tailed): diff={obs:.2f}, p={p:.4f} {interpret_p_value(p)}")

    nonzero = improvement[improvement != 0]
    if len(nonzero) > 0:
        w, wp = stats.wilcoxon(icon_v, t2_v)
        results['wilcoxon_test'] = {'statistic': w, 'p_value': wp}
        report(f"Wilcoxon signed-rank: W={w:.1f}, p={wp:.4f} {interpret_p_value(wp)}")

    d = cliffs_delta(icon_v, t2_v)
    results['cliffs_delta'] = d
    report(f"Cliff's delta: {d:.3f} ({interpret_cliffs_delta(d)})")

    # Bootstrap CI for improvement
    _, ci_low, ci_high = bootstrap_ci(improvement)
    results['improvement_ci'] = (ci_low, ci_high)
    report(f"95% Bootstrap CI for improvement: [{ci_low:.2f}, {ci_high:.2f}]")

    return results


# ============================================================================
# Q6: ITEM-SPECIFIC LEARNING - Which items are learned better?
# ============================================================================
# Analyses per-item absolute errors across phases.
# Groups items by role: dominant(6), medium(4), rare(1).
# Tests dominant vs rare via Mann-Whitney U (prediction: dominant < rare error).
# Bias analysis: systematic over/underestimation direction per item per phase.

def analyze_item_learning(df, summary_df):
    """Q6: Item-specific error by role + dominant vs rare comparison."""
    report("\n" + "=" * 70)
    report("Q6: ITEM-SPECIFIC LEARNING")
    report("=" * 70)

    results = {'by_phase': {}, 'by_role': {}}

    report(f"\n--- Item Estimates by Phase ---")
    report(f"True distribution: {TRUE_DISTRIBUTION}")

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_LABELS[phase]
        if len(phase_df) == 0:
            continue

        mean_est = [phase_df[f'gen_est_item{i}'].mean() for i in range(1, 5)]
        abs_errors = [np.abs(phase_df[f'gen_est_item{i}'] - TRUE_DISTRIBUTION[i - 1]).mean()
                      for i in range(1, 5)]
        results['by_phase'][phase] = {'mean_estimates': mean_est, 'mean_abs_errors': abs_errors}
        report(f"\n{label}:")
        report(f"  Estimates: [{mean_est[0]:.2f}, {mean_est[1]:.2f}, {mean_est[2]:.2f}, {mean_est[3]:.2f}]")
        report(f"  Abs errors: [{abs_errors[0]:.2f}, {abs_errors[1]:.2f}, {abs_errors[2]:.2f}, {abs_errors[3]:.2f}]")

    # By role (T2)
    report("\n--- Learning by Item Role (Trial 2) ---")
    t2_df = df[df['trial_type'] == 'exposure_gen_2'].copy()
    if len(t2_df) > 0:
        role_errors = {'dominant': [], 'medium': [], 'rare': []}
        for _, row in t2_df.iterrows():
            for i in range(1, 5):
                true_count = TRUE_DISTRIBUTION[i - 1]
                est = row[f'gen_est_item{i}']
                if not pd.isna(est):
                    error = abs(est - true_count)
                    if true_count == 6: role_errors['dominant'].append(error)
                    elif true_count == 4: role_errors['medium'].append(error)
                    else: role_errors['rare'].append(error)

        for role in ['dominant', 'medium', 'rare']:
            errors = [e for e in role_errors[role] if not np.isnan(e)]
            if errors:
                results['by_role'][role] = {
                    'mean_error': np.mean(errors), 'sd_error': safe_std(pd.Series(errors)),
                    'n': len(errors)
                }
                report(f"{role.capitalize()}: M={np.mean(errors):.2f} (SD={safe_std(pd.Series(errors)):.2f}, n={len(errors)})")

        # Dom vs Rare comparison
        dom_err = [e for e in role_errors['dominant'] if not np.isnan(e)]
        rare_err = [e for e in role_errors['rare'] if not np.isnan(e)]
        if len(dom_err) > 1 and len(rare_err) > 1:
            report("\n--- Dominant vs Rare ---")
            u, up = stats.mannwhitneyu(dom_err, rare_err, alternative='less')
            d = cliffs_delta(rare_err, dom_err)
            results['dom_vs_rare'] = {'statistic': u, 'p_value': up, 'cliffs_delta': d}
            report(f"Dom < Rare errors: U={u:.1f}, p={up:.4f} {interpret_p_value(up)}")
            report(f"Cliff's delta (rare - dom): {d:.3f} ({interpret_cliffs_delta(d)})")

    # Bias analysis
    report("\n--- Bias (Mean estimate - True) ---")
    for phase in ['blind_prior', 'exposure_gen_2']:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_LABELS.get(phase, phase)
        if len(phase_df) == 0:
            continue
        biases = [(phase_df[f'gen_est_item{i}'] - TRUE_DISTRIBUTION[i - 1]).mean() for i in range(1, 5)]
        results[f'{phase}_bias'] = biases
        report(f"{label}: [{biases[0]:+.2f}, {biases[1]:+.2f}, {biases[2]:+.2f}, {biases[3]:+.2f}]")

    return results


# ============================================================================
# EXACT MULTINOMIAL LOG-PROBABILITY ANALYSIS (v19)
# ============================================================================
# Computes log P(sorted_response | model) for each participant in each phase.
# Models: Uniform [.25,.25,.25,.25] and True [1/12,1/12,4/12,6/12].
# Sorted responses avoid the blind-phase position assignment problem.
# Tracks whether log-probability under the true model increases across phases.

def _multinomial_log_prob(response_sorted, probs_sorted):
    """Compute log P(response | Multinomial(12, probs)) for sorted vectors."""
    from math import lgamma, log
    n = sum(response_sorted)
    log_p = lgamma(n + 1)
    for x, p in zip(response_sorted, probs_sorted):
        if x > 0 and p > 0:
            log_p += x * log(p) - lgamma(x + 1)
        elif x > 0 and p == 0:
            return -np.inf  # impossible outcome
        else:
            log_p -= lgamma(x + 1)
    return log_p


def analyze_multinomial_probability(df, summary_df):
    """Compute exact multinomial log-probabilities under uniform and true models."""
    report("\n" + "=" * 70)
    report("MULTINOMIAL LOG-PROBABILITY ANALYSIS")
    report("=" * 70)

    results = {}

    true_probs_sorted = sorted([1/12, 1/12, 4/12, 6/12])  # [1/12, 1/12, 1/3, 1/2]
    uniform_probs = [0.25, 0.25, 0.25, 0.25]

    # Compute log-probs per participant per phase
    phase_log_true = {p: [] for p in PHASE_ORDER}
    phase_log_uniform = {p: [] for p in PHASE_ORDER}
    phase_log_ratio = {p: [] for p in PHASE_ORDER}  # log(P_true / P_uniform)

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        for _, row in phase_df.iterrows():
            ests = [row.get(f'gen_est_item{i}', np.nan) for i in range(1, 5)]
            if any(pd.isna(e) for e in ests):
                continue
            ests_sorted = sorted([int(e) for e in ests])

            lp_true = _multinomial_log_prob(ests_sorted, true_probs_sorted)
            lp_uniform = _multinomial_log_prob(ests_sorted, uniform_probs)
            lr = lp_true - lp_uniform  # positive = more likely under true

            phase_log_true[phase].append(lp_true)
            phase_log_uniform[phase].append(lp_uniform)
            phase_log_ratio[phase].append(lr)

    # Report descriptives
    report(f"\n  Log-probability under TRUE model [1/12, 1/12, 4/12, 6/12] (sorted):")
    report(f"  {'Phase':<8} {'N':>4} {'Mean':>8} {'SD':>8} {'Mdn':>8}")
    report(f"  " + "-" * 40)
    for phase in PHASE_ORDER:
        vals = phase_log_true[phase]
        if vals:
            report(f"  {PHASE_SHORT[phase]:<8} {len(vals):>4} {np.mean(vals):>8.3f} {np.std(vals):>8.3f} {np.median(vals):>8.3f}")

    report(f"\n  Log-probability under UNIFORM model [.25, .25, .25, .25]:")
    report(f"  {'Phase':<8} {'N':>4} {'Mean':>8} {'SD':>8} {'Mdn':>8}")
    report(f"  " + "-" * 40)
    for phase in PHASE_ORDER:
        vals = phase_log_uniform[phase]
        if vals:
            report(f"  {PHASE_SHORT[phase]:<8} {len(vals):>4} {np.mean(vals):>8.3f} {np.std(vals):>8.3f} {np.median(vals):>8.3f}")

    report(f"\n  Log-likelihood ratio (true - uniform, positive = closer to true):")
    report(f"  {'Phase':<8} {'N':>4} {'Mean':>8} {'SD':>8} {'Mdn':>8}")
    report(f"  " + "-" * 40)
    for phase in PHASE_ORDER:
        vals = phase_log_ratio[phase]
        if vals:
            report(f"  {PHASE_SHORT[phase]:<8} {len(vals):>4} {np.mean(vals):>8.3f} {np.std(vals):>8.3f} {np.median(vals):>8.3f}")

    results['phase_log_true'] = {p: np.array(v) for p, v in phase_log_true.items()}
    results['phase_log_uniform'] = {p: np.array(v) for p, v in phase_log_uniform.items()}
    results['phase_log_ratio'] = {p: np.array(v) for p, v in phase_log_ratio.items()}

    # ---- Friedman on log P(true) across 4 phases ----
    report(f"\n  --- Tests on log P(response | true) across phases ---")
    lp_matrix = []
    for _, row in summary_df.iterrows():
        vals = []
        for prefix, phase in zip(['Blind', 'Icon', 'T1', 'T2'], PHASE_ORDER):
            ests = [row.get(f'{prefix}_est{i}', np.nan) for i in range(1, 5)]
            if any(pd.isna(e) for e in ests):
                vals.append(np.nan)
            else:
                ests_sorted = sorted([int(e) for e in ests])
                vals.append(_multinomial_log_prob(ests_sorted, true_probs_sorted))
        lp_matrix.append(vals)
    lp_matrix = np.array(lp_matrix)
    valid = lp_matrix[~np.any(np.isnan(lp_matrix), axis=1)]

    if valid.shape[0] >= 3:
        chi2_lp, p_lp = stats.friedmanchisquare(*[valid[:, i] for i in range(4)])
        results['friedman_log_true'] = {'statistic': chi2_lp, 'p_value': p_lp, 'n': valid.shape[0]}
        report(f"  Friedman on log P(true): chi2(3) = {chi2_lp:.3f}, p = {p_lp:.4f} {interpret_p_value(p_lp)}")

        # Pairwise comparisons
        report(f"\n  Pairwise Wilcoxon on log P(true) (Bonferroni, 6 tests, alpha=0.0083):")
        pairs = [('Blind', 'Icon', 0, 1), ('Blind', 'T1', 0, 2), ('Blind', 'T2', 0, 3),
                 ('Icon', 'T1', 1, 2), ('Icon', 'T2', 1, 3), ('T1', 'T2', 2, 3)]
        results['pairwise_log_true'] = {}
        for label_a, label_b, i, j in pairs:
            a, b = valid[:, i], valid[:, j]
            diffs = b - a
            non_zero = diffs[diffs != 0]
            if len(non_zero) >= 1:
                try:
                    w, p = stats.wilcoxon(a, b)
                except ValueError:
                    w, p = np.nan, np.nan
            else:
                w, p = 0, 1.0
            p_bonf = min(p * 6, 1.0)
            mean_diff = np.mean(b - a)
            sig = '***' if p_bonf < 0.001 else '**' if p_bonf < 0.01 else '*' if p_bonf < 0.05 else 'n.s.'
            results['pairwise_log_true'][f'{label_a}_vs_{label_b}'] = {
                'w': w, 'p_raw': p, 'p_bonf': p_bonf, 'mean_diff': mean_diff
            }
            report(f"    {label_a:>5} vs {label_b:<5}: diff = {mean_diff:+.3f}, W = {w:.1f}, "
                   f"p_raw = {p:.4f}, p_bonf = {p_bonf:.4f} {sig}")
    else:
        report(f"  Insufficient data (n={valid.shape[0]})")

    # ---- Friedman on log-likelihood ratio across 4 phases ----
    report(f"\n  --- Tests on log-likelihood ratio (true/uniform) across phases ---")
    lr_matrix = []
    for _, row in summary_df.iterrows():
        vals = []
        for prefix in ['Blind', 'Icon', 'T1', 'T2']:
            ests = [row.get(f'{prefix}_est{i}', np.nan) for i in range(1, 5)]
            if any(pd.isna(e) for e in ests):
                vals.append(np.nan)
            else:
                ests_sorted = sorted([int(e) for e in ests])
                lp_t = _multinomial_log_prob(ests_sorted, true_probs_sorted)
                lp_u = _multinomial_log_prob(ests_sorted, uniform_probs)
                vals.append(lp_t - lp_u)
        lr_matrix.append(vals)
    lr_matrix = np.array(lr_matrix)
    valid_lr = lr_matrix[~np.any(np.isnan(lr_matrix), axis=1)]

    if valid_lr.shape[0] >= 3:
        chi2_lr, p_lr = stats.friedmanchisquare(*[valid_lr[:, i] for i in range(4)])
        results['friedman_log_ratio'] = {'statistic': chi2_lr, 'p_value': p_lr, 'n': valid_lr.shape[0]}
        report(f"  Friedman on LR: chi2(3) = {chi2_lr:.3f}, p = {p_lr:.4f} {interpret_p_value(p_lr)}")

        phase_means = [np.mean(valid_lr[:, i]) for i in range(4)]
        report(f"  LR means: Blind={phase_means[0]:.3f}, Icon={phase_means[1]:.3f}, "
               f"T1={phase_means[2]:.3f}, T2={phase_means[3]:.3f}")
        results['lr_phase_means'] = phase_means
    else:
        report(f"  Insufficient data (n={valid_lr.shape[0]})")

    return results


# ============================================================================
# EXACT DISTRIBUTION ANALYSIS & 34-DISTRIBUTION SPACE (v22)
# ============================================================================
# Enumerates all 34 possible sorted distributions of 12 across 4 items.
# Tests exact distribution counts per phase using binomial tests.
# Creates colored histogram of distribution space.

def _enumerate_all_34():
    """Enumerate all sorted distributions [a,b,c,d] where a<=b<=c<=d and sum=12."""
    all_sorted = []
    for a in range(13):
        for b in range(a, 13):
            for c in range(b, 13):
                d = 12 - a - b - c
                if d >= c and d >= 0:
                    all_sorted.append((a, b, c, d))
    return all_sorted


def _classify_distribution(resp_sorted):
    """Classify a sorted distribution using 5-reference SAD + chi-sq tiebreaker."""
    def _sad(a, b): return sum(abs(x - y) for x, y in zip(a, b))
    def _chi2(obs, exp): return sum((o - e) ** 2 / max(e, 0.5) for o, e in zip(obs, exp))

    sad_scores = {name: _sad(resp_sorted, ref) for name, ref in REFERENCE_DISTRIBUTIONS.items()}
    min_sad = min(sad_scores.values())
    tied = [n for n, s in sad_scores.items() if s == min_sad]

    if len(tied) == 1:
        return tied[0]
    chi2_scores = {n: _chi2(resp_sorted, REFERENCE_DISTRIBUTIONS[n]) for n in tied}
    min_chi2 = min(chi2_scores.values())
    chi2_winners = [n for n, s in chi2_scores.items() if abs(s - min_chi2) < 1e-10]
    return chi2_winners[0] if len(chi2_winners) == 1 else 'Mixed'


def _multinomial_prob_sorted(resp_sorted, probs=[0.25, 0.25, 0.25, 0.25]):
    """P(sorted response) under Multinomial(12, probs). Accounts for permutations."""
    from math import factorial as fac
    from collections import Counter
    n = sum(resp_sorted)
    counts = Counter(resp_sorted)
    n_perms = fac(4)
    for v in counts.values():
        n_perms //= fac(v)
    coeff = fac(n)
    for x in resp_sorted:
        coeff //= fac(x)
    p_sorted = sorted(probs)
    prob = coeff
    for x, p in zip(resp_sorted, p_sorted):
        prob *= p ** x
    return n_perms * prob


def analyze_distribution_space(df, summary_df):
    """Analyze exact distribution counts against the 34-distribution space."""
    report("\n" + "=" * 70)
    report("EXACT DISTRIBUTION SPACE ANALYSIS (34 distributions)")
    report("=" * 70)

    results = {}

    # Enumerate and classify all 34
    all_34 = _enumerate_all_34()
    dist_info = {}
    for d in all_34:
        cls = _classify_distribution(d)
        prob = _multinomial_prob_sorted(d)
        dist_info[d] = {'class': cls, 'prob': prob}

    results['all_34'] = dist_info

    # Count observed distributions per phase
    report(f"\n  Observed exact distributions per phase:")
    results['phase_counts'] = {}

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        dist_counts = {}
        for _, row in phase_df.iterrows():
            ests = [row.get(f'gen_est_item{i}', np.nan) for i in range(1, 5)]
            if any(pd.isna(e) for e in ests):
                continue
            key = tuple(sorted([int(e) for e in ests]))
            dist_counts[key] = dist_counts.get(key, 0) + 1
        results['phase_counts'][phase] = dist_counts

    # Report key distributions
    n_total = len(summary_df)
    key_dists = [
        ((3, 3, 3, 3), 'Exact uniform'),
        ((1, 1, 4, 6), 'Exact true distribution'),
        ((1, 2, 3, 6), 'Unimodal-mild reference'),
    ]

    report(f"\n  Key exact distributions across phases (N={n_total}):")
    report(f"  {'Distribution':<18} {'Label':<25} {'Blind':>6} {'Icon':>6} {'T1':>6} {'T2':>6} {'P(null)':>8}")
    report(f"  " + "-" * 78)

    results['key_dist_tests'] = {}
    for dist, label in key_dists:
        p_null = dist_info.get(dist, {}).get('prob', 0)
        counts = []
        for phase in PHASE_ORDER:
            c = results['phase_counts'].get(phase, {}).get(dist, 0)
            counts.append(c)
        report(f"  {str(list(dist)):<18} {label:<25} {counts[0]:>6} {counts[1]:>6} "
               f"{counts[2]:>6} {counts[3]:>6} {p_null:>7.4f}")

        # Binomial test per phase
        results['key_dist_tests'][dist] = {'label': label, 'p_null': p_null, 'phase_counts': counts}
        for i, (phase, count) in enumerate(zip(PHASE_ORDER, counts)):
            if n_total > 0 and p_null > 0:
                p_binom = 1 - stats.binom.cdf(count - 1, n_total, p_null) if count > 0 else 1.0
                results['key_dist_tests'][dist][PHASE_SHORT[phase]] = {
                    'count': count, 'p_binom': p_binom
                }

    # Binomial test report for key distributions
    report(f"\n  Binomial tests (is observed count > null expectation?):")
    for dist, label in key_dists:
        p_null = dist_info.get(dist, {}).get('prob', 0)
        expected = n_total * p_null
        report(f"\n    {label} {list(dist)} (P_null={p_null:.4f}, expected={expected:.1f}):")
        for phase in PHASE_ORDER:
            c = results['phase_counts'].get(phase, {}).get(dist, 0)
            if n_total > 0 and p_null > 0:
                p_binom = 1 - stats.binom.cdf(c - 1, n_total, p_null) if c > 0 else 1.0
                sig = '***' if p_binom < 0.001 else '**' if p_binom < 0.01 else '*' if p_binom < 0.05 else 'n.s.'
                report(f"      {PHASE_SHORT[phase]}: {c}/{n_total}, p(X>={c}) = {p_binom:.4f} {sig}")

    # Cochran's Q: does exact [3,3,3,3] count change across phases?
    report(f"\n  Cochran's Q: does exact [3,3,3,3] rate change across phases?")
    uniform_binary = []
    for _, row in summary_df.iterrows():
        vals = []
        for prefix in ['Blind', 'Icon', 'T1', 'T2']:
            ests = [row.get(f'{prefix}_est{i}', np.nan) for i in range(1, 5)]
            if any(pd.isna(e) for e in ests):
                vals.append(np.nan)
            else:
                vals.append(1 if tuple(sorted([int(e) for e in ests])) == (3, 3, 3, 3) else 0)
        uniform_binary.append(vals)
    ub = np.array(uniform_binary)
    valid_ub = ub[~np.any(np.isnan(ub), axis=1)].astype(int)
    if valid_ub.shape[0] >= 3 and valid_ub.sum() > 0:
        k = 4; T = valid_ub.sum(); Cj = valid_ub.sum(axis=0); Ri = valid_ub.sum(axis=1)
        numer = (k - 1) * (k * np.sum(Cj ** 2) - T ** 2)
        denom = k * T - np.sum(Ri ** 2)
        if denom > 0:
            Q = numer / denom
            p_q = 1 - stats.chi2.cdf(Q, df=k - 1)
            results['uniform_exact_cochran'] = {'Q': Q, 'p_value': p_q}
            report(f"    Q = {Q:.3f}, p = {p_q:.4f} {interpret_p_value(p_q)}")

    return results


# ============================================================================
# VERSION B: PRIOR FINGERPRINT PERSISTENCE (v23)
# ============================================================================
# Does T1/T2 classification predict blind prior classification?
# If yes, the prior "fingerprint" persists into test phases.

def analyze_prior_fingerprint(df, summary_df):
    """Version B: Can T1/T2 responses predict blind prior classification?"""
    report("\n" + "=" * 70)
    report("PRIOR FINGERPRINT PERSISTENCE (Version B)")
    report("=" * 70)

    results = {}

    # Classify each participant in each phase
    phase_classes = {p: {} for p in PHASE_ORDER}
    for _, row in summary_df.iterrows():
        subj = row.get('subject_nr', row.name)
        for prefix, phase in zip(['Blind', 'Icon', 'T1', 'T2'], PHASE_ORDER):
            ests = [row.get(f'{prefix}_est{i}', np.nan) for i in range(1, 5)]
            if any(pd.isna(e) for e in ests):
                continue
            resp_sorted = tuple(sorted([int(e) for e in ests]))
            phase_classes[phase][subj] = _classify_distribution(resp_sorted)

    results['phase_classifications'] = phase_classes

    # Build confusion: blind class vs T1/T2 class
    blind_cls = phase_classes.get(PHASE_ORDER[0], {})
    if len(blind_cls) < 3:
        report("  Insufficient data for fingerprint analysis")
        return results

    for test_phase, test_label in [(PHASE_ORDER[2], 'T1'), (PHASE_ORDER[3], 'T2')]:
        test_cls = phase_classes.get(test_phase, {})
        common_subjs = set(blind_cls.keys()) & set(test_cls.keys())
        if len(common_subjs) < 3:
            continue

        # Agreement rate
        matches = sum(1 for s in common_subjs if blind_cls[s] == test_cls[s])
        agreement = 100 * matches / len(common_subjs)

        # Transition matrix
        from collections import Counter
        transitions = Counter((blind_cls[s], test_cls[s]) for s in common_subjs)

        # Persistence rate per category
        persistence = {}
        for cat in set(blind_cls[s] for s in common_subjs):
            n_cat = sum(1 for s in common_subjs if blind_cls[s] == cat)
            n_same = sum(1 for s in common_subjs if blind_cls[s] == cat and test_cls[s] == cat)
            persistence[cat] = 100 * n_same / n_cat if n_cat > 0 else 0

        results[f'agreement_{test_label}'] = {
            'rate': agreement, 'n': len(common_subjs), 'matches': matches
        }
        results[f'persistence_{test_label}'] = persistence
        results[f'transitions_{test_label}'] = dict(transitions)

        report(f"\n  Blind -> {test_label} (n={len(common_subjs)}):")
        report(f"    Overall agreement: {matches}/{len(common_subjs)} ({agreement:.0f}%)")
        report(f"    Persistence per category:")
        for cat, pct in sorted(persistence.items()):
            n_cat = sum(1 for s in common_subjs if blind_cls[s] == cat)
            report(f"      {cat}: {pct:.0f}% stayed (n={n_cat})")

    return results


# ============================================================================
# VERSION C: BAYESIAN COGNITIVE MODEL (v23)
# ============================================================================
# Model: Prior x Likelihood = Posterior
# P(prior_type | T2) proportional to P(T2 | prior_type) x P(prior_type)
# Uses multinomial probability of T2 response under each prior model.

def analyze_bayesian_model(df, summary_df):
    """Version C: Bayesian inference of prior type from T2 responses."""
    report("\n" + "=" * 70)
    report("BAYESIAN COGNITIVE MODEL (Version C)")
    report("=" * 70)

    results = {}

    # Define prior models as multinomial probabilities
    # Each prior type implies a different starting distribution
    prior_models = {
        'Uniform': [3/12, 3/12, 3/12, 3/12],       # [3,3,3,3] normalized
        'Unimodal-mild': [1/12, 2/12, 3/12, 6/12],  # [1,2,3,6] normalized
    }

    # Base rates from observed data
    blind_classes = {}
    for _, row in summary_df.iterrows():
        subj = row.get('subject_nr', row.name)
        ests = [row.get(f'Blind_est{i}', np.nan) for i in range(1, 5)]
        if any(pd.isna(e) for e in ests):
            continue
        blind_classes[subj] = _classify_distribution(tuple(sorted([int(e) for e in ests])))

    n_total = len(blind_classes)
    if n_total < 3:
        report("  Insufficient data for Bayesian model")
        return results

    base_rates = {}
    for model_name in prior_models:
        count = sum(1 for c in blind_classes.values() if c == model_name)
        base_rates[model_name] = count / n_total if n_total > 0 else 0.5
    # Ensure base rates sum to 1 for the modeled categories
    total_br = sum(base_rates.values())
    if total_br > 0:
        base_rates = {k: v / total_br for k, v in base_rates.items()}
    results['base_rates'] = base_rates
    report(f"  Base rates: {', '.join(f'{k}: {v:.2f}' for k, v in base_rates.items())}")

    # For each participant's T2 response, compute posterior P(prior_type | T2)
    report(f"\n  Bayesian posterior P(prior_type | T2):")
    posteriors = []
    for _, row in summary_df.iterrows():
        subj = row.get('subject_nr', row.name)
        t2_ests = [row.get(f'T2_est{i}', np.nan) for i in range(1, 5)]
        if any(pd.isna(e) for e in t2_ests):
            continue
        t2_sorted = sorted([int(e) for e in t2_ests])

        # Compute likelihood P(T2 | prior_type) for each model
        likelihoods = {}
        for model_name, model_probs in prior_models.items():
            lp = _multinomial_log_prob(t2_sorted, sorted(model_probs))
            likelihoods[model_name] = np.exp(lp)

        # Posterior = likelihood * prior / evidence
        unnorm = {k: likelihoods[k] * base_rates.get(k, 0.5) for k in prior_models}
        evidence = sum(unnorm.values())
        if evidence > 0:
            posterior = {k: v / evidence for k, v in unnorm.items()}
        else:
            posterior = {k: 1 / len(prior_models) for k in prior_models}

        actual_blind = blind_classes.get(subj, 'Unknown')
        map_estimate = max(posterior, key=posterior.get)
        posteriors.append({
            'subject': subj, 'actual_blind': actual_blind,
            'map_estimate': map_estimate, 'posterior': posterior,
            't2_response': t2_sorted
        })

    results['posteriors'] = posteriors

    # Report accuracy
    if posteriors:
        # Only count participants whose blind class is in the model set
        modeled = [p for p in posteriors if p['actual_blind'] in prior_models]
        if modeled:
            correct = sum(1 for p in modeled if p['map_estimate'] == p['actual_blind'])
            accuracy = 100 * correct / len(modeled)
            results['map_accuracy'] = accuracy
            results['n_modeled'] = len(modeled)
            report(f"  MAP classification accuracy: {correct}/{len(modeled)} ({accuracy:.0f}%)")
            report(f"  (Only participants with Uniform or Unimodal-mild blind prior)")

            for p in posteriors:
                p_uniform = p['posterior'].get('Uniform', 0)
                p_unimodal = p['posterior'].get('Unimodal-mild', 0)
                match = 'Y' if p['map_estimate'] == p['actual_blind'] else 'N'
                report(f"    S{p['subject']}: T2={p['t2_response']} "
                       f"P(Uni)={p_uniform:.2f} P(UM)={p_unimodal:.2f} "
                       f"MAP={p['map_estimate']} Actual={p['actual_blind']} [{match}]")

    return results


# ============================================================================
# VERSION D: PRIOR TYPE PREDICTS LEARNING (v23)
# ============================================================================
# Do participants classified as Uniform learn differently from Unimodal-mild?

def analyze_prior_predicts_learning(df, summary_df):
    """Version D: Does blind prior classification predict learning trajectory?"""
    report("\n" + "=" * 70)
    report("PRIOR TYPE PREDICTS LEARNING (Version D)")
    report("=" * 70)

    results = {}

    # Classify blind prior
    blind_classes = {}
    for _, row in summary_df.iterrows():
        subj = row.get('subject_nr', row.name)
        ests = [row.get(f'Blind_est{i}', np.nan) for i in range(1, 5)]
        if any(pd.isna(e) for e in ests):
            continue
        blind_classes[subj] = _classify_distribution(tuple(sorted([int(e) for e in ests])))

    # Split by Uniform vs Unimodal-mild
    uniform_subjs = [s for s, c in blind_classes.items() if c == 'Uniform']
    unimodal_subjs = [s for s, c in blind_classes.items() if c == 'Unimodal-mild']
    results['n_uniform'] = len(uniform_subjs)
    results['n_unimodal'] = len(unimodal_subjs)
    report(f"  Uniform prior: n={len(uniform_subjs)}")
    report(f"  Unimodal-mild prior: n={len(unimodal_subjs)}")

    if len(uniform_subjs) < 2 or len(unimodal_subjs) < 2:
        report("  Insufficient data for group comparison")
        return results

    # Get SAD trajectories per group
    for phase_label, prefix in [('Blind', 'Blind'), ('Icon', 'Icon'), ('T1', 'T1'), ('T2', 'T2')]:
        uni_sads = []
        um_sads = []
        for _, row in summary_df.iterrows():
            subj = row.get('subject_nr', row.name)
            sad_val = row.get(f'{prefix}_SAD', np.nan)
            if np.isnan(sad_val):
                continue
            if subj in uniform_subjs:
                uni_sads.append(sad_val)
            elif subj in unimodal_subjs:
                um_sads.append(sad_val)

        results[f'{phase_label}_uniform_sad'] = uni_sads
        results[f'{phase_label}_unimodal_sad'] = um_sads

        if uni_sads and um_sads:
            report(f"\n  {phase_label}: Uniform M={np.mean(uni_sads):.2f} (n={len(uni_sads)}), "
                   f"Unimodal-mild M={np.mean(um_sads):.2f} (n={len(um_sads)})")

    # Mann-Whitney: T2 SAD between groups
    t2_uni = results.get('T2_uniform_sad', [])
    t2_um = results.get('T2_unimodal_sad', [])
    if len(t2_uni) >= 2 and len(t2_um) >= 2:
        u, p = stats.mannwhitneyu(t2_uni, t2_um, alternative='two-sided')
        # Cliff's delta
        n1, n2 = len(t2_uni), len(t2_um)
        d = (2 * u / (n1 * n2)) - 1
        results['t2_mannwhitney'] = {'statistic': u, 'p_value': p, 'cliffs_delta': d}
        report(f"\n  Mann-Whitney (T2 SAD): U={u:.1f}, p={p:.4f} {interpret_p_value(p)}, d={d:.3f}")
        report(f"    Uniform T2 SAD: M={np.mean(t2_uni):.2f}")
        report(f"    Unimodal-mild T2 SAD: M={np.mean(t2_um):.2f}")

    # Learning magnitude: Blind SAD - T2 SAD per group
    blind_uni = results.get('Blind_uniform_sad', [])
    blind_um = results.get('Blind_unimodal_sad', [])
    if blind_uni and t2_uni and blind_um and t2_um:
        learn_uni = [b - t for b, t in zip(blind_uni, t2_uni)]
        learn_um = [b - t for b, t in zip(blind_um, t2_um)]
        results['learning_uniform'] = learn_uni
        results['learning_unimodal'] = learn_um
        report(f"\n  Learning magnitude (Blind - T2 SAD):")
        report(f"    Uniform: M={np.mean(learn_uni):.2f}")
        report(f"    Unimodal-mild: M={np.mean(learn_um):.2f}")

        if len(learn_uni) >= 2 and len(learn_um) >= 2:
            u2, p2 = stats.mannwhitneyu(learn_uni, learn_um, alternative='two-sided')
            results['learning_mannwhitney'] = {'statistic': u2, 'p_value': p2}
            report(f"    Mann-Whitney (learning): U={u2:.1f}, p={p2:.4f} {interpret_p_value(p2)}")

    return results


def create_figure_distribution_space(df, summary_df, results, save_path=None):
    """Figure 9: Distribution space, exact counts, null histogram, classification proportions (2x2)."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Figure 9: Distribution Space & Classification Under Null', fontsize=13, fontweight='bold')

    dist_info = results.get('dist_space', {}).get('all_34', {})
    if not dist_info:
        plt.close(fig)
        return fig

    sorted_dists = sorted(dist_info.items(), key=lambda x: -x[1]['prob'])
    labels = [str(list(d)) for d, _ in sorted_dists]
    probs = [info['prob'] for _, info in sorted_dists]
    classes = [info['class'] for _, info in sorted_dists]

    from matplotlib.patches import Patch
    cat_order = ['Uniform', 'Unimodal-mild', 'J-shaped (True)', 'Bimodal-symmetric', 'Unimodal-extreme', 'Mixed']

    # ---- 9.1: Probability bars colored by classification ----
    ax = axes[0, 0]
    colors = [SHAPE_COLORS.get(c, '#9E9E9E') for c in classes]
    ax.bar(range(len(labels)), [p * 100 for p in probs], color=colors,
           edgecolor='black', linewidth=0.3, alpha=0.85)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=5)
    ax.set_ylabel('P(distribution) under uniform [%]')
    ax.set_title('9.1 All 34 distributions by category')
    seen = set()
    legend_handles = []
    for c in classes:
        if c not in seen:
            seen.add(c)
            legend_handles.append(Patch(facecolor=SHAPE_COLORS.get(c, '#9E9E9E'), edgecolor='black', linewidth=0.5, label=c))
    ax.legend(handles=legend_handles, fontsize=5.5, loc='upper right')
    for i in range(min(3, len(labels))):
        ax.text(i, probs[i] * 100 + 0.3, f'{probs[i]*100:.1f}%', ha='center', fontsize=5.5, fontweight='bold')

    # ---- 9.2: Observed counts per phase ----
    ax = axes[0, 1]
    phase_counts = results.get('dist_space', {}).get('phase_counts', {})
    key_dists_plot = [(3, 3, 3, 3), (1, 1, 4, 6), (1, 2, 3, 6), (2, 3, 3, 4)]
    x = np.arange(4); w = 0.18
    dist_colors = ['#78909C', '#E53935', '#FB8C00', '#5C6BC0']
    for i, dist in enumerate(key_dists_plot):
        counts = [phase_counts.get(p, {}).get(dist, 0) for p in PHASE_ORDER]
        ax.bar(x + (i - 1.5) * w, counts, w, color=dist_colors[i],
               edgecolor='black', linewidth=0.5, alpha=0.85, label=str(list(dist)))
    ax.set_xticks(x); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('Number of participants')
    ax.set_title('9.2 Exact distribution counts per phase')
    ax.legend(fontsize=6, loc='upper left')
    for i, dist in enumerate(key_dists_plot):
        p_null = dist_info.get(dist, {}).get('prob', 0)
        expected = len(summary_df) * p_null
        if expected > 0:
            ax.axhline(y=expected, color=dist_colors[i], ls=':', lw=0.8, alpha=0.5)

    # ---- 9.3: Classification-colored null SAD histogram (reuses stored data) ----
    ax = axes[1, 0]
    cat_sads = results.get('q1', {}).get('null_individual_sads_by_cat', {})
    n_hist = sum(len(v) for v in cat_sads.values()) if cat_sads else 0
    if cat_sads and n_hist > 0:
        max_sad = max(max(v) for v in cat_sads.values() if v)
        bins = np.arange(0, max_sad + 3, 2) - 0.5
        cat_present = [c for c in cat_order if c in cat_sads]
        hist_data = [cat_sads.get(c, []) for c in cat_present]
        hist_colors = [SHAPE_COLORS.get(c, '#9E9E9E') for c in cat_present]
        ax.hist(hist_data, bins=bins, stacked=True, color=hist_colors, edgecolor='white',
                linewidth=0.3, alpha=0.85, label=cat_present)
        ut = results.get('q1', {}).get('uniform_test', {})
        obs_sad = ut.get('mean_diff')
        if obs_sad is not None:
            ax.axvline(x=obs_sad, color='#D32F2F', lw=2, ls='-', label=f'Observed mean ({obs_sad:.2f})')
        ax.set_xlabel('SAD from uniform (always even)')
        ax.set_ylabel('Count (simulated responses)')
        ax.set_title('9.3 Null SAD distribution by category')
        ax.legend(fontsize=5.5, loc='upper right')
        uniform_sads = cat_sads.get('Uniform', [])
        if uniform_sads:
            pct_u = 100 * len(uniform_sads) / n_hist
            ax.text(0.03, 0.95, f'Uniform: {pct_u:.1f}% of null\n(SAD 0-4 range)',
                transform=ax.transAxes, fontsize=6, va='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # ---- 9.4: Classification proportions - observed vs null ----
    ax = axes[1, 1]
    null_cc = results.get('q1', {}).get('null_class_counts', {})
    obs_cc = results.get('q1', {}).get('classification_counts', {})
    n_valid = sum(obs_cc.values()) if obs_cc else 1

    if null_cc and obs_cc:
        cat_plot = [c for c in cat_order if c in obs_cc or (c in null_cc and np.mean(null_cc.get(c, [0])) > 0.1)]
        if not cat_plot:
            cat_plot = list(obs_cc.keys())
        x_cats = np.arange(len(cat_plot))
        bar_w = 0.35
        null_pcts = [100 * np.mean(null_cc.get(c, np.zeros(1))) / n_valid for c in cat_plot]
        null_sds = [100 * np.std(null_cc.get(c, np.zeros(1))) / n_valid for c in cat_plot]
        cat_colors = [SHAPE_COLORS.get(c, '#9E9E9E') for c in cat_plot]

        # Null bars (lighter)
        ax.bar(x_cats - bar_w/2, null_pcts, bar_w, yerr=null_sds, color=cat_colors,
               alpha=0.35, edgecolor='black', linewidth=0.5, capsize=3, label='Null (simulation)')
        # Observed bars (solid)
        obs_pcts = [100 * obs_cc.get(c, 0) / n_valid for c in cat_plot]
        ax.bar(x_cats + bar_w/2, obs_pcts, bar_w, color=cat_colors,
               alpha=0.85, edgecolor='black', linewidth=0.5, label='Observed')
        # Annotate counts
        for i, (pct, c) in enumerate(zip(obs_pcts, cat_plot)):
            count = obs_cc.get(c, 0)
            if count > 0:
                ax.text(i + bar_w/2, pct + 1, f'{count}', ha='center', fontsize=7, fontweight='bold')
        # Significance stars
        cs = results.get('q1', {}).get('classification_significance', {})
        for i, c in enumerate(cat_plot):
            p_val = cs.get(c, {}).get('p_value')
            if p_val is not None and p_val < 0.05:
                sig = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*'
                y_max = max(obs_pcts[i], null_pcts[i]) + (null_sds[i] if i < len(null_sds) else 0)
                ax.text(i, y_max + 3, sig, ha='center', fontsize=10, fontweight='bold', color='#D32F2F')
        ax.set_xticks(x_cats)
        ax.set_xticklabels(cat_plot, fontsize=7, rotation=20, ha='right')
        ax.set_ylabel('% of participants')
        ax.legend(fontsize=7, loc='upper right')
    ax.set_title('9.4 Classification: Observed vs Null')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        report(f"Distribution space figure saved to: {save_path}")
    return fig



# ============================================================================
# EXACT MATCH ANALYSIS - How many participants hit exact item counts?
# ============================================================================
# Tracks % of participants who estimate the exact true count for each item,
# by phase. Important because:
#   - Exact match for 6 (dominant): requires noticing AND calibrating correctly
#   - Exact match for 1 (rare): easy by chance (1/13) but hard by observation
#   - Full distribution match (SAD=0): requires all 4 items correct simultaneously
# Reported per item, per role (dominant/medium/rare), and as full match rate.

def analyze_exact_matches(df, summary_df):
    """Exact match rates: % participants estimating exact true count, by phase."""
    report("\n" + "=" * 70)
    report("EXACT MATCH ANALYSIS")
    report("=" * 70)

    results = {'by_phase': {}, 'by_role': {}}
    item_labels = ['Item 1 (rare=1)', 'Item 2 (rare=1)', 'Item 3 (med=4)', 'Item 4 (dom=6)']

    report(f"\n--- Exact Match Rate by Phase (% of participants) ---")
    report(f"{'Phase':<8} {'Item1=1':>8} {'Item2=1':>8} {'Item3=4':>8} {'Item4=6':>8} {'All=SAD0':>9}")
    report("-" * 52)

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        n = len(phase_df)
        if n == 0:
            continue

        match_rates = []
        for i, true_val in enumerate(TRUE_DISTRIBUTION):
            col = f'gen_est_item{i + 1}'
            exact = (phase_df[col] == true_val).sum()
            rate = 100 * exact / n if n > 0 else 0
            match_rates.append(rate)

        # Full match (SAD=0)
        full_match = (phase_df['distance_from_true'] == 0).sum()
        full_rate = 100 * full_match / n if n > 0 else 0

        results['by_phase'][phase] = {
            'item_rates': match_rates,
            'full_match_rate': full_rate,
            'n': n
        }
        report(f"{label:<8} {match_rates[0]:>8.1f} {match_rates[1]:>8.1f} "
               f"{match_rates[2]:>8.1f} {match_rates[3]:>8.1f} {full_rate:>9.1f}")

    # By role (averaged across items of same role)
    report(f"\n--- Exact Match by Item Role ---")
    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        n = len(phase_df)
        if n == 0:
            continue

        dom_rate = 100 * (phase_df['gen_est_item4'] == 6).sum() / n
        med_rate = 100 * (phase_df['gen_est_item3'] == 4).sum() / n
        rare_rate = 100 * ((phase_df['gen_est_item1'] == 1).sum() +
                           (phase_df['gen_est_item2'] == 1).sum()) / (2 * n)

        results['by_role'][phase] = {
            'dominant': dom_rate, 'medium': med_rate, 'rare': rare_rate
        }
        report(f"  {label}: Dominant={dom_rate:.0f}%, Medium={med_rate:.0f}%, Rare={rare_rate:.0f}%")

    # ================================================================
    # POSITION-FREE COUNT MATCH (v12)
    # ================================================================
    # Checks whether the response CONTAINS specific count values anywhere,
    # regardless of which item position they occupy. This is valid in ALL
    # phases including blind (where item positions are meaningless).
    report(f"\n--- Position-Free Count Match (value present in response, any position) ---")
    report(f"{'Phase':<8} {'Has6':>6} {'Has4':>6} {'Has1':>6} {'Has1x2':>7} {'Sorted':>8} {'N':>4}")
    report("-" * 48)

    results['count_match'] = {}
    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        n = len(phase_df)
        if n == 0:
            continue

        has_6, has_4, has_1, has_1x2, full_sorted = 0, 0, 0, 0, 0
        for _, row in phase_df.iterrows():
            ests = [row.get(f'gen_est_item{i}', np.nan) for i in range(1, 5)]
            if any(pd.isna(e) for e in ests):
                continue
            ests_int = [int(e) for e in ests]

            if 6 in ests_int:
                has_6 += 1
            if 4 in ests_int:
                has_4 += 1
            count_1 = ests_int.count(1)
            if count_1 >= 1:
                has_1 += 1
            if count_1 >= 2:
                has_1x2 += 1
            if sorted(ests_int) == sorted(TRUE_DISTRIBUTION):
                full_sorted += 1

        pct_6 = 100 * has_6 / n
        pct_4 = 100 * has_4 / n
        pct_1 = 100 * has_1 / n
        pct_1x2 = 100 * has_1x2 / n
        pct_sorted = 100 * full_sorted / n

        results['count_match'][phase] = {
            'has_6': pct_6, 'has_4': pct_4, 'has_1': pct_1,
            'has_1x2': pct_1x2, 'full_sorted': pct_sorted, 'n': n,
            'raw_6': has_6, 'raw_4': has_4, 'raw_1': has_1,
            'raw_1x2': has_1x2, 'raw_sorted': full_sorted
        }
        report(f"{label:<8} {pct_6:>5.1f}% {pct_4:>5.1f}% {pct_1:>5.1f}% {pct_1x2:>6.1f}% {pct_sorted:>7.1f}% {n:>4}")

    # Cochran's Q on each count match across phases
    report(f"\n  Cochran's Q tests (position-free):")
    results['count_match_cochran'] = {}
    for count_label, count_val, min_count in [('Has 6', 6, 1), ('Has 4', 4, 1), ('Has 1', 1, 1), ('Has 1x2', 1, 2)]:
        binary_mat = []
        for _, row in summary_df.iterrows():
            brow = []
            for prefix in ['Blind', 'Icon', 'T1', 'T2']:
                ests = [row.get(f'{prefix}_est{i}', np.nan) for i in range(1, 5)]
                if any(pd.isna(e) for e in ests):
                    brow.append(np.nan)
                else:
                    ests_int = [int(e) for e in ests]
                    brow.append(1 if ests_int.count(count_val) >= min_count else 0)
            binary_mat.append(brow)
        bm = np.array(binary_mat)
        valid = bm[~np.any(np.isnan(bm), axis=1)].astype(int)
        if valid.shape[0] >= 3 and valid.sum() > 0:
            k = 4
            T = valid.sum()
            Cj = valid.sum(axis=0)
            Ri = valid.sum(axis=1)
            numer = (k - 1) * (k * np.sum(Cj ** 2) - T ** 2)
            denom = k * T - np.sum(Ri ** 2)
            if denom > 0:
                Q_stat = numer / denom
                p_q = 1 - stats.chi2.cdf(Q_stat, df=k - 1)
                results['count_match_cochran'][count_label] = {
                    'Q': Q_stat, 'p_value': p_q, 'n': valid.shape[0],
                    'phase_rates': [100 * Cj[i] / valid.shape[0] for i in range(4)]
                }
                report(f"    {count_label}: Q={Q_stat:.3f}, p={p_q:.4f} {interpret_p_value(p_q)}")

    return results


# ============================================================================
# TIMING ANALYSIS - RT, Completion Time, and Deliberation
# ============================================================================
# Three timing components decompose the generation task:
#   RT (first click)      = decision initiation, reflects confidence
#   Completion (total)    = full task duration including all 4 items
#   Deliberation (comp-RT)= execution/adjustment time after first decision
# Analyses: (a) Descriptives per phase (M, Mdn, SD, MAD).
#   (b) RT as proportion of completion (how much is "thinking" vs "doing").
#   (c) Within-phase RT-completion correlation (coupled or independent?).
#   (d) Timing-accuracy correlations (T2 and pooled across phases).
#   (e) Deliberation Blind vs T2 comparison (does execution speed up?).

def analyze_rt(df, summary_df):
    """Timing analysis: 3-component decomposition by phase + accuracy links."""
    report("\n" + "=" * 70)
    report("TIMING ANALYSIS (RT, Completion, Deliberation)")
    report("=" * 70)

    results = {'by_phase': {}}

    # --- Descriptives by phase: RT, Completion, Deliberation ---
    report("\n--- Timing by Phase ---")
    report(f"{'Phase':<8} {'RT M':>8} {'RT Mdn':>8} {'Comp M':>8} {'Comp Mdn':>9} "
           f"{'Delib M':>8} {'Delib Mdn':>10}  (all in seconds)")
    report("-" * 75)

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        phase_timing = {}

        # RT (first click)
        if 'gen_rt' in phase_df.columns:
            rt = phase_df['gen_rt'].dropna()
            if len(rt) > 0:
                phase_timing['rt'] = {
                    'mean': rt.mean(), 'sd': safe_std(rt),
                    'median': rt.median(), 'mad': safe_mad(rt),
                    'iqr': safe_iqr(rt)
                }

        # Completion time (total)
        if 'gen_completion_time' in phase_df.columns:
            comp = phase_df['gen_completion_time'].dropna()
            if len(comp) > 0:
                phase_timing['completion'] = {
                    'mean': comp.mean(), 'sd': safe_std(comp),
                    'median': comp.median(), 'mad': safe_mad(comp),
                    'iqr': safe_iqr(comp)
                }

        # Deliberation time (completion - RT)
        if 'deliberation_time' in phase_df.columns:
            delib = phase_df['deliberation_time'].dropna()
            if len(delib) > 0:
                phase_timing['deliberation'] = {
                    'mean': delib.mean(), 'sd': safe_std(delib),
                    'median': delib.median(), 'mad': safe_mad(delib),
                    'iqr': safe_iqr(delib)
                }

        results['by_phase'][phase] = phase_timing

        # Print formatted row (in seconds)
        r = phase_timing.get('rt', {})
        c = phase_timing.get('completion', {})
        d = phase_timing.get('deliberation', {})
        report(f"{label:<8} {r.get('mean', 0) / 1000:>8.1f} {r.get('median', 0) / 1000:>8.1f} "
               f"{c.get('mean', 0) / 1000:>8.1f} {c.get('median', 0) / 1000:>9.1f} "
               f"{d.get('mean', 0) / 1000:>8.1f} {d.get('median', 0) / 1000:>10.1f}")

    # --- Proportion: RT as fraction of completion time ---
    report("\n--- RT as Proportion of Completion Time ---")
    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        if 'gen_rt' in phase_df.columns and 'gen_completion_time' in phase_df.columns:
            rt = phase_df['gen_rt'].dropna()
            comp = phase_df.loc[rt.index, 'gen_completion_time'].dropna()
            valid_idx = rt.index.intersection(comp.index)
            if len(valid_idx) > 0:
                proportions = rt.loc[valid_idx] / comp.loc[valid_idx]
                proportions = proportions.replace([np.inf, -np.inf], np.nan).dropna()
                if len(proportions) > 0:
                    results['by_phase'][phase]['rt_proportion'] = {
                        'mean': proportions.mean(), 'sd': safe_std(proportions)
                    }
                    report(f"  {label}: RT/Completion = {proportions.mean():.1%} "
                           f"(SD={safe_std(proportions):.1%})")

    # --- Within-phase correlation: RT vs Completion Time ---
    report("\n--- RT vs Completion Time Correlation (within-phase) ---")
    results['rt_completion_corr'] = {}
    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        if 'gen_rt' in phase_df.columns and 'gen_completion_time' in phase_df.columns:
            rt = phase_df['gen_rt'].dropna()
            comp = phase_df.loc[rt.index, 'gen_completion_time'].dropna()
            valid_idx = rt.index.intersection(comp.index)
            if len(valid_idx) > 2:
                rho, p = stats.spearmanr(rt.loc[valid_idx], comp.loc[valid_idx])
                results['rt_completion_corr'][phase] = {'rho': rho, 'p_value': p}
                report(f"  {label}: rho={rho:.3f}, p={p:.4f} {interpret_p_value(p)}")

    # --- Timing vs Accuracy (Trial 2) ---
    report("\n--- Timing vs Accuracy (Trial 2) ---")
    t2 = df[df['trial_type'] == 'exposure_gen_2']

    for measure, label in [('gen_rt', 'RT'), ('gen_completion_time', 'Completion'),
                            ('deliberation_time', 'Deliberation')]:
        if measure in t2.columns and 'distance_from_true' in t2.columns:
            vals = t2[measure].dropna()
            sad = t2.loc[vals.index, 'distance_from_true'].dropna()
            valid_idx = vals.index.intersection(sad.index)
            if len(valid_idx) > 2:
                rho, p = stats.spearmanr(vals.loc[valid_idx], sad.loc[valid_idx])
                results[f'{measure}_accuracy'] = {'rho': rho, 'p_value': p}
                report(f"  {label} vs SAD: rho={rho:.3f}, p={p:.4f} {interpret_p_value(p)}")
            else:
                report(f"  {label} vs SAD: insufficient data (n={len(valid_idx)})")

    # --- Timing vs Accuracy (across all phases, pooled) ---
    report("\n--- Timing vs Accuracy (All Phases Pooled) ---")
    for measure, label in [('gen_rt', 'RT'), ('gen_completion_time', 'Completion'),
                            ('deliberation_time', 'Deliberation')]:
        if measure in df.columns and 'distance_from_true' in df.columns:
            vals = df[measure].dropna()
            sad = df.loc[vals.index, 'distance_from_true'].dropna()
            valid_idx = vals.index.intersection(sad.index)
            if len(valid_idx) > 2:
                rho, p = stats.spearmanr(vals.loc[valid_idx], sad.loc[valid_idx])
                results[f'{measure}_accuracy_pooled'] = {'rho': rho, 'p_value': p}
                report(f"  {label} vs SAD (pooled): rho={rho:.3f}, p={p:.4f} {interpret_p_value(p)}")

    # --- Deliberation time change across phases ---
    report("\n--- Deliberation Time Phase Comparison ---")
    if 'deliberation_time' in df.columns:
        # Blind vs T2 deliberation
        blind_delib = []
        t2_delib = []
        for subj in summary_df['subject_nr']:
            b = df[(df['subject_nr'] == subj) & (df['trial_type'] == 'blind_prior')]['deliberation_time'].values
            t = df[(df['subject_nr'] == subj) & (df['trial_type'] == 'exposure_gen_2')]['deliberation_time'].values
            if len(b) > 0 and len(t) > 0 and not np.isnan(b[0]) and not np.isnan(t[0]):
                blind_delib.append(b[0])
                t2_delib.append(t[0])

        if len(blind_delib) >= 2:
            blind_arr = np.array(blind_delib)
            t2_arr = np.array(t2_delib)
            diff = blind_arr - t2_arr
            obs, p = permutation_test_paired(blind_arr, t2_arr, alternative='greater')
            d = cliffs_delta(blind_arr, t2_arr)
            results['delib_blind_vs_t2'] = {
                'mean_diff': np.mean(diff), 'p_value': p, 'cliffs_delta': d,
                'blind_mean': np.mean(blind_arr), 't2_mean': np.mean(t2_arr)
            }
            report(f"  Blind delib: M={np.mean(blind_arr) / 1000:.1f}s, "
                   f"T2 delib: M={np.mean(t2_arr) / 1000:.1f}s")
            report(f"  Reduction: {np.mean(diff) / 1000:.1f}s, p={p:.4f} {interpret_p_value(p)}, "
                   f"d={d:.3f} ({interpret_cliffs_delta(d)})")

    # --- Friedman test on RT across 4 phases ---
    report("\n--- RT Friedman Test (4-phase) ---")
    rt_matrix = []
    for subj in summary_df['subject_nr']:
        row_vals = []
        for phase in PHASE_ORDER:
            vals = df[(df['subject_nr'] == subj) & (df['trial_type'] == phase)]['gen_rt'].values
            row_vals.append(vals[0] if len(vals) > 0 and not np.isnan(vals[0]) else np.nan)
        rt_matrix.append(row_vals)
    rt_matrix = np.array(rt_matrix)
    valid_rows = ~np.any(np.isnan(rt_matrix), axis=1)
    rt_valid = rt_matrix[valid_rows]

    if rt_valid.shape[0] >= 3:
        chi2, fp = stats.friedmanchisquare(*[rt_valid[:, i] for i in range(4)])
        results['rt_friedman'] = {'statistic': chi2, 'p_value': fp, 'n': rt_valid.shape[0]}
        report(f"  Friedman chi-square(3) = {chi2:.3f}, p = {fp:.4f} {interpret_p_value(fp)}")
        report(f"  N = {rt_valid.shape[0]}")

        # Post-hoc pairwise Wilcoxon (Bonferroni)
        report("\n--- RT Pairwise Wilcoxon (Bonferroni) ---")
        n_comp = 6
        rt_pairwise = []
        pairs = [(0,1,'Blind-Icon'), (0,2,'Blind-T1'), (0,3,'Blind-T2'),
                 (1,2,'Icon-T1'), (1,3,'Icon-T2'), (2,3,'T1-T2')]
        for i, j, label in pairs:
            x, y = rt_valid[:, i], rt_valid[:, j]
            nonzero = (x - y) != 0
            if np.sum(nonzero) > 0:
                w, wp = stats.wilcoxon(x, y)
                bp = min(wp * n_comp, 1.0)
            else:
                w, wp, bp = np.nan, np.nan, np.nan
            rt_pairwise.append({'comparison': label, 'W': w, 'p_bonf': bp, 'mean_diff': np.mean(x - y)})
            report(f"  {label:<12}: diff={np.mean(x-y)/1000:+.1f}s, W={w:.1f}, p_bonf={bp:.4f} {interpret_p_value(bp)}")
        results['rt_pairwise'] = rt_pairwise
    else:
        report(f"  Insufficient subjects with complete RT data (n={rt_valid.shape[0]})")

    # --- Completion time Friedman ---
    report("\n--- Completion Time Friedman Test ---")
    comp_matrix = []
    for subj in summary_df['subject_nr']:
        row_vals = []
        for phase in PHASE_ORDER:
            vals = df[(df['subject_nr'] == subj) & (df['trial_type'] == phase)]['gen_completion_time'].values
            row_vals.append(vals[0] if len(vals) > 0 and not np.isnan(vals[0]) else np.nan)
        comp_matrix.append(row_vals)
    comp_matrix = np.array(comp_matrix)
    valid_rows_c = ~np.any(np.isnan(comp_matrix), axis=1)
    comp_valid = comp_matrix[valid_rows_c]

    if comp_valid.shape[0] >= 3:
        chi2c, fpc = stats.friedmanchisquare(*[comp_valid[:, i] for i in range(4)])
        results['comp_friedman'] = {'statistic': chi2c, 'p_value': fpc, 'n': comp_valid.shape[0]}
        report(f"  Friedman chi-square(3) = {chi2c:.3f}, p = {fpc:.4f} {interpret_p_value(fpc)}")

    # --- RT Distribution Analysis: skewness, kurtosis, outlier detection ---
    report("\n--- RT Distribution Properties (Raw Data) ---")
    report(f"{'Phase':<8} {'Skew':>7} {'Kurt':>7} {'N':>4} {'M(s)':>7} {'SD(s)':>7} "
           f"{'Out':>4} {'Cl_M(s)':>8} {'Cl_SD(s)':>9}")
    report("-" * 75)
    results['rt_distribution'] = {}

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        rt_raw = phase_df['gen_rt'].dropna().values

        if len(rt_raw) < 2:
            continue

        # Raw descriptives
        raw_mean = np.mean(rt_raw)
        raw_sd = safe_std(pd.Series(rt_raw))

        # Skewness and kurtosis on raw data (before outlier removal)
        skewness = float(stats.skew(rt_raw, bias=False)) if len(rt_raw) >= 3 else np.nan
        kurtosis_val = float(stats.kurtosis(rt_raw, bias=False)) if len(rt_raw) >= 3 else np.nan

        # Outlier detection: 2.5 SD threshold per phase
        threshold = 2.5
        rt_mean_phase = np.mean(rt_raw)
        rt_sd_phase = np.std(rt_raw, ddof=1) if len(rt_raw) > 1 else 0
        lower_bound = rt_mean_phase - threshold * rt_sd_phase
        upper_bound = rt_mean_phase + threshold * rt_sd_phase
        outlier_mask = (rt_raw < lower_bound) | (rt_raw > upper_bound)
        n_outliers = int(np.sum(outlier_mask))
        rt_cleaned = rt_raw[~outlier_mask]

        # Cleaned descriptives
        cleaned_mean = np.mean(rt_cleaned) if len(rt_cleaned) > 0 else np.nan
        cleaned_sd = safe_std(pd.Series(rt_cleaned)) if len(rt_cleaned) > 1 else np.nan

        phase_dist = {
            'skewness': skewness, 'kurtosis': kurtosis_val,
            'n_raw': len(rt_raw), 'raw_mean': raw_mean, 'raw_sd': raw_sd,
            'n_outliers': n_outliers, 'outlier_threshold_sd': threshold,
            'lower_bound': lower_bound, 'upper_bound': upper_bound,
            'n_cleaned': len(rt_cleaned),
            'cleaned_mean': cleaned_mean, 'cleaned_sd': cleaned_sd,
        }
        results['rt_distribution'][phase] = phase_dist

        report(f"{label:<8} {skewness:>7.2f} {kurtosis_val:>7.2f} {len(rt_raw):>4} "
               f"{raw_mean/1000:>7.1f} {raw_sd/1000:>7.1f} "
               f"{n_outliers:>4} {cleaned_mean/1000:>8.1f} {cleaned_sd/1000:>9.1f}")

    # Summary of outliers
    total_outliers = sum(d.get('n_outliers', 0) for d in results['rt_distribution'].values())
    total_trials = sum(d.get('n_raw', 0) for d in results['rt_distribution'].values())
    report(f"\n  Total outliers: {total_outliers}/{total_trials} "
           f"({100*total_outliers/total_trials:.1f}%)" if total_trials > 0 else "")

    return results


# ============================================================================
# ALTERNATIVE ERROR MEASURES - Power-law loss functions
# ============================================================================
# SAD uses exponent 1 (|error|^1). The CNS may optimize closer to exponent
# 1.72 (Kording & Wolpert, 2004, PNAS). SSE uses exponent 2.
# This analysis compares learning curves under different loss assumptions.

def compute_power_error(estimates, true_dist, exponent):
    """Compute sum of |estimate_i - true_i|^exponent across items."""
    errors = np.abs(np.array(estimates) - np.array(true_dist))
    return np.sum(errors ** exponent)


def analyze_alternative_errors(df, summary_df):
    """Compute error with exponents 1 (SAD), 1.72 (CNS-optimal), 2 (SSE)."""
    report("\n" + "=" * 70)
    report("ALTERNATIVE ERROR MEASURES (Power-Law Loss Functions)")
    report("=" * 70)

    exponents = [1.0, 1.72, 2.0]
    exp_labels = ['SAD (p=1)', 'CNS (p=1.72)', 'SSE (p=2)']
    results = {'exponents': exponents, 'labels': exp_labels, 'by_phase': {}}

    report(f"\n{'Phase':<8}  " + '  '.join(f"{lbl:>14}" for lbl in exp_labels))
    report("-" * 55)

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        phase_errors = {}

        for exp, exp_lbl in zip(exponents, exp_labels):
            errors = []
            for _, row in phase_df.iterrows():
                ests = [row.get(f'gen_est_item{i}', np.nan) for i in range(1, 5)]
                if not any(pd.isna(e) for e in ests):
                    errors.append(compute_power_error(ests, TRUE_DISTRIBUTION, exp))
            if errors:
                phase_errors[exp] = {
                    'mean': np.mean(errors), 'sd': safe_std(pd.Series(errors)),
                    'median': np.median(errors), 'sem': safe_sem(errors),
                    'values': errors
                }

        results['by_phase'][phase] = phase_errors

        parts = [f"{label:<8}"]
        for exp in exponents:
            d = phase_errors.get(exp, {})
            parts.append(f"  M={d.get('mean',0):>6.2f} SD={d.get('sd',0):>5.2f}")
        report(''.join(parts))

    # Friedman test for each exponent
    report("\n--- Friedman Tests per Exponent ---")
    results['friedman_tests'] = {}
    for exp, exp_lbl in zip(exponents, exp_labels):
        matrix = []
        for _, row in summary_df.iterrows():
            subj = row['subject_nr']
            row_vals = []
            for phase in PHASE_ORDER:
                pdata = df[(df['subject_nr'] == subj) & (df['trial_type'] == phase)]
                if len(pdata) > 0:
                    ests = [pdata.iloc[0].get(f'gen_est_item{i}', np.nan) for i in range(1, 5)]
                    if not any(pd.isna(e) for e in ests):
                        row_vals.append(compute_power_error(ests, TRUE_DISTRIBUTION, exp))
                    else:
                        row_vals.append(np.nan)
                else:
                    row_vals.append(np.nan)
            matrix.append(row_vals)

        matrix = np.array(matrix)
        valid = ~np.any(np.isnan(matrix), axis=1)
        valid_m = matrix[valid]

        if valid_m.shape[0] >= 3:
            chi2, p = stats.friedmanchisquare(*[valid_m[:, i] for i in range(4)])
            results['friedman_tests'][exp] = {'statistic': chi2, 'p_value': p, 'n': valid_m.shape[0]}
            report(f"  {exp_lbl}: chi2={chi2:.3f}, p={p:.4f} {interpret_p_value(p)}")
        else:
            report(f"  {exp_lbl}: insufficient data (n={valid_m.shape[0]})")

    # Correlation between exponents (do they agree?)
    report("\n--- Cross-Exponent Correlation (T2 phase) ---")
    t2_errors = results['by_phase'].get('exposure_gen_2', {})
    if 1.0 in t2_errors and 2.0 in t2_errors:
        v1 = t2_errors[1.0].get('values', [])
        v2 = t2_errors[2.0].get('values', [])
        if len(v1) == len(v2) and len(v1) > 2:
            rho, p = stats.spearmanr(v1, v2)
            results['sad_sse_correlation'] = {'rho': rho, 'p_value': p}
            report(f"  SAD vs SSE (T2): rho={rho:.3f}, p={p:.4f}")

    return results


# ============================================================================
# DISTRIBUTION FIT ANALYSIS - Chi-square GoF and KS test
# ============================================================================
# Tests whether participant estimates fit the true distribution [1,1,4,6].
# Chi-square GoF: classical categorical fit test.
# KS test: applied to cumulative proportions (4-point CDF).

def analyze_distribution_fit(df, summary_df):
    """Chi-square goodness-of-fit and KS test of estimates vs true distribution."""
    report("\n" + "=" * 70)
    report("DISTRIBUTION FIT ANALYSIS (Chi-square GoF & KS Test)")
    report("=" * 70)

    results = {'by_phase': {}, 'individual': {}}
    true_props = np.array(TRUE_DISTRIBUTION) / sum(TRUE_DISTRIBUTION)
    true_cdf = np.cumsum(true_props)

    report(f"\nTrue distribution: {TRUE_DISTRIBUTION} (proportions: {true_props.round(4)})")
    report(f"\n{'Phase':<8} {'ChiSq_M':>8} {'ChiSq_Mdn':>10} {'KS_M':>7} {'KS_Mdn':>8} "
           f"{'%Fit':>6} {'N':>4}")
    report("-" * 60)

    for phase in PHASE_ORDER:
        phase_df = df[df['trial_type'] == phase]
        label = PHASE_SHORT[phase]
        chi2_vals, ks_vals, p_chi2_vals, p_ks_vals = [], [], [], []

        for _, row in phase_df.iterrows():
            ests = np.array([row.get(f'gen_est_item{i}', np.nan) for i in range(1, 5)])
            if any(np.isnan(ests)):
                continue
            total = ests.sum()
            if total == 0:
                continue

            # Chi-square GoF
            # Expected counts based on true proportions scaled to participant's total
            expected = true_props * total
            # Avoid division by zero: use max(expected, 0.5)
            expected_safe = np.maximum(expected, 0.5)
            chi2_stat = np.sum((ests - expected) ** 2 / expected_safe)
            # df = k - 1 = 3 (4 categories, no fitted parameters)
            p_chi2 = 1 - stats.chi2.cdf(chi2_stat, df=3)
            chi2_vals.append(chi2_stat)
            p_chi2_vals.append(p_chi2)

            # KS test on cumulative proportions
            est_props = ests / total
            est_cdf = np.cumsum(est_props)
            ks_stat = np.max(np.abs(est_cdf - true_cdf))
            ks_vals.append(ks_stat)

            # Store individual results
            subj = row.get('subject_nr', 'unknown')
            if subj not in results['individual']:
                results['individual'][subj] = {}
            results['individual'][subj][phase] = {
                'chi2': chi2_stat, 'p_chi2': p_chi2,
                'ks': ks_stat, 'estimates': ests.tolist()
            }

        # Phase summary
        if chi2_vals:
            n_fit = sum(1 for p in p_chi2_vals if p > 0.05)
            phase_res = {
                'chi2_mean': np.mean(chi2_vals), 'chi2_median': np.median(chi2_vals),
                'chi2_sd': safe_std(pd.Series(chi2_vals)),
                'ks_mean': np.mean(ks_vals), 'ks_median': np.median(ks_vals),
                'ks_sd': safe_std(pd.Series(ks_vals)),
                'pct_fit': 100 * n_fit / len(chi2_vals),
                'n': len(chi2_vals),
                'chi2_values': chi2_vals, 'ks_values': ks_vals,
                'p_chi2_values': p_chi2_vals,
            }
            results['by_phase'][phase] = phase_res
            report(f"{label:<8} {phase_res['chi2_mean']:>8.2f} {phase_res['chi2_median']:>10.2f} "
                   f"{phase_res['ks_mean']:>7.3f} {phase_res['ks_median']:>8.3f} "
                   f"{phase_res['pct_fit']:>5.1f}% {phase_res['n']:>4}")

    # Friedman on chi-square values across phases
    report("\n--- Chi-square GoF Friedman Test ---")
    chi2_matrix = []
    for subj in summary_df['subject_nr']:
        row_vals = []
        for phase in PHASE_ORDER:
            subj_data = results['individual'].get(subj, {}).get(phase, {})
            row_vals.append(subj_data.get('chi2', np.nan))
        chi2_matrix.append(row_vals)
    chi2_matrix = np.array(chi2_matrix)
    valid = ~np.any(np.isnan(chi2_matrix), axis=1)
    valid_m = chi2_matrix[valid]
    if valid_m.shape[0] >= 3:
        chi2f, pf = stats.friedmanchisquare(*[valid_m[:, i] for i in range(4)])
        results['chi2_friedman'] = {'statistic': chi2f, 'p_value': pf, 'n': valid_m.shape[0]}
        report(f"  Friedman chi2={chi2f:.3f}, p={pf:.4f} {interpret_p_value(pf)}")
    else:
        report(f"  Insufficient data (n={valid_m.shape[0]})")

    # Note about chi-square limitations
    report("\n  NOTE: Chi-square GoF with expected values < 5 (rare items: E=1)")
    report("  should be interpreted with caution. Results are supplementary to SAD.")

    return results


# ============================================================================
# Q7: SELF-REPORT VALIDATION - Do strategies match behavior?
# ============================================================================
# Analyzes 5 post-experiment questionnaire items:
#   Q1: Blind prior strategy (what did you do with gray squares?)
#   Q2: Icon prior strategy (did shapes change your guess?)
#   Q3: Task understanding (1-6 scale) -> correlated with T2 SAD
#   Q4: Update strategy after exposure -> compared to T1 accuracy
#   Q5: Learning source T1->T2 (observation vs feedback) -> improvement
# Purpose: Validates whether explicit strategies align with implicit learning.
# Displayed in separate Figure 3 with full Hebrew question text.

# Full Hebrew question texts for Figure 3 panel headers.
# Separated into English label and Hebrew text to avoid mixed-direction rendering.
Q_TEXTS = {
    'q1': ('Q1:', 'איך ניגשת להערכה הראשונה כשראית ריבועים אפורים?'),
    'q2': ('Q2:', 'איך ניגשת להערכה כשראית את הצורות עצמן?'),
    'q3': ('Q3:', 'באיזו מידה הבנת את המשימה? (1-6)'),
    'q4': ('Q4:', 'איך עדכנת את ההערכה שלך אחרי שראית את המערך?'),
    'q5': ('Q5:', 'מה השפיע על השינוי בין ההערכה הראשונה לשנייה?'),
}

def analyze_self_report(df, summary_df):
    """Q7: Strategy-behavior concordance for all 5 questionnaire items."""
    report("\n" + "=" * 70)
    report("Q7: SELF-REPORT VALIDATION")
    report("=" * 70)

    results = {}

    # Q1: Blind prior approach
    report("\n--- Q1: Blind Prior Approach ---")
    if 'post_q1_blind_prior_approach' in summary_df.columns:
        q1_counts = summary_df['post_q1_blind_prior_approach'].value_counts()
        results['q1_distribution'] = q1_counts.to_dict()
        report("Strategies:")
        for s, c in q1_counts.items():
            report(f"  {str(s)[:60]}: {c}")

    # Q2: Icon prior approach
    report("\n--- Q2: Icon Prior Approach ---")
    if 'post_q2_icon_prior_approach' in summary_df.columns:
        q2_counts = summary_df['post_q2_icon_prior_approach'].value_counts()
        results['q2_distribution'] = q2_counts.to_dict()
        for s, c in q2_counts.items():
            report(f"  {str(s)[:60]}: {c}")

    # Q3: Task understanding vs performance
    report("\n--- Q3: Understanding vs Performance ---")
    if 'post_q3_task_understanding' in summary_df.columns and 'T2_sad' in summary_df.columns:
        understanding = summary_df['post_q3_task_understanding'].dropna()
        t2_sad = summary_df.loc[understanding.index, 'T2_sad'].dropna()
        valid_idx = understanding.index.intersection(t2_sad.index)

        if len(valid_idx) > 2:
            rho, p = stats.spearmanr(understanding.loc[valid_idx],
                                     summary_df.loc[valid_idx, 'T2_sad'])
            results['q3_correlation'] = {'rho': rho, 'p_value': p}
            report(f"Understanding vs T2 SAD: rho={rho:.3f}, p={p:.4f} {interpret_p_value(p)}")

            high = summary_df.loc[valid_idx][understanding.loc[valid_idx] >= 5]['T2_sad']
            low = summary_df.loc[valid_idx][understanding.loc[valid_idx] <= 3]['T2_sad']
            if len(high) > 0:
                report(f"High understanding (5-6): M={high.mean():.2f} (n={len(high)})")
            if len(low) > 0:
                report(f"Low understanding (1-3): M={low.mean():.2f} (n={len(low)})")

    # Q4: Update strategy
    report("\n--- Q4: Update Strategy vs T1 ---")
    if 'post_q4_update_strategy' in summary_df.columns and 'T1_sad' in summary_df.columns:
        strategies = summary_df['post_q4_update_strategy'].dropna().unique()
        results['q4_by_strategy'] = {}
        for strat in strategies:
            mask = summary_df['post_q4_update_strategy'] == strat
            sad_vals = summary_df.loc[mask, 'T1_sad'].dropna()
            if len(sad_vals) > 0:
                results['q4_by_strategy'][strat] = {'mean': sad_vals.mean(), 'n': len(sad_vals)}
                report(f"  {str(strat)[:50]}: M={sad_vals.mean():.2f} (n={len(sad_vals)})")

    # Q5: Learning source
    report("\n--- Q5: Learning Source (T1->T2) ---")
    if 'post_q5_update_between_trials' in summary_df.columns:
        q5_counts = summary_df['post_q5_update_between_trials'].value_counts()
        results['q5_distribution'] = q5_counts.to_dict()
        for s, c in q5_counts.items():
            report(f"  {str(s)[:50]}: {c}")

        # Improvement by source
        results['q5_by_source'] = {}
        for source in q5_counts.index:
            mask = summary_df['post_q5_update_between_trials'] == source
            t1 = summary_df.loc[mask, 'T1_sad']
            t2 = summary_df.loc[mask, 'T2_sad']
            improvement = (t1 - t2).dropna()
            if len(improvement) > 0:
                results['q5_by_source'][source] = {
                    'mean_improvement': improvement.mean(), 'n': len(improvement)
                }
                report(f"    -> Improvement: M={improvement.mean():.2f} (n={len(improvement)})")

    return results



# ============================================================================
# FIGURE HELPERS
# ============================================================================

def add_significance_bracket(ax, x1, x2, y, p_value, h=0.3, lw=1.2):
    """Draw significance bracket between two x positions (only if significant)."""
    stars = interpret_p_value(p_value)
    if stars == "n.s.":
        return
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=lw, color='black')
    ax.text((x1 + x2) / 2, y + h, stars, ha='center', va='bottom', fontsize=9, fontweight='bold')

def add_bracket_labeled(ax, x1, x2, y, p_value, h=0.25, lw=1.0, fontsize=8):
    """Draw a significance bracket between x1..x2 at height y, ALWAYS labeled
    (stars if significant, 'n.s.' otherwise). Unlike add_significance_bracket,
    this does not skip non-significant comparisons."""
    stars = interpret_p_value(p_value)
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=lw, color='black')
    ax.text((x1 + x2) / 2, y + h, stars, ha='center', va='bottom',
            fontsize=fontsize, fontweight='bold')

def add_stats_text(ax, text, loc='upper right', fontsize=7):
    """Add statistics text box to a panel."""
    props = dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85, edgecolor='gray')
    positions = {
        'upper right': (0.97, 0.97, 'right', 'top'),
        'upper left': (0.03, 0.97, 'left', 'top'),
        'lower right': (0.97, 0.03, 'right', 'bottom'),
        'lower left': (0.03, 0.03, 'left', 'bottom'),
    }
    x, y, ha, va = positions.get(loc, positions['upper right'])
    ax.text(x, y, text, transform=ax.transAxes, fontsize=fontsize,
            ha=ha, va=va, bbox=props, family='monospace')

# Shape classification colors (for Figure 2 and Figure 3)
SHAPE_COLORS = {
    'Uniform': '#808080',
    'Unimodal-mild': '#FF8C00',
    'Unimodal-extreme': '#DC143C',
    'Bimodal-symmetric': '#4682B4',
    'J-shaped (True)': '#2E8B57',
}


# ============================================================================
# ESTIMATION TREND ANALYSIS - Higher estimates, range convergence, precision
# ============================================================================
# Analyzes how estimation patterns change across phases:
# (a) Max estimate and dominant item estimate trends
# (b) Proportion of estimates in target range [4,6]
# (c) Near-miss analysis and conditional probability of joint hits

def analyze_estimation_trends(df, summary_df):
    """Analyze estimation trends: max/dominant trends, range convergence, precision."""
    report("\n" + "=" * 70)
    report("ESTIMATION TREND ANALYSIS")
    report("=" * 70)

    results = {}

    # ---- (a) Max estimate and dominant item per participant per phase ----
    report("\n--- Max Estimate & Dominant Item Trends ---")
    max_matrix, dom_matrix = [], []
    for _, row in summary_df.iterrows():
        max_row, dom_row = [], []
        for prefix in ['Blind', 'Icon', 'T1', 'T2']:
            ests = [row.get(f'{prefix}_est{i}', np.nan) for i in range(1, 5)]
            if not any(pd.isna(e) for e in ests):
                max_row.append(max(ests))
                dom_row.append(ests[3])  # item 4 = dominant
            else:
                max_row.append(np.nan)
                dom_row.append(np.nan)
        max_matrix.append(max_row)
        dom_matrix.append(dom_row)

    max_matrix = np.array(max_matrix)
    dom_matrix = np.array(dom_matrix)
    results['max_matrix'] = max_matrix
    results['dom_matrix'] = dom_matrix

    # Friedman on max estimates
    valid_max = max_matrix[~np.any(np.isnan(max_matrix), axis=1)]
    if valid_max.shape[0] >= 3:
        chi2, p = stats.friedmanchisquare(*[valid_max[:, i] for i in range(4)])
        results['max_friedman'] = {'statistic': chi2, 'p_value': p, 'n': valid_max.shape[0]}
        report(f"  Max estimate Friedman: chi2={chi2:.3f}, p={p:.4f} {interpret_p_value(p)}")

    # Friedman on dominant item
    valid_dom = dom_matrix[~np.any(np.isnan(dom_matrix), axis=1)]
    if valid_dom.shape[0] >= 3:
        chi2, p = stats.friedmanchisquare(*[valid_dom[:, i] for i in range(4)])
        results['dom_friedman'] = {'statistic': chi2, 'p_value': p, 'n': valid_dom.shape[0]}
        report(f"  Dominant item Friedman: chi2={chi2:.3f}, p={p:.4f} {interpret_p_value(p)}")

    # Page's trend test (tests monotonic trend across Blind, Icon, T1, T2)
    # Two-tailed: positive Z = decreasing SAD (improvement), negative Z = increasing SAD (worsening)
    # L = sum of rank_sum_j * j for j=1..k. Under H0, L ~ normal.
    for label, matrix in [('Max', valid_max), ('Dominant', valid_dom)]:
        if matrix.shape[0] >= 3:
            n_subj, k = matrix.shape
            # Rank within each subject
            ranked = np.zeros_like(matrix)
            for i in range(n_subj):
                ranked[i] = stats.rankdata(matrix[i])
            rank_sums = ranked.sum(axis=0)  # sum of ranks per condition
            L = sum(rank_sums[j] * (j + 1) for j in range(k))
            # Expected value and variance under H0
            E_L = n_subj * k * (k + 1) ** 2 / 4
            Var_L = n_subj * k ** 2 * (k + 1) * (k ** 2 - 1) / 144
            Z = (L - E_L) / np.sqrt(Var_L) if Var_L > 0 else 0
            p_page = 2 * stats.norm.sf(abs(Z))  # two-tailed
            direction = 'decreasing SAD (improvement)' if Z > 0 else 'increasing SAD (worsening)' if Z < 0 else 'no trend'
            results[f'{label.lower()}_page'] = {'L': L, 'Z': Z, 'p_value': p_page, 'n': n_subj, 'direction': direction}
            report(f"  {label} Page trend: L={L:.1f}, Z={Z:.2f}, p={p_page:.4f} {interpret_p_value(p_page)} ({direction})")

    # Phase means
    report(f"\n  {'Phase':<8} {'MaxEst_M':>9} {'MaxEst_SD':>10} {'DomEst_M':>9} {'DomEst_SD':>10}")
    for i, phase in enumerate(PHASE_ORDER):
        max_vals = max_matrix[:, i][~np.isnan(max_matrix[:, i])]
        dom_vals = dom_matrix[:, i][~np.isnan(dom_matrix[:, i])]
        report(f"  {PHASE_SHORT[phase]:<8} {np.mean(max_vals):>9.2f} {safe_std(pd.Series(max_vals)):>10.2f} "
               f"{np.mean(dom_vals):>9.2f} {safe_std(pd.Series(dom_vals)):>10.2f}")

    # ---- (b) Range convergence: proportion of estimates in [4,6] ----
    report("\n--- Range Convergence [4,6] ---")

    # Per participant: proportion of 4 items in [4,6]
    prop_in_range = []
    for _, row in summary_df.iterrows():
        prow = []
        for prefix in ['Blind', 'Icon', 'T1', 'T2']:
            ests = [row.get(f'{prefix}_est{i}', np.nan) for i in range(1, 5)]
            if not any(pd.isna(e) for e in ests):
                prow.append(sum(4 <= e <= 6 for e in ests) / 4.0)
            else:
                prow.append(np.nan)
        prop_in_range.append(prow)
    prop_in_range = np.array(prop_in_range)
    results['prop_in_range'] = prop_in_range

    # Per item role: % with estimate in [4,6]
    role_in_range = {'dominant': [], 'medium': [], 'rare': []}
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type'] == phase]
        if len(pdf) > 0:
            role_in_range['dominant'].append(100 * (pdf['gen_est_item4'].between(4, 6)).mean())
            role_in_range['medium'].append(100 * (pdf['gen_est_item3'].between(4, 6)).mean())
            role_in_range['rare'].append(100 * ((pdf['gen_est_item1'].between(4, 6)) | (pdf['gen_est_item2'].between(4, 6))).mean())
    results['role_in_range'] = role_in_range

    # Friedman on proportion in range
    valid_pir = prop_in_range[~np.any(np.isnan(prop_in_range), axis=1)]
    if valid_pir.shape[0] >= 3:
        chi2, p = stats.friedmanchisquare(*[valid_pir[:, i] for i in range(4)])
        results['range_friedman'] = {'statistic': chi2, 'p_value': p, 'n': valid_pir.shape[0]}
        report(f"  Prop in [4,6] Friedman: chi2={chi2:.3f}, p={p:.4f} {interpret_p_value(p)}")

    # Cochran's Q per role (binary: in [4,6] or not)
    report("\n  Cochran's Q per item role:")
    for role, item_cols in [('Dominant', ['gen_est_item4']),
                             ('Medium', ['gen_est_item3']),
                             ('Rare', ['gen_est_item1', 'gen_est_item2'])]:
        binary_matrix = []
        for _, row in summary_df.iterrows():
            brow = []
            for prefix in ['Blind', 'Icon', 'T1', 'T2']:
                ests = [row.get(f'{prefix}_est{int(c.split("item")[1])}', np.nan) for c in item_cols]
                if not any(pd.isna(e) for e in ests):
                    brow.append(1 if any(4 <= e <= 6 for e in ests) else 0)
                else:
                    brow.append(np.nan)
            binary_matrix.append(brow)
        bm = np.array(binary_matrix)
        valid_bm = bm[~np.any(np.isnan(bm), axis=1)].astype(int)
        if valid_bm.shape[0] >= 3:
            # Cochran's Q: Q = (k-1) * [k * sum(Cj^2) - T^2] / [k*T - sum(Ri^2)]
            k = 4
            T = valid_bm.sum()
            Cj = valid_bm.sum(axis=0)
            Ri = valid_bm.sum(axis=1)
            numer = (k - 1) * (k * np.sum(Cj ** 2) - T ** 2)
            denom = k * T - np.sum(Ri ** 2)
            Q_stat = numer / denom if denom > 0 else 0
            p_q = 1 - stats.chi2.cdf(Q_stat, df=k - 1)
            results[f'cochran_{role.lower()}'] = {'Q': Q_stat, 'p_value': p_q, 'n': valid_bm.shape[0]}
            report(f"    {role}: Q={Q_stat:.3f}, p={p_q:.4f} {interpret_p_value(p_q)}")

    # ---- (c) Near-miss analysis ----
    report("\n--- Near-Miss & Exact Hit Analysis ---")
    # For dominant (true=6): exact=6, near={5,7}, far=rest
    # For medium (true=4): exact=4, near={3,5}, far=rest
    results['precision'] = {}
    for role, item_col, true_val in [('dominant', 'gen_est_item4', 6), ('medium', 'gen_est_item3', 4)]:
        phase_precision = {}
        for phase in PHASE_ORDER:
            pdf = df[df['trial_type'] == phase]
            vals = pdf[item_col].dropna().values
            n_total = len(vals)
            if n_total > 0:
                exact = int(np.sum(vals == true_val))
                near = int(np.sum(np.abs(vals - true_val) == 1))
                far = n_total - exact - near
                phase_precision[phase] = {
                    'exact': exact, 'exact_pct': 100 * exact / n_total,
                    'near': near, 'near_pct': 100 * near / n_total,
                    'far': far, 'far_pct': 100 * far / n_total,
                    'n': n_total
                }
        results['precision'][role] = phase_precision

    # Cochran's Q on exact+near (binary: within 1 of true or not)
    for role, item_col, true_val in [('dominant', 'gen_est_item4', 6), ('medium', 'gen_est_item3', 4)]:
        binary_mat = []
        for _, row in summary_df.iterrows():
            brow = []
            for prefix in ['Blind', 'Icon', 'T1', 'T2']:
                est = row.get(f'{prefix}_est{int(item_col.split("item")[1])}', np.nan)
                if not pd.isna(est):
                    brow.append(1 if abs(est - true_val) <= 1 else 0)
                else:
                    brow.append(np.nan)
            binary_mat.append(brow)
        bm = np.array(binary_mat)
        valid_bm = bm[~np.any(np.isnan(bm), axis=1)].astype(int)
        if valid_bm.shape[0] >= 3:
            k = 4
            T = valid_bm.sum()
            Cj = valid_bm.sum(axis=0)
            Ri = valid_bm.sum(axis=1)
            numer = (k - 1) * (k * np.sum(Cj ** 2) - T ** 2)
            denom = k * T - np.sum(Ri ** 2)
            Q_stat = numer / denom if denom > 0 else 0
            p_q = 1 - stats.chi2.cdf(Q_stat, df=k - 1)
            results[f'near_cochran_{role}'] = {'Q': Q_stat, 'p_value': p_q, 'n': valid_bm.shape[0]}
            report(f"  {role.title()} exact+near Cochran Q={Q_stat:.3f}, p={p_q:.4f} {interpret_p_value(p_q)}")

    # ---- (d) Conditional probability: P(hit6|hit4) and joint hits ----
    report("\n--- Joint & Conditional Hit Probabilities ---")
    results['joint_hits'] = {}
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type'] == phase]
        if len(pdf) > 0:
            hit6 = (pdf['gen_est_item4'] == 6).values
            hit4 = (pdf['gen_est_item3'] == 4).values
            n = len(pdf)
            n_hit6 = int(hit6.sum())
            n_hit4 = int(hit4.sum())
            n_both = int((hit6 & hit4).sum())
            p_6g4 = n_both / n_hit4 if n_hit4 > 0 else np.nan
            p_4g6 = n_both / n_hit6 if n_hit6 > 0 else np.nan
            results['joint_hits'][phase] = {
                'p_hit6': n_hit6 / n, 'p_hit4': n_hit4 / n,
                'p_both': n_both / n, 'p_6_given_4': p_6g4, 'p_4_given_6': p_4g6, 'n': n
            }
            report(f"  {PHASE_SHORT[phase]}: P(6)={n_hit6/n:.2f} P(4)={n_hit4/n:.2f} "
                   f"P(both)={n_both/n:.2f} P(6|4)={p_6g4:.2f} P(4|6)={p_4g6:.2f}")

    # Cochran's Q on joint hits across phases
    joint_binary = []
    for _, row in summary_df.iterrows():
        brow = []
        for prefix in ['Blind', 'Icon', 'T1', 'T2']:
            e4 = row.get(f'{prefix}_est4', np.nan)
            e3 = row.get(f'{prefix}_est3', np.nan)
            if not (pd.isna(e4) or pd.isna(e3)):
                brow.append(1 if (e4 == 6 and e3 == 4) else 0)
            else:
                brow.append(np.nan)
        joint_binary.append(brow)
    jm = np.array(joint_binary)
    valid_jm = jm[~np.any(np.isnan(jm), axis=1)].astype(int)
    if valid_jm.shape[0] >= 3 and valid_jm.sum() > 0:
        k = 4
        T = valid_jm.sum()
        Cj = valid_jm.sum(axis=0)
        Ri = valid_jm.sum(axis=1)
        numer = (k - 1) * (k * np.sum(Cj ** 2) - T ** 2)
        denom = k * T - np.sum(Ri ** 2)
        if denom > 0:
            Q_stat = numer / denom
            p_q = 1 - stats.chi2.cdf(Q_stat, df=k - 1)
            results['joint_cochran'] = {'Q': Q_stat, 'p_value': p_q, 'n': valid_jm.shape[0]}
            report(f"  Joint hit Cochran Q={Q_stat:.3f}, p={p_q:.4f} {interpret_p_value(p_q)}")

    # ---- (e) Dominant item estimate bins for stacked bar / alluvial ----
    results['dom_bins'] = {}
    bin_edges = [0, 2, 4, 5, 6, 7, 13]  # 0-1, 2-3, 4-5, 6, 7+
    bin_labels = ['0-1', '2-3', '4-5', '6', '7+']
    results['bin_labels'] = bin_labels
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type'] == phase]
        vals = pdf['gen_est_item4'].dropna().values
        if len(vals) > 0:
            counts = np.histogram(vals, bins=[0, 2, 4, 5.5, 6.5, 13])[0]
            # Bins: [0,2)=0-1, [2,4)=2-3, [4,5.5)=4-5, [5.5,6.5)=6, [6.5,13)=7+
            results['dom_bins'][phase] = {
                'counts': counts.tolist(),
                'pcts': (100 * counts / len(vals)).tolist(),
                'n': len(vals)
            }

    return results


# ============================================================================
# FEEDBACK UTILIZATION ANALYSIS - Does T1 error signal drive T2 correction?
# ============================================================================
# Tests whether larger SAD feedback on Trial 1 produces more correction on
# Trial 2 (prediction-error driven learning). Also tests feedback band effects
# and item-level correction direction.
# Caveat: regression to the mean inflates apparent correction for high T1 SAD.

def jonckheere_terpstra_test(groups, n_perm=10000, seed=42):
    """Jonckheere-Terpstra test for an ordered (monotonic) trend across groups.

    `groups` is a list of 1-D arrays given in the hypothesized order. Tests H0:
    no trend vs H1: a monotonic trend across the ordered groups. scipy has no JT,
    so this computes the statistic directly, a normal-approximation z, and a
    two-sided permutation p-value (label-shuffle, robust for small/unequal n).
    Returns {} if fewer than 2 non-empty groups or <3 total observations.
    """
    groups = [np.asarray(g, dtype=float) for g in groups if len(g) > 0]
    if len(groups) < 2:
        return {}
    ns = [len(g) for g in groups]
    N = int(sum(ns))
    if N < 3:
        return {}

    def _jt(grps):
        total = 0.0
        for i in range(len(grps)):
            for j in range(i + 1, len(grps)):
                xi, yj = grps[i], grps[j]
                # # of (x<y) pairs + 0.5 * ties, summed over ordered group pairs
                diff = yj[:, None] - xi[None, :]
                total += np.sum(diff > 0) + 0.5 * np.sum(diff == 0)
        return total

    jt = _jt(groups)
    # Normal approximation (no tie correction): mean & variance under H0
    sum_n2 = sum(n * n for n in ns)
    mean = (N * N - sum_n2) / 4.0
    var = (N * N * (2 * N + 3) - sum(n * n * (2 * n + 3) for n in ns)) / 72.0
    z = (jt - mean) / np.sqrt(var) if var > 0 else np.nan
    p_norm = 2 * stats.norm.sf(abs(z)) if not np.isnan(z) else np.nan

    # Two-sided permutation p-value: shuffle membership, keep group sizes fixed
    rng = np.random.default_rng(seed)
    pooled = np.concatenate(groups)
    obs_dev = abs(jt - mean)
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(pooled)
        idx, parts = 0, []
        for n in ns:
            parts.append(perm[idx:idx + n]); idx += n
        if abs(_jt(parts) - mean) >= obs_dev:
            count += 1
    p_perm = (count + 1) / (n_perm + 1)
    return {'statistic': float(jt), 'z': float(z), 'p_norm': float(p_norm),
            'p_value': float(p_perm), 'n': N, 'k_groups': len(groups)}


def analyze_feedback_utilization(df, summary_df):
    """Analyze whether T1 SAD feedback predicts T2 improvement magnitude."""
    report("\n" + "=" * 70)
    report("FEEDBACK UTILIZATION ANALYSIS")
    report("=" * 70)

    results = {}

    # Extract T1 and T2 SAD per participant
    t1_sad, t2_sad = [], []
    subj_ids = []
    for _, row in summary_df.iterrows():
        s1 = row.get('T1_sad', np.nan)
        s2 = row.get('T2_sad', np.nan)
        if not (pd.isna(s1) or pd.isna(s2)):
            t1_sad.append(s1)
            t2_sad.append(s2)
            subj_ids.append(row['subject_nr'])
    t1_sad = np.array(t1_sad)
    t2_sad = np.array(t2_sad)
    improvement = t1_sad - t2_sad  # positive = improved

    results['t1_sad'] = t1_sad
    results['t2_sad'] = t2_sad
    results['improvement'] = improvement
    results['n'] = len(t1_sad)

    if len(t1_sad) < 3:
        report("  Insufficient data for feedback analysis")
        return results

    # ---- (1) T1 SAD vs T2 SAD correlation ----
    rho_t1t2, p_t1t2 = stats.spearmanr(t1_sad, t2_sad)
    results['t1_t2_correlation'] = {'rho': rho_t1t2, 'p_value': p_t1t2}
    report(f"\n  T1 SAD vs T2 SAD: rho={rho_t1t2:.3f}, p={p_t1t2:.4f} {interpret_p_value(p_t1t2)}")
    report(f"    (Positive rho = stable individual differences; negative = overcorrection)")

    # ---- (2) T1 SAD vs Improvement ----
    rho_imp, p_imp = stats.spearmanr(t1_sad, improvement)
    results['error_correction'] = {'rho': rho_imp, 'p_value': p_imp}
    report(f"  T1 SAD vs Improvement (T1-T2): rho={rho_imp:.3f}, p={p_imp:.4f} {interpret_p_value(p_imp)}")
    report(f"    NOTE: This correlation is partially confounded by regression to the mean.")
    report(f"    High T1 SAD participants have more room to improve AND will regress toward the mean.")

    # ---- (3) Feedback band analysis ----
    # Categorize T1 SAD into bands matching the feedback color scheme
    # SAD 0: perfect, 1-2: green, 3-4: orange, 5-6: dark orange, 7+: red
    bands = []
    for s in t1_sad:
        if s <= 2: bands.append('Low (0-2)')
        elif s <= 4: bands.append('Mid (3-4)')
        elif s <= 6: bands.append('High (5-6)')
        else: bands.append('VHigh (7+)')
    bands = np.array(bands)
    results['bands'] = bands

    report(f"\n  Improvement by T1 Feedback Band:")
    report(f"  {'Band':<14} {'N':>4} {'Imp_M':>7} {'Imp_Mdn':>8} {'T2_M':>6}")
    report(f"  " + "-" * 45)
    band_stats = {}
    band_order = ['Low (0-2)', 'Mid (3-4)', 'High (5-6)', 'VHigh (7+)']
    band_groups = []   # ordered improvement arrays for the trend test
    for band in band_order:
        mask = bands == band
        if mask.sum() > 0:
            imp_vals = improvement[mask]
            t2_vals = t2_sad[mask]
            band_stats[band] = {
                'n': int(mask.sum()),
                'imp_mean': float(np.mean(imp_vals)),
                'imp_median': float(np.median(imp_vals)),
                't2_mean': float(np.mean(t2_vals)),
            }
            band_groups.append(imp_vals)
            report(f"  {band:<14} {mask.sum():>4} {np.mean(imp_vals):>7.2f} "
                   f"{np.median(imp_vals):>8.1f} {np.mean(t2_vals):>6.1f}")
    results['band_stats'] = band_stats

    # Jonckheere-Terpstra trend test: does improvement change monotonically across
    # the ordered T1 feedback bands? (exploratory; confounded by regression to mean)
    jt = jonckheere_terpstra_test(band_groups)
    results['jt_trend'] = jt
    if jt:
        report(f"\n  Jonckheere-Terpstra trend (improvement across ordered bands): "
               f"JT={jt['statistic']:.1f}, z={jt['z']:.2f}, "
               f"p_perm={jt['p_value']:.4f} {interpret_p_value(jt['p_value'])} "
               f"(k={jt['k_groups']} bands, N={jt['n']})")
        report(f"    NOTE: exploratory; band differences are inflated by regression to the mean.")

    # ---- (4) Item-level correction direction ----
    report(f"\n  Item-Level Correction (T1 -> T2):")
    results['item_correction'] = {}
    t1_df = df[df['trial_type'] == 'exposure_gen_1']
    t2_df = df[df['trial_type'] == 'exposure_gen_2']

    for item_idx in range(1, 5):
        item_col = f'gen_est_item{item_idx}'
        true_val = TRUE_DISTRIBUTION[item_idx - 1]
        role = ['rare', 'rare', 'medium', 'dominant'][item_idx - 1]

        corrections = []
        correct_direction = 0
        for subj in subj_ids:
            t1_est = t1_df.loc[t1_df['subject_nr'] == subj, item_col]
            t2_est = t2_df.loc[t2_df['subject_nr'] == subj, item_col]
            if len(t1_est) > 0 and len(t2_est) > 0:
                e1, e2 = t1_est.iloc[0], t2_est.iloc[0]
                error1 = e1 - true_val
                error2 = e2 - true_val
                correction = abs(error1) - abs(error2)  # positive = error reduced
                corrections.append(correction)
                # Did they move in the right direction?
                if error1 > 0 and e2 < e1:  # was over, moved down
                    correct_direction += 1
                elif error1 < 0 and e2 > e1:  # was under, moved up
                    correct_direction += 1
                elif error1 == 0:  # was correct
                    correct_direction += 1 if e2 == e1 else 0

        if corrections:
            n_corr = len(corrections)
            pct_correct = 100 * correct_direction / n_corr
            results['item_correction'][item_idx] = {
                'mean_correction': float(np.mean(corrections)),
                'pct_correct_direction': pct_correct,
                'n': n_corr
            }
            report(f"  Item {item_idx} ({role}, true={true_val}): "
                   f"mean correction={np.mean(corrections):+.2f}, "
                   f"{pct_correct:.0f}% correct direction")

    return results


def save_individual_panels(fig, fig_name, output_dir, timestamp, dpi=150,
                           pad_frac_x=0.065, pad_frac_y=0.05):
    """Save each subplot of `fig` as its own PNG under output_dir/subfigures/.

    Panel id is taken from the axis title (first token, dots->underscores). Each
    save is wrapped in try/except so one bad panel (e.g. a rich table or Hebrew
    RTL panel) can't abort the run.

    Companion axes are merged into their parent panel rather than saved separately:
      - colorbars (e.g. Panel 1.3 heatmap's 0-12 estimate scale), found via the
        mappable's `.colorbar` attribute;
      - twin/secondary axes (ax.twinx()/twiny()), detected by an identical
        position to another axis.
    Each panel is then given a clean whitespace margin of `pad_frac_x` of its
    width on the left and right and `pad_frac_y` of its height on top and bottom
    (defaults: 6.5% horizontal, 5% vertical). The margin is added as a white
    border on the rasterised crop, so it never pulls in ink from neighbouring
    panels.
    """
    import io
    import matplotlib.image as mpimg
    from matplotlib.transforms import Bbox

    subfig_dir = Path(output_dir) / 'subfigures'
    subfig_dir.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()                       # renderer must exist for tightbbox
    renderer = fig.canvas.get_renderer()
    all_axes = fig.get_axes()

    # ---- Group companion axes (colorbars + twins) with their parent panel ----
    companions = {}     # id(parent_ax) -> [companion axes]
    skip = set()        # axes NOT to save on their own (they ride along a parent)

    # Colorbars: a colorbar's axes is reachable from its mappable's `.colorbar`.
    for ax in all_axes:
        for m in list(ax.images) + list(ax.collections):
            cb = getattr(m, 'colorbar', None)
            if cb is not None and cb.ax is not None and cb.ax is not ax:
                companions.setdefault(id(ax), []).append(cb.ax)
                skip.add(cb.ax)

    # Twin/secondary axes share the exact same position as their parent.
    for a in all_axes:
        if a in skip:
            continue
        a_pos = a.get_position().bounds
        for b in all_axes:
            if b is a or b in skip or id(b) in {id(a)}:
                continue
            if b in companions.get(id(a), []):
                continue
            if np.allclose(a_pos, b.get_position().bounds, atol=1e-3):
                companions.setdefault(id(a), []).append(b)
                skip.add(b)

    for i, ax in enumerate(all_axes):
        if ax in skip:
            continue
        if not (ax.has_data() or ax.get_title()):   # skip truly empty axes
            continue
        title = ax.get_title()
        panel_id = (title.split(' ')[0] if title else f'panel_{i}').replace('.', '_')

        # Union the panel's tightbbox with those of its companion axes.
        bboxes = [ax.get_tightbbox(renderer)]
        for comp in companions.get(id(ax), []):
            bboxes.append(comp.get_tightbbox(renderer))
        bboxes = [b for b in bboxes if b is not None]
        if not bboxes:
            continue
        extent = Bbox.union(bboxes).transformed(fig.dpi_scale_trans.inverted())

        out = subfig_dir / f'{fig_name}_{panel_id}_{timestamp}.png'
        try:
            # Crop tightly to the panel (+ companions) into memory, then add a
            # clean white margin as a raster border (no neighbouring-panel bleed).
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches=extent, pad_inches=0)
            buf.seek(0)
            arr = mpimg.imread(buf)
            ph = int(round(arr.shape[0] * pad_frac_y))
            pw = int(round(arr.shape[1] * pad_frac_x))
            bordered = np.ones((arr.shape[0] + 2 * ph, arr.shape[1] + 2 * pw, arr.shape[2]),
                               dtype=arr.dtype)
            bordered[ph:ph + arr.shape[0], pw:pw + arr.shape[1], :] = arr
            mpimg.imsave(out, bordered)
            report(f"  Subfigure saved: {out}")
        except Exception as e:
            report(f"  Subfigure save failed for {panel_id}: {e}")


# ============================================================================
# FIGURE 1: DESCRIPTIVE OVERVIEW
# ============================================================================
# Panels: 1.1 Statistics table, 1.2 SAD violins, 1.3 Heatmap, 1.4 Diversity

def create_figure1(df, summary_df, results, save_path=None):
    """Figure 1: Descriptive overview (2x2). Table + distributions + heatmap + diversity."""
    fig = plt.figure(figsize=(16, 11))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)
    fig.suptitle('Figure 1: Descriptive Overview', fontsize=14, fontweight='bold', y=0.98)
    n = results.get('descriptives', {}).get('n_subjects', len(summary_df))

    # ---- 1.1: Statistics Table (reordered: M, SD, Mdn, MAD, Mode, IQR) ----
    ax = fig.add_subplot(gs[0, 0])
    ax.axis('off')
    ax.set_title('1.1 Descriptive Statistics by Phase', fontsize=11, fontweight='bold', pad=10)

    col_labels = ['Phase', 'SAD\nM', 'SAD\nSD', 'SAD\nMdn', 'SAD\nMAD', 'SAD\nMode', 'SAD\nIQR',
                  'Ent\nM', 'Ent\nSD', 'RT\nM(s)', 'RT\nSD(s)', 'RT\nMdn(s)', 'RT\nMAD(s)']
    table_data = []
    desc = results.get('descriptives', {}).get('by_phase', {})
    for phase in PHASE_ORDER:
        ps = desc.get(phase, {})
        s, e, r = ps.get('sad', {}), ps.get('entropy', {}), ps.get('rt', {})
        table_data.append([
            PHASE_SHORT[phase],
            f"{s.get('mean',0):.1f}", f"{s.get('sd',0):.1f}",
            f"{s.get('median',0):.0f}", f"{s.get('mad',0):.1f}",
            f"{s.get('mode',0):.0f}",
            f"{s.get('iqr',0):.1f}" if not pd.isna(s.get('iqr', np.nan)) else "-",
            f"{e.get('mean',0):.2f}", f"{e.get('sd',0):.2f}" if not pd.isna(e.get('sd', np.nan)) else "-",
            f"{r.get('mean',0)/1000:.1f}" if r.get('mean') else "-",
            f"{r.get('sd',0)/1000:.1f}" if r.get('sd') and not pd.isna(r.get('sd')) else "-",
            f"{r.get('median',0)/1000:.1f}" if r.get('median') else "-",
            f"{r.get('mad',0)/1000:.1f}" if r.get('mad') and not pd.isna(r.get('mad')) else "-",
        ])
    if table_data:
        table = ax.table(cellText=table_data, colLabels=col_labels, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.scale(1.0, 1.4)
        for j in range(len(col_labels)):
            table[0, j].set_height(0.12)
            table[0, j].set_facecolor('#4472C4')
            table[0, j].set_text_props(color='white', fontweight='bold', fontsize=6)
        for i, phase in enumerate(PHASE_ORDER):
            table[i+1, 0].set_facecolor(COLORS[phase])
            table[i+1, 0].set_text_props(color='white', fontweight='bold')
    ax.text(0.5, -0.02, f'N = {n}', ha='center', va='top', fontsize=9, transform=ax.transAxes, style='italic')

    # ---- 1.2: SAD Violin ----
    ax = fig.add_subplot(gs[0, 1])
    sad_data = [df[df['trial_type']==p]['distance_from_true'].dropna().values for p in PHASE_ORDER]
    parts = ax.violinplot(sad_data, positions=np.arange(1,5), showmeans=True, showmedians=True)
    for pc, phase in zip(parts['bodies'], PHASE_ORDER):
        pc.set_facecolor(COLORS[phase]); pc.set_alpha(0.6)
    parts['cmeans'].set_color('black'); parts['cmedians'].set_color('red')
    ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1.5, alpha=0.7, label=f'Uniform (SAD={UNIFORM_SAD})')
    ax.set_xticks(np.arange(1,5)); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('SAD'); ax.set_title('1.2 SAD Distribution by Phase'); ax.legend(fontsize=8); ax.set_ylim(0, MAX_SAD)

    # ---- 1.3: Response Heatmap with cell values ----
    ax = fig.add_subplot(gs[1, 0])
    subjects = summary_df.sort_values('T2_sad', ascending=True, na_position='last')
    n_subj = len(subjects)
    heatmap_data = np.full((n_subj, 16), np.nan)
    for row_idx, (_, row) in enumerate(subjects.iterrows()):
        for phase_idx, prefix in enumerate(['Blind', 'Icon', 'T1', 'T2']):
            for item_idx in range(1, 5):
                heatmap_data[row_idx, phase_idx*4 + (item_idx-1)] = row.get(f'{prefix}_est{item_idx}', np.nan)

    # Discrete colorbar: 13 bins (0-12) using YlOrRd but with BoundaryNorm
    from matplotlib.colors import BoundaryNorm
    boundaries = np.arange(-0.5, 13.5, 1)  # 0,1,2,...,12 bin edges
    cmap_discrete = plt.cm.YlOrRd
    norm = BoundaryNorm(boundaries, cmap_discrete.N)
    im = ax.imshow(heatmap_data, aspect='auto', cmap=cmap_discrete, norm=norm)

    ax.set_ylabel('Participant (sorted by T2 SAD)')
    ax.set_title('1.3 Response Heatmap (item estimates 0-12)')

    # TRUE values per item position within each phase block
    true_per_col = TRUE_DISTRIBUTION * 4  # [1,1,4,6, 1,1,4,6, 1,1,4,6, 1,1,4,6]

    for i in range(n_subj):
        for j in range(16):
            val = heatmap_data[i, j]
            if not np.isnan(val):
                tc = 'white' if val > 6 else 'black'
                is_exact = (int(val) == true_per_col[j])
                fw = 'bold' if is_exact else 'normal'
                fc = '#00AA00' if is_exact else tc  # green text for exact matches
                ax.text(j, i, f'{int(val)}', ha='center', va='center', fontsize=5,
                        color=fc, fontweight=fw)
                # Add subtle border for exact matches
                if is_exact:
                    rect = plt.Rectangle((j-0.45, i-0.45), 0.9, 0.9,
                                          linewidth=1.2, edgecolor='#00AA00',
                                          facecolor='none', zorder=3)
                    ax.add_patch(rect)

    for i in range(1, 4):
        ax.axvline(x=i*4-0.5, color='white', lw=2)
    ax.set_xticks([1.5, 5.5, 9.5, 13.5]); ax.set_xticklabels(['Blind', 'Icon', 'T1', 'T2'])
    ax.set_xticks(np.arange(16), minor=True)
    ax.set_xticklabels(['1','2','3','4']*4, minor=True, fontsize=5)
    ax.tick_params(axis='x', which='minor', length=0, pad=1)

    # Discrete colorbar with separated rectangles
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, ticks=np.arange(0, 13))
    cbar.set_label('Estimate (0-12)')
    ax.text(0.5, -0.12, 'Green bold = exact match (item true value)', ha='center',
            fontsize=7, style='italic', transform=ax.transAxes, color='#00AA00')

    # ---- 1.4: Diversity (Entropy + Gini-Simpson dual axis) ----
    ax = fig.add_subplot(gs[1, 1])
    ent_data = [df[df['trial_type']==p]['response_entropy'].dropna().values for p in PHASE_ORDER]
    bp = ax.boxplot(ent_data, positions=np.arange(1,5)-0.15, patch_artist=True, widths=0.25)
    for patch, phase in zip(bp['boxes'], PHASE_ORDER):
        patch.set_facecolor(COLORS[phase]); patch.set_alpha(0.6)
    u_ent, t_ent = calculate_entropy([3,3,3,3]), calculate_entropy(TRUE_DISTRIBUTION)
    ax.axhline(y=u_ent, color='gray', ls='--', lw=1, alpha=0.5)
    ax.axhline(y=t_ent, color=COLORS['true'], ls=':', lw=1, alpha=0.5)
    ax.set_ylabel('Shannon Entropy (bits)', fontsize=9); ax.set_ylim(1.4, 2.1)

    ax2 = ax.twinx()
    gs_m = [df[df['trial_type']==p]['response_gini_simpson'].dropna().mean() for p in PHASE_ORDER]
    gs_s = [safe_sem(df[df['trial_type']==p]['response_gini_simpson'].dropna()) for p in PHASE_ORDER]
    ax2.errorbar(np.arange(1,5)+0.15, gs_m, yerr=gs_s, fmt='D-', color='#E67E22', markersize=7, lw=1.5, capsize=3, markeredgecolor='black', label='Gini-Simpson')
    u_gs, t_gs = calculate_gini_simpson([3,3,3,3]), calculate_gini_simpson(TRUE_DISTRIBUTION)
    ax2.axhline(y=u_gs, color='#E67E22', ls='--', lw=1, alpha=0.3)
    ax2.axhline(y=t_gs, color='#E67E22', ls=':', lw=1, alpha=0.3)
    ax2.set_ylabel('Gini-Simpson Index', fontsize=9, color='#E67E22'); ax2.tick_params(axis='y', labelcolor='#E67E22'); ax2.set_ylim(0.4, 0.8)
    ax.set_xticks(range(1,5)); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_title('1.4 Response Diversity by Phase')
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Patch(facecolor=COLORS['blind_prior'], alpha=0.6, label='Entropy (box)'),
        Line2D([0],[0], color='#E67E22', marker='D', label='Gini-Simpson'),
        Line2D([0],[0], color='gray', ls='--', label=f'Uniform (H={u_ent:.2f}, GS={u_gs:.2f})'),
        Line2D([0],[0], color=COLORS['true'], ls=':', label=f'True (H={t_ent:.2f}, GS={t_gs:.2f})'),
    ], fontsize=6, loc='lower left')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 1 saved to: {save_path}")
    return fig


# ============================================================================
# FIGURE 2: PRIOR ANALYSIS (Q1) + EXACT MATCH RATES
# ============================================================================
# Panels: 2.1 Prior boxplots, 2.2 Shape classification, 2.3 Exact match by phase, 2.4 Exact match by role

def create_figure2(df, summary_df, results, save_path=None):
    """Figure 2: Prior analysis Q1 + exact match + prior response comparison (3x3)."""
    fig, axes = plt.subplots(3, 3, figsize=(18, 15))
    fig.suptitle('Figure 2: Prior Analysis & Exact Match Rates', fontsize=14, fontweight='bold')
    item_labels = ['Item 1\n(rare)', 'Item 2\n(rare)', 'Item 3\n(med)', 'Item 4\n(dom)']
    x_items = np.arange(4)
    q1 = results.get('q1', {})
    blind = df[df['trial_type'] == 'blind_prior']

    # ---- 2.1: Prior Distribution boxplot (Q1) ----
    ax = axes[0, 0]
    items_data = [blind[f'gen_est_item{i+1}'].dropna().values for i in range(4)]
    bp = ax.boxplot(items_data, positions=np.arange(4), patch_artist=True, widths=0.6)
    for patch, c in zip(bp['boxes'], [COLORS['rare'], COLORS['rare'], COLORS['medium'], COLORS['dominant']]):
        patch.set_facecolor(c); patch.set_alpha(0.6)
    ax.scatter(np.arange(4), TRUE_DISTRIBUTION, marker='*', s=200, color=COLORS['true'], zorder=10, label='True', edgecolor='black')
    ax.axhline(y=3, color='gray', ls='--', lw=1.5, alpha=0.6, label='Uniform (3.0)')
    ax.set_xticks(np.arange(4)); ax.set_xticklabels(item_labels)
    ax.set_ylabel('Blind Prior Estimate'); ax.set_title('2.1 Prior Distribution (Q1)')
    ax.legend(fontsize=7, loc='upper left'); ax.set_ylim(0, 12)
    ut = q1.get('uniform_test', {})
    if ut:
        add_stats_text(ax, f"vs Uniform:\np={ut.get('p_value', np.nan):.3f} {interpret_p_value(ut.get('p_value', 1))}", loc='upper right', fontsize=7)

    # ---- 2.7: Blind Prior Bars (mean + SEM + individual dots) ----
    ax = axes[0, 1]
    if len(blind) > 0:
        role_colors = [COLORS['rare'], COLORS['rare'], COLORS['medium'], COLORS['dominant']]
        role_labels_leg = ['Rare (true=1)', 'Rare (true=1)', 'Medium (true=4)', 'Dominant (true=6)']
        means_b = [blind[f'gen_est_item{i+1}'].dropna().mean() for i in range(4)]
        sems_b = [safe_sem(blind[f'gen_est_item{i+1}'].dropna()) for i in range(4)]
        medians_b = [blind[f'gen_est_item{i+1}'].dropna().median() for i in range(4)]
        # Plot bars individually for correct legend
        for i in range(4):
            lbl = role_labels_leg[i] if i != 1 else None  # skip duplicate rare label
            ax.bar(x_items[i], means_b[i], 0.55, yerr=sems_b[i], color=role_colors[i], alpha=0.7,
                   capsize=4, edgecolor='black', linewidth=0.5, label=lbl)
        # Individual dots
        rng_j = np.random.default_rng(42)
        for i in range(4):
            vals = blind[f'gen_est_item{i+1}'].dropna().values
            jx = rng_j.uniform(-0.18, 0.18, size=len(vals))
            ax.scatter(x_items[i] + jx, vals, s=12, alpha=0.4, color=role_colors[i],
                       edgecolor='black', linewidth=0.2, zorder=5)
        # Median markers
        ax.scatter(x_items, medians_b, marker='_', color='red', s=100, zorder=10, linewidths=2.5)
        # True values
        ax.scatter(x_items, TRUE_DISTRIBUTION, marker='*', s=200, color=COLORS['true'],
                   zorder=10, label='True', edgecolor='black')
        ax.axhline(y=3, color='gray', ls='--', lw=1, alpha=0.5, label='Uniform (3)')
        # Annotate means
        for i, m in enumerate(means_b):
            ax.text(i, m + sems_b[i] + 0.3, f'{m:.1f}', ha='center', fontsize=7, fontweight='bold')
    ax.set_xticks(x_items); ax.set_xticklabels(item_labels)
    ax.set_ylabel('Mean Estimate (red dash = median)')
    ax.set_title('2.2 Blind Prior (mean + SEM + dots)')
    ax.legend(fontsize=5.5, loc='upper left'); ax.set_ylim(0, 9)
    # Item assignment note
    ax.text(0.5, -0.18, 'Note: item assignment is position-based (see 2.9 for position-free test)',
            transform=ax.transAxes, fontsize=5.5, ha='center', style='italic', color='gray')

    # ---- 2.2: Prior Shape Classification ----
    ax = axes[0, 2]
    class_counts = q1.get('classification_counts', {})
    if class_counts:
        names = list(class_counts.keys())
        counts = [class_counts[n] for n in names]
        total = sum(counts)
        pcts = [100*c/total for c in counts]
        bar_colors = [SHAPE_COLORS.get(n, 'gray') for n in names]
        bars = ax.barh(np.arange(len(names)), pcts, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax.set_yticks(np.arange(len(names))); ax.set_yticklabels(names, fontsize=8)
        ax.set_xlabel('% of Participants')
        for bar, pct, cnt, name in zip(bars, pcts, counts, names):
            ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2,
                    f'{pct:.0f}% (n={cnt})', va='center', fontsize=8)
            ref = REFERENCE_DISTRIBUTIONS.get(name, [])
            if ref:
                ref_text = f'{ref}'
                if bar.get_width() > 12:
                    ax.text(bar.get_width()*0.5, bar.get_y()+bar.get_height()/2,
                            ref_text, va='center', ha='center', fontsize=7,
                            color='black', fontstyle='italic', alpha=0.7)
                else:
                    ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2 - 0.18,
                            ref_text, va='center', fontsize=6,
                            color='gray', fontstyle='italic')
        ax.set_xlim(0, max(pcts)*1.3 if pcts else 100)
    ax.set_title('2.3 Prior Shape Classification (Q1)')

    # ---- 2.5: Blind vs Icon Mean Response per Item ----
    ax = axes[1, 0]
    x_items = np.arange(4)
    bar_w = 0.3
    icon = df[df['trial_type'] == 'prior_icon']
    for phase_idx, (phase_df, phase_label, color, offset) in enumerate([
        (blind, 'Blind', COLORS['blind_prior'], -bar_w/2),
        (icon, 'Icon', COLORS['prior_icon'], bar_w/2),
    ]):
        means = [phase_df[f'gen_est_item{i+1}'].dropna().mean() for i in range(4)]
        sems = [safe_sem(phase_df[f'gen_est_item{i+1}'].dropna()) for i in range(4)]
        medians = [phase_df[f'gen_est_item{i+1}'].dropna().median() for i in range(4)]
        bars = ax.bar(x_items + offset, means, bar_w, yerr=sems, color=color, alpha=0.8,
                      capsize=3, edgecolor='black', linewidth=0.5, label=f'{phase_label} (mean)')
        # Median markers overlaid
        ax.scatter(x_items + offset, medians, marker='_', color='red', s=80,
                   zorder=10, linewidths=2)
    # True values as blue stars
    ax.scatter(x_items, TRUE_DISTRIBUTION, marker='*', s=200, color=COLORS['true'],
               zorder=10, label='True', edgecolor='black')
    ax.axhline(y=3, color='gray', ls='--', lw=1, alpha=0.5, label='Uniform (3)')
    ax.set_xticks(x_items); ax.set_xticklabels(item_labels)
    ax.set_ylabel('Mean Estimate (red dash = median)')
    ax.set_title('2.4 Blind vs Icon Prior (mean + SEM)')
    ax.legend(fontsize=6, loc='upper left'); ax.set_ylim(0, 9)

    # Annotate item-level Wilcoxon results (Blind vs Icon)
    item_bi = q1.get('item_blind_icon', {})
    if item_bi:
        for item_idx in range(1, 5):
            idata = item_bi.get(item_idx, {})
            if idata.get('p_bonferroni') is not None:
                p_bonf = idata['p_bonferroni']
                sig = '***' if p_bonf < 0.001 else '**' if p_bonf < 0.01 else '*' if p_bonf < 0.05 else ''
                if sig:
                    # Place significance star between the two bars
                    max_h = max(idata.get('blind_mean', 0), idata.get('icon_mean', 0))
                    ax.text(item_idx - 1, max_h + 0.6, sig, ha='center', fontsize=10,
                            fontweight='bold', color='#d32f2f')

    # Stats box with interaction test
    stats_lines = []
    interaction = q1.get('interaction_shift', {})
    if interaction.get('p_value') is not None:
        stats_lines.append(f"Interaction (shift x item):")
        stats_lines.append(f"\u03c7\u00b2={interaction['chi2']:.2f}, p={interaction['p_value']:.3f} {interpret_p_value(interaction['p_value'])}")
    # Item-level Wilcoxon summary
    sig_items = [f"It{k}" for k, v in item_bi.items() if v.get('p_bonferroni', 1) < 0.05]
    if sig_items:
        stats_lines.append(f"Wilcoxon sig (Bonf): {', '.join(sig_items)}")
    elif item_bi:
        stats_lines.append(f"Wilcoxon: none sig (Bonf)")
    if stats_lines:
        add_stats_text(ax, '\n'.join(stats_lines), loc='upper right', fontsize=5.5)

    # ---- 2.3: Exact Match by Phase ----
    ax = axes[2, 0]
    em = results.get('exact_match', {}).get('by_phase', {})
    if em:
        x = np.arange(len(PHASE_ORDER))
        width = 0.18
        for i, (true_val, label, color) in enumerate([
            (0, f'Item 1 (=1)', COLORS['rare']),
            (1, f'Item 2 (=1)', '#FF6B6B'),
            (2, f'Item 3 (=4)', COLORS['medium']),
            (3, f'Item 4 (=6)', COLORS['dominant']),
        ]):
            rates = [em.get(p, {}).get('item_rates', [0]*4)[i] for p in PHASE_ORDER]
            ns = [em.get(p, {}).get('n', 1) for p in PHASE_ORDER]
            bars = ax.bar(x + i*width, rates, width, color=color, alpha=0.8, edgecolor='black', linewidth=0.5, label=label)
            # Add raw count on each bar
            for j, (bar, rate, n) in enumerate(zip(bars, rates, ns)):
                count = int(round(rate * n / 100))
                if count > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                            str(count), ha='center', va='bottom', fontsize=6, fontweight='bold')
        ax.set_xticks(x + 1.5*width); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
        ax.set_ylabel('% Exact Match'); ax.legend(fontsize=7, ncol=2)
    ax.set_title('2.7 Exact Match Rate by Phase')

    # ---- 2.4: Exact Match by Role ----
    ax = axes[2, 1]
    em_role = results.get('exact_match', {}).get('by_role', {})
    if em_role:
        x = np.arange(len(PHASE_ORDER))
        w = 0.25
        for offset, role, color in [(-w, 'dominant', COLORS['dominant']), (0, 'medium', COLORS['medium']), (w, 'rare', COLORS['rare'])]:
            rates = [em_role.get(p, {}).get(role, 0) for p in PHASE_ORDER]
            ns = [em.get(p, {}).get('n', 1) for p in PHASE_ORDER]
            bars = ax.bar(x + offset, rates, w, color=color, alpha=0.8, edgecolor='black', linewidth=0.5, label=f'{role.capitalize()}')
            # Add raw count on each bar
            for j, (bar, rate, n) in enumerate(zip(bars, rates, ns)):
                count = int(round(rate * n / 100))
                if count > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                            str(count), ha='center', va='bottom', fontsize=6, fontweight='bold')
        ax.set_xticks(x); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
        ax.set_ylabel('% Exact Match'); ax.legend(fontsize=8)
    ax.set_title('2.8 Exact Match by Item Role')

    # ---- 2.6: Per-item shift (Icon - Blind) ----
    ax = axes[1, 1]
    if len(blind) > 0 and len(icon) > 0:
        blind_means = [blind[f'gen_est_item{i+1}'].dropna().mean() for i in range(4)]
        icon_means = [icon[f'gen_est_item{i+1}'].dropna().mean() for i in range(4)]
        shifts = [ic - bl for ic, bl in zip(icon_means, blind_means)]
        true_shifts = [t - 3 for t in TRUE_DISTRIBUTION]  # shift needed from uniform

        colors_shift = [COLORS['rare'], COLORS['rare'], COLORS['medium'], COLORS['dominant']]
        bars = ax.bar(x_items, shifts, 0.5, color=colors_shift, alpha=0.7, edgecolor='black', linewidth=0.5)
        # True shift direction markers
        ax.scatter(x_items, true_shifts, marker='*', s=150, color=COLORS['true'], zorder=10,
                   label='Needed shift\n(true - uniform)', edgecolor='black')
        ax.axhline(y=0, color='black', lw=0.8)

        # Annotate each bar
        for i, s in enumerate(shifts):
            ax.text(i, s + (0.15 if s >= 0 else -0.25), f'{s:+.2f}',
                    ha='center', fontsize=8, fontweight='bold')

    ax.set_xticks(x_items); ax.set_xticklabels(item_labels)
    ax.set_ylabel('Mean Shift (Icon - Blind)')
    ax.set_title('2.5 Prior Shift: Icon vs Blind')
    ax.legend(fontsize=6, loc='upper left')
    ylim = max(abs(ax.get_ylim()[0]), abs(ax.get_ylim()[1]), 3.5)
    ax.set_ylim(-ylim, ylim)
    ax.fill_between([-0.5, 3.5], 0, ylim, alpha=0.03, color='green')
    ax.fill_between([-0.5, 3.5], -ylim, 0, alpha=0.03, color='red')
    ax.text(3.4, ylim*0.1, 'Increase', fontsize=6, color='green', ha='right', style='italic')
    ax.text(3.4, -ylim*0.1, 'Decrease', fontsize=6, color='red', ha='right', style='italic')

    # ---- 2.8: Position-Free Count Match ----
    ax = axes[1, 2]
    cm = results.get('exact_match', {}).get('count_match', {})
    if cm:
        x_ph = np.arange(4)
        w = 0.15
        metrics = [('has_6', '6 (dom)', COLORS['dominant']),
                   ('has_4', '4 (med)', COLORS['medium']),
                   ('has_1', '1 (rare)', COLORS['rare']),
                   ('full_sorted', '[1,1,4,6]', 'black')]
        for m_idx, (metric, label, color) in enumerate(metrics):
            vals = [cm.get(p, {}).get(metric, 0) for p in PHASE_ORDER]
            ax.bar(x_ph + (m_idx - 1.5) * w, vals, w, color=color, alpha=0.8,
                   edgecolor='black', linewidth=0.5, label=label)
        ax.set_xticks(x_ph); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
        ax.set_ylabel('% with Value Present'); ax.legend(fontsize=6, ncol=2)
    ax.set_title('2.6 Position-Free Count Match')

    # ---- 2.9: Prior Null Distribution (histogram + KDE dual) ----
    ax = axes[2, 2]
    ut = q1.get('uniform_test', {})
    observed_sad = ut.get('mean_diff')
    expected_null = ut.get('expected_null_sad')
    p_sim = ut.get('p_value')

    if observed_sad is not None and expected_null is not None:
        rng_plot = np.random.default_rng(42)
        n_sim_plot = min(N_SIMULATIONS, 10000)
        n_part = len(blind['distance_from_uniform'].dropna())
        null_means = np.zeros(n_sim_plot)
        for s in range(n_sim_plot):
            sim_resp = rng_plot.multinomial(12, [0.25]*4, size=n_part)
            sim_sads = np.sum(np.abs(sim_resp - 3), axis=1)
            null_means[s] = np.mean(sim_sads)

        # Layer 1: Histogram with many bins
        n_unique = len(np.unique(np.round(null_means, 4)))
        n_bins = min(max(n_unique * 2, 80), 150)
        ax.hist(null_means, bins=n_bins, color='#BBDEFB', edgecolor='white',
                linewidth=0.3, alpha=0.5, density=True, label=f'Histogram ({n_bins} bins)')

        # Layer 2: KDE smooth curve
        from scipy.stats import gaussian_kde
        try:
            kde = gaussian_kde(null_means, bw_method=0.15)
            x_range = np.linspace(null_means.min() - 0.5, null_means.max() + 0.5, 300)
            y_kde = kde(x_range)
            ax.plot(x_range, y_kde, color='#1565C0', lw=2, label='KDE (smoothed)')
            ax.fill_between(x_range, y_kde, alpha=0.12, color='#1565C0')
            obs_dev = abs(observed_sad - expected_null) if expected_null else 0
            if obs_dev > 0 and expected_null is not None:
                mask_right = x_range >= (expected_null + obs_dev)
                mask_left = x_range <= (expected_null - obs_dev)
                ax.fill_between(x_range[mask_right], y_kde[mask_right], alpha=0.3, color='#D32F2F')
                ax.fill_between(x_range[mask_left], y_kde[mask_left], alpha=0.3, color='#D32F2F')
        except Exception:
            pass

        ax.axvline(x=observed_sad, color='#D32F2F', lw=2.5, ls='-', label=f'Blind ({observed_sad:.2f})')
        ax.axvline(x=expected_null, color='#1565C0', lw=1.5, ls='--', label=f'Null mean ({expected_null:.2f})')

        # Icon prior observed line (v24)
        icon_test = q1.get('icon_simulation_test', {})
        icon_obs = icon_test.get('observed_mean_sad')
        p_icon = icon_test.get('p_value')
        if icon_obs is not None:
            ax.axvline(x=icon_obs, color='#FF8C00', lw=2.5, ls='-', label=f'Icon ({icon_obs:.2f})')

        if p_sim is not None:
            direction = ut.get('direction', '')
            # Build annotation with both blind and icon results (v24)
            ann_text = f'Blind: p = {p_sim:.4f} {interpret_p_value(p_sim)}'
            if icon_obs is not None and p_icon is not None:
                ann_text += f'\nIcon: p = {p_icon:.4f} {interpret_p_value(p_icon)}'
            ax.text(0.97, 0.95, ann_text,
                    transform=ax.transAxes, fontsize=7, ha='right', va='top',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='gray', alpha=0.9))

        ax.text(0.97, 0.02, f'SAD always even; mean granularity = 2/N',
                transform=ax.transAxes, fontsize=5, ha='right', va='bottom',
                color='gray', style='italic')

        ax.set_xlabel('Mean SAD from Uniform'); ax.set_ylabel('Density')
        ax.legend(fontsize=5.5, loc='upper left')
    else:
        ax.text(0.5, 0.5, 'Insufficient data', transform=ax.transAxes, ha='center')
    ax.set_title('2.9 Prior Test: Blind & Icon vs Null')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 2 saved to: {save_path}")
    return fig


# ============================================================================
# FIGURE 3: LEARNING TRAJECTORY (Q2-Q5, Q5b)
# ============================================================================
# Panels: 3.1 SAD curve, 3.2 Total learning, 3.3 Mean response per item,
#   3.4 Individual trajectories, 3.5 Trajectories by prior type, 3.6 Prior-test correlation

def create_figure3(df, summary_df, results, save_path=None):
    """Figure 3: Learning trajectory analysis Q2-Q5 (4x3)."""
    fig, axes = plt.subplots(4, 3, figsize=(16, 20))
    fig.suptitle('Figure 3: Learning Trajectory', fontsize=14, fontweight='bold')
    q1 = results.get('q1', {})

    # ---- 3.1: SAD Learning Curve ----
    ax = axes[0, 0]
    means = [df[df['trial_type']==p]['distance_from_true'].dropna().mean() for p in PHASE_ORDER]
    sems = [safe_sem(df[df['trial_type']==p]['distance_from_true'].dropna()) for p in PHASE_ORDER]
    x = np.arange(4)
    ax.bar(x, means, yerr=sems, color=[COLORS[p] for p in PHASE_ORDER], capsize=4, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1.5, label=f'Uniform (SAD={UNIFORM_SAD})')
    ax.set_xticks(x); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('SAD'); ax.set_title('3.1 SAD Learning Curve')
    ymax = max(m for m in means if not np.isnan(m))
    ax.set_ylim(0, ymax*1.8); ax.legend(fontsize=7, loc='lower right')
    friedman_res = results.get('friedman', {})
    if friedman_res.get('p_value') is not None and not np.isnan(friedman_res.get('p_value', np.nan)):
        add_stats_text(ax, f"Friedman: \u03c7\u00b2={friedman_res['statistic']:.2f}\np={friedman_res['p_value']:.4f} {interpret_p_value(friedman_res['p_value'])}", loc='upper left', fontsize=7)
    # Significance brackets for all pairwise comparisons (x: 0=Blind,1=Icon,2=T1,3=T2).
    # Adjacent pairs share a level; span pairs are staggered higher. Labels show n.s. too.
    def _pp(key):
        return results.get(key, {}).get('permutation_test', {}).get('p_value', 1)
    add_bracket_labeled(ax, 0, 1, ymax*1.05, _pp('q2'))           # Blind-Icon
    add_bracket_labeled(ax, 1, 2, ymax*1.05, _pp('q3'))           # Icon-T1
    add_bracket_labeled(ax, 2, 3, ymax*1.05, _pp('q4'))           # T1-T2
    add_bracket_labeled(ax, 0, 2, ymax*1.28, _pp('q_blind_t1'))   # Blind-T1 (span)
    add_bracket_labeled(ax, 0, 3, ymax*1.45, _pp('q5'))           # Blind-T2 (span)

    # ---- 3.2: Total Learning (Q5) with jitter ----
    ax = axes[0, 1]
    blind_sad = summary_df['Blind_sad'].dropna().values
    t2_sad = summary_df['T2_sad'].dropna().values
    n_pairs = min(len(blind_sad), len(t2_sad))
    rng_j = np.random.default_rng(42)
    jitter = rng_j.uniform(-0.25, 0.25, size=n_pairs)
    for i in range(n_pairs):
        c = COLORS['learning'] if blind_sad[i]>t2_sad[i] else (COLORS['no_learning'] if blind_sad[i]<t2_sad[i] else 'gray')
        ax.plot([0,1], [blind_sad[i]+jitter[i], t2_sad[i]+jitter[i]], 'o-', color=c, alpha=0.4, markersize=5, linewidth=1.2)
    ax.errorbar([0], [np.mean(blind_sad)], yerr=[safe_sem(blind_sad)], fmt='s', color=COLORS['blind_prior'], markersize=14, capsize=6, label=f'Blind M={np.mean(blind_sad):.1f}', zorder=10, markeredgecolor='black')
    ax.errorbar([1], [np.mean(t2_sad)], yerr=[safe_sem(t2_sad)], fmt='s', color=COLORS['exposure_gen_2'], markersize=14, capsize=6, label=f'T2 M={np.mean(t2_sad):.1f}', zorder=10, markeredgecolor='black')
    ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1, alpha=0.5)
    ax.set_xticks([0,1]); ax.set_xticklabels(['Blind Prior', 'Trial 2']); ax.set_ylabel('SAD')
    ax.set_title('3.2 Total Learning (Q5)'); ax.legend(fontsize=8); ax.set_xlim(-0.4, 1.4)
    ni = int(np.sum(blind_sad[:n_pairs]>t2_sad[:n_pairs]))
    nw = int(np.sum(blind_sad[:n_pairs]<t2_sad[:n_pairs]))
    ns = n_pairs - ni - nw
    q5 = results.get('q5', {})
    add_stats_text(ax, f"N={n_pairs}\nd={q5.get('cliffs_delta',np.nan):.2f}, p={q5.get('permutation_test',{}).get('p_value',np.nan):.3f}\n{ni}\u2191 {nw}\u2193 {ns}\u2194", loc='upper right', fontsize=7)

    # ---- 3.2b: Icon-to-T2 Learning (mirrors 3.2, Icon prior baseline) ----
    ax = axes[0, 2]
    icon_sad = summary_df['Icon_sad'].dropna().values
    t2_sad_b = summary_df['T2_sad'].dropna().values
    n_pairs_b = min(len(icon_sad), len(t2_sad_b))
    rng_jb = np.random.default_rng(42)
    jitter_b = rng_jb.uniform(-0.25, 0.25, size=n_pairs_b)
    for i in range(n_pairs_b):
        c = COLORS['learning'] if icon_sad[i]>t2_sad_b[i] else (COLORS['no_learning'] if icon_sad[i]<t2_sad_b[i] else 'gray')
        ax.plot([0,1], [icon_sad[i]+jitter_b[i], t2_sad_b[i]+jitter_b[i]], 'o-', color=c, alpha=0.4, markersize=5, linewidth=1.2)
    ax.errorbar([0], [np.mean(icon_sad)], yerr=[safe_sem(icon_sad)], fmt='s', color=COLORS['prior_icon'], markersize=14, capsize=6, label=f'Icon M={np.mean(icon_sad):.1f}', zorder=10, markeredgecolor='black')
    ax.errorbar([1], [np.mean(t2_sad_b)], yerr=[safe_sem(t2_sad_b)], fmt='s', color=COLORS['exposure_gen_2'], markersize=14, capsize=6, label=f'T2 M={np.mean(t2_sad_b):.1f}', zorder=10, markeredgecolor='black')
    ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1, alpha=0.5)
    ax.set_xticks([0,1]); ax.set_xticklabels(['Icon Prior', 'Trial 2']); ax.set_ylabel('SAD')
    ax.set_title('3.2b Icon-to-T2 Learning'); ax.legend(fontsize=8); ax.set_xlim(-0.4, 1.4)
    ni_b = int(np.sum(icon_sad[:n_pairs_b]>t2_sad_b[:n_pairs_b]))
    nw_b = int(np.sum(icon_sad[:n_pairs_b]<t2_sad_b[:n_pairs_b]))
    ns_b = n_pairs_b - ni_b - nw_b
    qit = results.get('Q_icon_t2', {})
    add_stats_text(ax, f"N={n_pairs_b}\nd={qit.get('cliffs_delta',np.nan):.2f}, p={qit.get('permutation_test',{}).get('p_value',np.nan):.3f}\n{ni_b}\u2191 {nw_b}\u2193 {ns_b}\u2194", loc='upper right', fontsize=7)

    # ---- Paired dot-plot helper (identical style to 3.2 / 3.2b) ----
    def _paired_panel(ax, lv, rv, l_short, r_short, l_xtick, r_xtick, l_color, r_color, title, qres):
        n = min(len(lv), len(rv))
        rng_p = np.random.default_rng(42)
        jit = rng_p.uniform(-0.25, 0.25, size=n)
        for i in range(n):
            c = COLORS['learning'] if lv[i]>rv[i] else (COLORS['no_learning'] if lv[i]<rv[i] else 'gray')
            ax.plot([0,1], [lv[i]+jit[i], rv[i]+jit[i]], 'o-', color=c, alpha=0.4, markersize=5, linewidth=1.2)
        ax.errorbar([0], [np.mean(lv)], yerr=[safe_sem(lv)], fmt='s', color=l_color, markersize=14, capsize=6, label=f'{l_short} M={np.mean(lv):.1f}', zorder=10, markeredgecolor='black')
        ax.errorbar([1], [np.mean(rv)], yerr=[safe_sem(rv)], fmt='s', color=r_color, markersize=14, capsize=6, label=f'{r_short} M={np.mean(rv):.1f}', zorder=10, markeredgecolor='black')
        ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1, alpha=0.5)
        ax.set_xticks([0,1]); ax.set_xticklabels([l_xtick, r_xtick]); ax.set_ylabel('SAD')
        ax.set_title(title); ax.legend(fontsize=8); ax.set_xlim(-0.4, 1.4)
        ni_ = int(np.sum(lv[:n]>rv[:n])); nw_ = int(np.sum(lv[:n]<rv[:n])); ns_ = n - ni_ - nw_
        add_stats_text(ax, f"N={n}\nd={qres.get('cliffs_delta',np.nan):.2f}, p={qres.get('permutation_test',{}).get('p_value',np.nan):.3f}\n{ni_}\u2191 {nw_}\u2193 {ns_}\u2194", loc='upper right', fontsize=7)

    t1_sad = summary_df['T1_sad'].dropna().values

    # ---- 3.2c: Blind-to-T1 Learning (icon + first exposure, mirrors 3.2) ----
    _paired_panel(axes[1, 0], blind_sad, t1_sad, 'Blind', 'T1', 'Blind Prior', 'Trial 1',
                  COLORS['blind_prior'], COLORS['exposure_gen_1'], '3.2c Blind-to-T1 Learning',
                  results.get('q_blind_t1', {}))

    # ---- 3.2d: Icon-to-T1 Learning (one-shot exposure, mirrors 3.2) ----
    _paired_panel(axes[1, 1], icon_sad, t1_sad, 'Icon', 'T1', 'Icon Prior', 'Trial 1',
                  COLORS['prior_icon'], COLORS['exposure_gen_1'], '3.2d Icon-to-T1 Learning',
                  results.get('q3', {}))

    # ---- 3.2e: T1-to-T2 Learning (repetition, mirrors 3.2) ----
    _paired_panel(axes[1, 2], t1_sad, t2_sad, 'T1', 'T2', 'Trial 1', 'Trial 2',
                  COLORS['exposure_gen_1'], COLORS['exposure_gen_2'], '3.2e T1-to-T2 Learning',
                  results.get('q4', {}))

    # ---- 3.3: Mean Response by Phase (line plot) ----
    ax = axes[2, 0]
    x_items = np.arange(4)
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type']==phase]
        m = [pdf[f'gen_est_item{i}'].mean() for i in range(1,5)]
        s = [safe_sem(pdf[f'gen_est_item{i}']) for i in range(1,5)]
        ax.errorbar(x_items, m, yerr=s, fmt='o-', color=COLORS[phase], label=PHASE_SHORT[phase], lw=2, markersize=6, capsize=3)
    ax.plot(x_items, TRUE_DISTRIBUTION, 's--', color=COLORS['true'], lw=2, markersize=8, label='True', alpha=0.9, markeredgecolor='black')
    ax.set_xticks(x_items); ax.set_xticklabels(['Item 1\n(rare)', 'Item 2\n(rare)', 'Item 3\n(med)', 'Item 4\n(dom)'])
    ax.set_ylabel('Mean Estimate'); ax.set_title('3.3 Mean Response by Phase')
    ax.legend(fontsize=7, ncol=3, loc='upper left'); ax.set_ylim(0, 8)

    # ---- 3.4: Individual Trajectories ----
    ax = axes[2, 1]
    for _, row in summary_df.iterrows():
        traj = [row.get(f'{p}_sad', np.nan) for p in ['Blind','Icon','T1','T2']]
        ax.plot(range(4), traj, 'o-', color='gray', alpha=0.25, markersize=3)
    mt = [summary_df[f'{p}_sad'].mean() for p in ['Blind','Icon','T1','T2']]
    ax.plot(range(4), mt, 'o-', color='black', lw=3, markersize=10, label='Mean', zorder=10)
    ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1, alpha=0.5)
    ax.set_xticks(range(4)); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('SAD'); ax.set_title('3.4 Individual Trajectories'); ax.legend(fontsize=8); ax.set_ylim(0, MAX_SAD)

    # ---- 3.5: Trajectories by Prior Shape ----
    ax = axes[2, 2]
    classifications = q1.get('classifications', [])
    blind_df = df[df['trial_type']=='blind_prior'].sort_values('subject_nr')
    subj_order = blind_df['subject_nr'].values
    subj_class = {subj: classifications[i] for i, subj in enumerate(subj_order) if i < len(classifications)}
    legend_added = set()
    for _, row in summary_df.iterrows():
        subj = row['subject_nr']
        traj = [row.get(f'{p}_sad', np.nan) for p in ['Blind','Icon','T1','T2']]
        st = subj_class.get(subj, 'unknown')
        c = SHAPE_COLORS.get(st, 'gray')
        lbl = st if st not in legend_added else None
        if lbl: legend_added.add(st)
        ax.plot(range(4), traj, 'o-', color=c, alpha=0.5, markersize=5, linewidth=1.5, label=lbl)
    ax.plot(range(4), mt, 'o-', color='black', lw=3, markersize=10, label='Mean', zorder=10)
    ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1, alpha=0.5)
    ax.set_xticks(range(4)); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('SAD'); ax.set_title('3.5 Trajectories by Prior Shape'); ax.legend(fontsize=7); ax.set_ylim(0, MAX_SAD)

    # ---- 3.6: Prior-Test Correlation ----
    ax = axes[3, 0]
    prior_sads, test_sads, shapes = [], [], []
    for _, row in summary_df.iterrows():
        vals = [row.get(f'{p}_sad', np.nan) for p in ['Blind','Icon','T1','T2']]
        if not any(pd.isna(vals)):
            prior_sads.append((vals[0]+vals[1])/2)
            test_sads.append((vals[2]+vals[3])/2)
            shapes.append(subj_class.get(row['subject_nr'], 'unknown'))
    if len(prior_sads) > 2:
        pa, ta = np.array(prior_sads), np.array(test_sads)
        for px, ty, sh in zip(pa, ta, shapes):
            ax.scatter(px, ty, color=SHAPE_COLORS.get(sh,'gray'), s=60, edgecolor='black', linewidth=0.5, alpha=0.7)
        z = np.polyfit(pa, ta, 1); x_line = np.linspace(min(pa), max(pa), 100)
        ax.plot(x_line, np.poly1d(z)(x_line), '--', color='black', lw=1.5, alpha=0.7)
        rho, p = stats.spearmanr(pa, ta)
        add_stats_text(ax, f"N={len(pa)}\n\u03c1={rho:.2f}, p={p:.3f}", loc='upper left', fontsize=8)
        ax.axhline(y=UNIFORM_SAD, color='gray', ls='--', lw=1, alpha=0.3)
        ax.axvline(x=UNIFORM_SAD, color='gray', ls='--', lw=1, alpha=0.3)
    ax.set_xlabel('Prior SAD (mean Blind+Icon)'); ax.set_ylabel('Test SAD (mean T1+T2)')
    ax.set_title('3.6 Prior vs Test Quality (Q5b)')

    # Hide unused slots in the 4x3 grid (row 3, cols 1-2)
    axes[3, 1].axis('off')
    axes[3, 2].axis('off')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 3 saved to: {save_path}")
    return fig


# ============================================================================
# FIGURE 4: ITEM ESTIMATION (Q6)
# ============================================================================
# Panels: 4.1 Estimates vs true, 4.2 Error by phase, 4.3 Error by role, 4.4 Bias

def create_figure4(df, summary_df, results, save_path=None):
    """Figure 4: Item-specific estimation Q6 + alternative errors + distribution fit (2x3)."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Figure 4: Item Estimation Analysis (Q6)', fontsize=14, fontweight='bold')
    x_items = np.arange(4)
    item_labels = ['Item 1\n(rare)', 'Item 2\n(rare)', 'Item 3\n(med)', 'Item 4\n(dom)']

    # ---- 4.1: Final Estimates vs True ----
    ax = axes[0, 0]
    t2_df = df[df['trial_type']=='exposure_gen_2']
    t2_m = [t2_df[f'gen_est_item{i}'].mean() for i in range(1,5)]
    t2_s = [safe_sem(t2_df[f'gen_est_item{i}']) for i in range(1,5)]
    ax.bar(x_items-0.2, TRUE_DISTRIBUTION, 0.35, color=COLORS['true'], label='True', alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.bar(x_items+0.2, t2_m, 0.35, yerr=t2_s, color=COLORS['exposure_gen_2'], label='T2 Estimate', alpha=0.8, capsize=3, edgecolor='black', linewidth=0.5)
    ax.set_xticks(x_items); ax.set_xticklabels(item_labels); ax.set_ylabel('Count')
    ax.set_title('4.1 Final Estimates vs True'); ax.legend(fontsize=8); ax.set_ylim(0, 8)

    # ---- 4.2: Item Error by Phase ----
    ax = axes[0, 1]
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type']==phase]
        errors = [np.abs(pdf[f'gen_est_item{j+1}']-TRUE_DISTRIBUTION[j]).mean() for j in range(4)]
        sems_e = [safe_sem(np.abs(pdf[f'gen_est_item{j+1}']-TRUE_DISTRIBUTION[j])) for j in range(4)]
        ax.errorbar(x_items, errors, yerr=sems_e, fmt='o-', color=COLORS[phase], label=PHASE_SHORT[phase], lw=2, markersize=6, capsize=3)
    ax.set_xticks(x_items); ax.set_xticklabels(item_labels); ax.set_ylabel('Mean Absolute Error')
    ax.set_title('4.2 Item Error by Phase'); ax.legend(fontsize=8)

    # ---- 4.3: Error by Item Role ----
    ax = axes[0, 2]
    role_err = {'dominant': [], 'medium': [], 'rare': []}
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type']==phase]
        role_err['dominant'].append(np.abs(pdf['gen_est_item4']-6).mean())
        role_err['medium'].append(np.abs(pdf['gen_est_item3']-4).mean())
        role_err['rare'].append((np.abs(pdf['gen_est_item1']-1).mean()+np.abs(pdf['gen_est_item2']-1).mean())/2)
    x = np.arange(len(PHASE_ORDER)); w = 0.25
    ax.bar(x-w, role_err['dominant'], w, color=COLORS['dominant'], label='Dominant (6)', alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.bar(x, role_err['medium'], w, color=COLORS['medium'], label='Medium (4)', alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.bar(x+w, role_err['rare'], w, color=COLORS['rare'], label='Rare (1)', alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('Mean Absolute Error'); ax.set_title('4.3 Error by Item Role (Q6)'); ax.legend(fontsize=7)
    dvr = results.get('q6',{}).get('dom_vs_rare',{})
    if dvr:
        add_stats_text(ax, f"Dom vs Rare (T2):\nd={dvr.get('cliffs_delta',np.nan):.2f}, p={dvr.get('p_value',np.nan):.3f}", loc='upper left', fontsize=7)

    # ---- 4.4: Estimation Bias ----
    ax = axes[1, 0]
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type']==phase]
        if len(pdf) == 0: continue
        biases = [(pdf[f'gen_est_item{i}']-TRUE_DISTRIBUTION[i-1]).mean() for i in range(1,5)]
        ax.plot(x_items, biases, 'o-', color=COLORS[phase], label=PHASE_SHORT[phase], lw=2, markersize=6)
    ax.axhline(y=0, color='black', ls='-', lw=0.5)
    ax.set_xticks(x_items); ax.set_xticklabels(item_labels); ax.set_ylabel('Bias (Estimate - True)')
    ax.set_title('4.4 Estimation Bias'); ax.legend(fontsize=7, ncol=2)
    ylim = ax.get_ylim()
    ax.fill_between([-0.5, 3.5], 0, max(ylim[1], 1), alpha=0.05, color='red')
    ax.fill_between([-0.5, 3.5], min(ylim[0], -1), 0, alpha=0.05, color='blue')
    ax.text(3.4, 0.3, 'Over', fontsize=7, color='red', ha='right', style='italic')
    ax.text(3.4, -0.3, 'Under', fontsize=7, color='blue', ha='right', style='italic')

    # ---- 4.5: Alternative Error Measures (learning curves with 3 exponents) ----
    ax = axes[1, 1]
    alt_err = results.get('alt_errors', {}).get('by_phase', {})
    exp_colors = {1.0: '#2196F3', 1.72: '#FF9800', 2.0: '#E91E63'}
    exp_labels_map = {1.0: 'SAD (p=1)', 1.72: 'CNS (p=1.72)', 2.0: 'SSE (p=2)'}
    exp_markers = {1.0: 'o', 1.72: 's', 2.0: 'D'}
    x_phases = np.arange(4)

    for exp in [1.0, 1.72, 2.0]:
        means, sems_exp = [], []
        for phase in PHASE_ORDER:
            pd_exp = alt_err.get(phase, {}).get(exp, {})
            means.append(pd_exp.get('mean', np.nan))
            sems_exp.append(pd_exp.get('sem', 0))
        ax.errorbar(x_phases, means, yerr=sems_exp, fmt=f'{exp_markers[exp]}-',
                     color=exp_colors[exp], label=exp_labels_map[exp],
                     lw=2, markersize=7, capsize=3)

    ax.set_xticks(x_phases); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('Error (sum of |e|^p)'); ax.set_title('4.5 Alternative Error Measures')
    ax.legend(fontsize=7, loc='upper right')

    # Add Friedman p-values as annotation
    friedman_tests = results.get('alt_errors', {}).get('friedman_tests', {})
    f_lines = []
    for exp, lbl in [(1.0, 'SAD'), (1.72, 'CNS'), (2.0, 'SSE')]:
        ft = friedman_tests.get(exp, {})
        if ft.get('p_value') is not None:
            f_lines.append(f"{lbl}: p={ft['p_value']:.3f} {interpret_p_value(ft['p_value'])}")
    if f_lines:
        add_stats_text(ax, 'Friedman:\n' + '\n'.join(f_lines), loc='upper left', fontsize=6)

    # ---- 4.6: Distribution Fit (Chi-square GoF by phase) ----
    ax = axes[1, 2]
    dist_fit = results.get('dist_fit', {}).get('by_phase', {})

    if dist_fit:
        chi2_means = [dist_fit.get(p, {}).get('chi2_mean', np.nan) for p in PHASE_ORDER]
        chi2_sems = [safe_sem(dist_fit.get(p, {}).get('chi2_values', [])) for p in PHASE_ORDER]
        ks_means = [dist_fit.get(p, {}).get('ks_mean', np.nan) for p in PHASE_ORDER]

        # Chi-square as bars
        bars = ax.bar(x_phases, chi2_means, yerr=chi2_sems,
                      color=[COLORS[p] for p in PHASE_ORDER], alpha=0.7,
                      capsize=4, edgecolor='black', linewidth=0.5)

        # % fitting as text on bars
        for i, phase in enumerate(PHASE_ORDER):
            pct = dist_fit.get(phase, {}).get('pct_fit', 0)
            ax.text(i, chi2_means[i] + (chi2_sems[i] if chi2_sems[i] else 0) + 0.3,
                    f'{pct:.0f}%', ha='center', fontsize=7, color='green', fontweight='bold')

        # KS overlay on secondary axis
        ax2 = ax.twinx()
        ax2.plot(x_phases, ks_means, 'D--', color='#9C27B0', markersize=7, lw=1.5, label='KS stat')
        ax2.set_ylabel('KS Statistic', color='#9C27B0', fontsize=8)
        ax2.tick_params(axis='y', labelcolor='#9C27B0')

        ax.set_xticks(x_phases); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
        ax.set_ylabel('Chi-square GoF')
        ax.set_title('4.6 Distribution Fit (lower = better)')

        # Friedman annotation
        chi2f = results.get('dist_fit', {}).get('chi2_friedman', {})
        note = '%fit: p(chi2)>0.05'
        if chi2f.get('p_value') is not None:
            note += f"\nFriedman: p={chi2f['p_value']:.3f}"
        add_stats_text(ax, note, loc='upper right', fontsize=6)

        # Legend combining both axes
        from matplotlib.lines import Line2D
        ax.legend(handles=[
            Line2D([0],[0], color='gray', marker='s', ls='', label='Chi-sq (bars)', markersize=6),
            Line2D([0],[0], color='#9C27B0', marker='D', ls='--', label='KS (line)', markersize=6),
        ], fontsize=7, loc='upper left')
    else:
        ax.text(0.5, 0.5, 'Insufficient data', transform=ax.transAxes, ha='center', fontsize=10)
        ax.set_title('4.6 Distribution Fit')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 4 saved to: {save_path}")
    return fig


# ============================================================================
# FIGURE 5: TIMING ANALYSIS - Expanded 2x3 with raincloud + histogram + table
# ============================================================================
# 5.1 Timing decomposition (stacked bar)
# 5.2 RT raincloud (half-violin + strip + box) by phase
# 5.3 RT Descriptive Table (standalone large panel)
# 5.4 RT Histogram by phase
# 5.5 Completion raincloud (half-violin + strip + box)
# 5.6 Timing vs accuracy (improved with regression lines)

def _draw_raincloud(ax, data_list, positions, phase_order, colors):
    """Draw raincloud plot: half-violin (left) + box (center) + strip (right)."""
    from matplotlib.lines import Line2D
    rng_j = np.random.default_rng(42)

    for i, (vals, phase) in enumerate(zip(data_list, phase_order)):
        pos = positions[i]
        if len(vals) < 2:
            ax.scatter([pos]*len(vals), vals, s=15, alpha=0.6, color=colors[phase],
                       edgecolor='black', linewidth=0.3, zorder=5)
            continue

        # Half-violin (left side)
        from scipy.stats import gaussian_kde
        try:
            kde = gaussian_kde(vals, bw_method=0.3)
            y_range = np.linspace(vals.min(), vals.max(), 100)
            density = kde(y_range)
            density_scaled = density / density.max() * 0.35
            ax.fill_betweenx(y_range, pos - density_scaled, pos,
                             alpha=0.35, color=colors[phase], zorder=2)
        except Exception:
            pass  # Skip KDE if insufficient data

        # Box (narrow, centered)
        bp = ax.boxplot([vals], positions=[pos], widths=0.12, patch_artist=True,
                        showfliers=False, zorder=4)
        bp['boxes'][0].set_facecolor(colors[phase])
        bp['boxes'][0].set_alpha(0.7)
        bp['medians'][0].set_color('red')
        bp['medians'][0].set_linewidth(1.5)

        # Strip dots (right side, jittered)
        jy = rng_j.uniform(0.08, 0.28, size=len(vals))
        ax.scatter(pos + jy, vals, s=12, alpha=0.5, color=colors[phase],
                   edgecolor='black', linewidth=0.2, zorder=5)

        # Mean diamond
        ax.plot(pos, np.mean(vals), 'D', color='black', markersize=5, zorder=10)

    ax.legend(handles=[
        Line2D([0],[0], marker='D', color='black', ls='', label='Mean', markersize=5),
        Line2D([0],[0], color='red', lw=1.5, label='Median'),
    ], fontsize=6, loc='upper right')


def create_figure5(df, summary_df, results, save_path=None):
    """Figure 5: Timing analysis with raincloud, histogram, table (2x3)."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle('Figure 5: Timing Analysis', fontsize=14, fontweight='bold')
    rt_res = results.get('rt', {})

    # Collect RT and Completion data
    rt_data, comp_data = [], []
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type']==phase]
        rt_data.append(pdf['gen_rt'].dropna().values / 1000)
        comp_data.append(pdf['gen_completion_time'].dropna().values / 1000 if 'gen_completion_time' in pdf.columns else np.array([]))

    positions = np.arange(1, 5)

    # ---- 5.1: Timing Decomposition (stacked bar) ----
    ax = axes[0, 0]
    x = np.arange(len(PHASE_ORDER))
    rt_m, delib_m = [], []
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type']==phase]
        rt_m.append(pdf['gen_rt'].dropna().mean()/1000 if 'gen_rt' in pdf.columns else 0)
        delib_m.append(max(pdf['deliberation_time'].dropna().mean()/1000 if 'deliberation_time' in pdf.columns else 0, 0))
    ax.bar(x, rt_m, 0.55, label='First Click RT', color=[COLORS[p] for p in PHASE_ORDER], alpha=0.9, edgecolor='black', linewidth=0.5)
    ax.bar(x, delib_m, 0.55, bottom=rt_m, label='Deliberation', color=[COLORS[p] for p in PHASE_ORDER], alpha=0.4, edgecolor='black', linewidth=0.5, hatch='//')
    ax.set_xticks(x); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('Time (seconds)'); ax.set_title('5.1 Timing Decomposition'); ax.legend(fontsize=7)
    for i, (r, d) in enumerate(zip(rt_m, delib_m)):
        ax.text(i, r+d+0.5, f'{r+d:.0f}s', ha='center', fontsize=7)

    # ---- 5.2: RT Raincloud by Phase ----
    ax = axes[0, 1]
    _draw_raincloud(ax, rt_data, positions, PHASE_ORDER, COLORS)
    ax.set_xticks(positions); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('First Click RT (seconds)'); ax.set_title('5.2 RT Raincloud by Phase')
    # Friedman annotation
    rt_friedman = rt_res.get('rt_friedman', {})
    if rt_friedman.get('statistic') is not None:
        add_stats_text(ax, f"Friedman: \u03c7\u00b2={rt_friedman['statistic']:.1f}, p={rt_friedman['p_value']:.3f} {interpret_p_value(rt_friedman['p_value'])}", loc='upper left', fontsize=7)

    # ---- 5.3: RT Descriptive Table (standalone, large) ----
    ax = axes[0, 2]
    ax.axis('off')
    ax.set_title('5.3 RT Descriptive Statistics', fontsize=11, fontweight='bold', pad=10)

    rt_dist = rt_res.get('rt_distribution', {})
    col_labels = ['Phase', 'N', 'M(s)', 'SD(s)', 'Mdn(s)', 'MAD(s)', 'Skew', 'Kurt',
                  'Out', 'Cl_M(s)', 'Cl_SD(s)']
    table_rows = []
    for phase in PHASE_ORDER:
        d = rt_dist.get(phase, {})
        bp = rt_res.get('by_phase', {}).get(phase, {}).get('rt', {})
        if d:
            table_rows.append([
                PHASE_SHORT[phase],
                str(d.get('n_raw', '-')),
                f"{d['raw_mean']/1000:.1f}", f"{d['raw_sd']/1000:.1f}",
                f"{bp.get('median', d['raw_mean'])/1000:.1f}",
                f"{bp.get('mad', 0)/1000:.1f}" if bp.get('mad') and not pd.isna(bp.get('mad', np.nan)) else "-",
                f"{d['skewness']:.2f}" if not np.isnan(d.get('skewness', np.nan)) else "-",
                f"{d['kurtosis']:.2f}" if not np.isnan(d.get('kurtosis', np.nan)) else "-",
                str(d.get('n_outliers', 0)),
                f"{d['cleaned_mean']/1000:.1f}" if not np.isnan(d.get('cleaned_mean', np.nan)) else "-",
                f"{d['cleaned_sd']/1000:.1f}" if not np.isnan(d.get('cleaned_sd', np.nan)) else "-",
            ])
        else:
            table_rows.append([PHASE_SHORT[phase]] + ['-']*10)

    if table_rows:
        table = ax.table(cellText=table_rows, colLabels=col_labels, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.0, 1.6)
        for j in range(len(col_labels)):
            table[0, j].set_height(0.14)
            table[0, j].set_facecolor('#FF8C00')
            table[0, j].set_text_props(color='white', fontweight='bold', fontsize=7)
        for i in range(len(table_rows)):
            table[i+1, 0].set_facecolor(COLORS[PHASE_ORDER[i]])
            table[i+1, 0].set_text_props(color='white', fontweight='bold')
            # Highlight outlier column if outliers exist
            if table_rows[i][8] != '0' and table_rows[i][8] != '-':
                table[i+1, 8].set_facecolor('#FFCCCC')
        ax.text(0.5, 0.05, 'Out = outliers (2.5 SD/phase); Cl = cleaned after removal',
                ha='center', fontsize=7, style='italic', transform=ax.transAxes, color='gray')

    # ---- 5.4: RT Histogram by Phase ----
    ax = axes[1, 0]
    for i, (vals, phase) in enumerate(zip(rt_data, PHASE_ORDER)):
        if len(vals) > 0:
            ax.hist(vals, bins='auto', alpha=0.4, color=COLORS[phase],
                    label=PHASE_SHORT[phase], edgecolor='black', linewidth=0.3, density=True)
    ax.set_xlabel('First Click RT (seconds)'); ax.set_ylabel('Density')
    ax.set_title('5.4 RT Histogram by Phase'); ax.legend(fontsize=7)

    # ---- 5.5: Completion Raincloud by Phase ----
    ax = axes[1, 1]
    _draw_raincloud(ax, comp_data, positions, PHASE_ORDER, COLORS)
    ax.set_xticks(positions); ax.set_xticklabels([PHASE_SHORT[p] for p in PHASE_ORDER])
    ax.set_ylabel('Completion Time (seconds)'); ax.set_title('5.5 Completion Raincloud by Phase')
    comp_friedman = rt_res.get('comp_friedman', {})
    if comp_friedman.get('statistic') is not None:
        add_stats_text(ax, f"Friedman: \u03c7\u00b2={comp_friedman['statistic']:.1f}, p={comp_friedman['p_value']:.3f} {interpret_p_value(comp_friedman['p_value'])}", loc='upper left', fontsize=7)

    # ---- 5.6: Timing vs Accuracy (T2, improved) ----
    ax = axes[1, 2]
    t2 = df[df['trial_type']=='exposure_gen_2']
    stat_lines = []
    from matplotlib.lines import Line2D
    for measure, label, marker, color in [
        ('gen_rt', 'RT', 'o', COLORS['exposure_gen_1']),
        ('gen_completion_time', 'Completion', 's', COLORS['blind_prior']),
        ('deliberation_time', 'Deliberation', '^', COLORS['exposure_gen_2']),
    ]:
        if measure in t2.columns and 'distance_from_true' in t2.columns:
            vals = t2[measure].dropna()/1000
            sad = t2.loc[vals.index, 'distance_from_true'].dropna()
            vi = vals.index.intersection(sad.index)
            if len(vi) >= 2:
                ax.scatter(vals.loc[vi], sad.loc[vi], alpha=0.5, s=60, color=color,
                           edgecolor='black', marker=marker, label=label, linewidth=0.5)
                # Add regression line if enough points
                if len(vi) >= 5:
                    z = np.polyfit(vals.loc[vi].values, sad.loc[vi].values, 1)
                    x_line = np.linspace(vals.loc[vi].min(), vals.loc[vi].max(), 50)
                    ax.plot(x_line, np.polyval(z, x_line), '--', color=color, alpha=0.5, lw=1.5)
                if len(vi) > 2:
                    rho, rp = stats.spearmanr(vals.loc[vi], sad.loc[vi])
                    stat_lines.append(f'{label}: \u03c1={rho:.2f}, p={rp:.2f}')
    ax.set_xlabel('Time (seconds)'); ax.set_ylabel('T2 SAD'); ax.set_title('5.6 Timing vs Accuracy (T2)')
    ax.legend(fontsize=7, loc='upper left')
    if stat_lines:
        add_stats_text(ax, '\n'.join(stat_lines), loc='lower right', fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 5 saved to: {save_path}")
    return fig


# ============================================================================
# FIGURE 6: SELF-REPORT VALIDATION (Q7) - Hebrew question text
# ============================================================================
# Each panel header shows English label on line 1, Hebrew text on line 2,
# preventing mixed-direction overlap. Summary table applies bidi to Hebrew values.

def create_figure6(df, summary_df, results, save_path=None):
    """Figure 6: Self-report validation Q7 (2x3, Hebrew RTL)."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 11))
    fig.suptitle('Figure 6: Self-Report Validation (Q7)', fontsize=14, fontweight='bold')
    q7 = results.get('q7', {})

    def add_q_header(ax, q_key, panel_label, y_offset=1.02):
        """Add panel label + Hebrew question as yellow header box (replaces ax.set_title)."""
        q_data = Q_TEXTS.get(q_key, None)
        if q_data:
            eng, heb = q_data
            heb_w = hebrew_wrap(heb, width=45)
            ax.set_title(panel_label, fontsize=10, pad=35)
            ax.text(0.5, y_offset, f"{eng}\n{heb_w}", transform=ax.transAxes, fontsize=7, ha='center', va='bottom',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9, edgecolor='#cccccc'), linespacing=1.3)

    # ---- 6.1: Q1 Blind Strategy ----
    ax = axes[0, 0]
    add_q_header(ax, 'q1', '6.1 Blind Prior Strategy')
    q1d = q7.get('q1_distribution', {})
    if q1d:
        labels = [truncate_hebrew(str(k), 25) for k in q1d.keys()]
        values = list(q1d.values())
        ax.barh(np.arange(len(labels)), values, color=plt.cm.Set2(np.linspace(0,1,len(labels))), edgecolor='black', linewidth=0.5)
        ax.set_yticks(np.arange(len(labels))); ax.set_yticklabels(labels, fontsize=7); ax.set_xlabel('Count')
        for i, v in enumerate(values):
            ax.text(v+0.1, i, str(v), va='center', fontsize=8)

    # ---- 6.2: Q2 Icon Strategy ----
    ax = axes[0, 1]
    add_q_header(ax, 'q2', '6.2 Icon Prior Strategy')
    q2d = q7.get('q2_distribution', {})
    if q2d:
        labels = [truncate_hebrew(str(k), 25) for k in q2d.keys()]
        values = list(q2d.values())
        ax.barh(np.arange(len(labels)), values, color=plt.cm.Set3(np.linspace(0,1,len(labels))), edgecolor='black', linewidth=0.5)
        ax.set_yticks(np.arange(len(labels))); ax.set_yticklabels(labels, fontsize=7); ax.set_xlabel('Count')

    # ---- 6.3: Q3 Understanding vs Performance ----
    ax = axes[0, 2]
    add_q_header(ax, 'q3', '6.3 Understanding vs Performance')
    if 'post_q3_task_understanding' in summary_df.columns and 'T2_sad' in summary_df.columns:
        und = summary_df['post_q3_task_understanding'].dropna()
        t2s = summary_df.loc[und.index, 'T2_sad'].dropna()
        vi = und.index.intersection(t2s.index)
        if len(vi) > 0:
            xv, yv = und.loc[vi].values, summary_df.loc[vi, 'T2_sad'].values
            ax.scatter(xv, yv, alpha=0.6, s=60, color=COLORS['exposure_gen_2'], edgecolor='black')
            if len(vi) > 2:
                z = np.polyfit(xv, yv, 1); ax.plot(np.linspace(min(xv),max(xv),100), np.poly1d(z)(np.linspace(min(xv),max(xv),100)), '--', color='black', lw=1.5, alpha=0.7)
                rho, rp = stats.spearmanr(xv, yv)
                add_stats_text(ax, f"\u03c1 = {rho:.2f}\np = {rp:.3f}", fontsize=8)
    ax.set_xlabel('Task Understanding (1-6)'); ax.set_ylabel('T2 SAD (lower = better)')

    # ---- 6.4: Q4 Strategy vs T1 ----
    ax = axes[1, 0]
    add_q_header(ax, 'q4', '6.4 Strategy vs T1 Accuracy')
    q4d = q7.get('q4_by_strategy', {})
    if q4d:
        labels = [truncate_hebrew(str(k), 25) for k in q4d.keys()]
        means = [v['mean'] for v in q4d.values()]
        ns = [v['n'] for v in q4d.values()]
        ax.barh(np.arange(len(labels)), means, color=plt.cm.Pastel1(np.linspace(0,1,len(labels))), edgecolor='black', linewidth=0.5)
        ax.set_yticks(np.arange(len(labels))); ax.set_yticklabels(labels, fontsize=7); ax.set_xlabel('Mean T1 SAD')
        for i, (m, n) in enumerate(zip(means, ns)):
            ax.text(m+0.1, i, f'M={m:.1f} (n={n})', va='center', fontsize=7)

    # ---- 6.5: Q5 Learning Source ----
    ax = axes[1, 1]
    add_q_header(ax, 'q5', '6.5 Learning Source (Q5)')
    q5d = q7.get('q5_distribution', {})
    if q5d:
        labels = [truncate_hebrew(str(k), 25) for k in q5d.keys()]
        values = list(q5d.values()); total = sum(values); pcts = [100*v/total for v in values]
        ax.barh(np.arange(len(labels)), pcts, color=plt.cm.Set2(np.linspace(0,1,len(labels))), edgecolor='black', linewidth=0.5)
        ax.set_yticks(np.arange(len(labels))); ax.set_yticklabels(labels, fontsize=7); ax.set_xlabel('% of Participants')
        for i, (pct, cnt) in enumerate(zip(pcts, values)):
            ax.text(pct+1, i, f'{pct:.0f}% (n={cnt})', va='center', fontsize=7)

    # ---- 6.6: Summary Table ----
    ax = axes[1, 2]
    ax.axis('off'); ax.set_title('6.6 Self-Report Summary', fontsize=10)
    rows = [['Question', 'Key Finding']]
    q3c = q7.get('q3_correlation', {})
    rho_v = q3c.get('rho', np.nan); p_v = q3c.get('p_value', np.nan)
    rows.append(['Q3: Understanding', f"\u03c1={rho_v:.2f}, p={p_v:.3f}" if not np.isnan(rho_v) else 'N/A'])
    if q7.get('q1_distribution'):
        top = max(q7['q1_distribution'], key=q7['q1_distribution'].get)
        rows.append(['Q1: Blind strategy', truncate_hebrew(str(top), 28)])
    if q7.get('q5_distribution'):
        top = max(q7['q5_distribution'], key=q7['q5_distribution'].get)
        cnt = q7['q5_distribution'][top]
        rows.append(['Q5: Learning source', f'{truncate_hebrew(str(top), 25)} (n={cnt})'])
    if len(rows) > 1:
        t = ax.table(cellText=rows[1:], colLabels=rows[0], cellLoc='left', loc='center')
        t.auto_set_font_size(False); t.set_fontsize(8); t.scale(1.0, 1.8)
        t[0,0].set_facecolor('#4472C4'); t[0,0].set_text_props(color='white', fontweight='bold')
        t[0,1].set_facecolor('#4472C4'); t[0,1].set_text_props(color='white', fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 6 saved to: {save_path}")
    return fig

def save_summary_table(summary_df, output_path):
    """Save per-subject summary table."""
    summary_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    report(f"Summary table saved to: {output_path}")

def save_descriptive_table(results, output_path):
    """Save comprehensive descriptive statistics to CSV."""
    rows = []
    desc = results.get('descriptives', {}).get('by_phase', {})

    for phase in PHASE_ORDER:
        ps = desc.get(phase, {})
        s = ps.get('sad', {})
        e = ps.get('entropy', {})
        gs = ps.get('gini_simpson', {})
        r = ps.get('rt', {})
        comp = ps.get('completion', {})

        row = {
            'Phase': PHASE_LABELS.get(phase, phase),
            'SAD_Mean': s.get('mean', np.nan),
            'SAD_Median': s.get('median', np.nan),
            'SAD_Mode': s.get('mode', np.nan),
            'SAD_SD': s.get('sd', np.nan),
            'SAD_MAD': s.get('mad', np.nan),
            'SAD_IQR': s.get('iqr', np.nan),
            'SAD_Min': s.get('min', np.nan),
            'SAD_Max': s.get('max', np.nan),
            'SAD_SEM': s.get('sem', np.nan),
            'SAD_N': s.get('n', np.nan),
            'Entropy_Mean': e.get('mean', np.nan),
            'Entropy_SD': e.get('sd', np.nan),
            'Entropy_Median': e.get('median', np.nan),
            'GiniSimpson_Mean': gs.get('mean', np.nan),
            'GiniSimpson_SD': gs.get('sd', np.nan),
            'GiniSimpson_Median': gs.get('median', np.nan),
            'RT_Mean': r.get('mean', np.nan),
            'RT_Median': r.get('median', np.nan),
            'RT_SD': r.get('sd', np.nan),
            'RT_IQR': r.get('iqr', np.nan),
            'Completion_Mean': comp.get('mean', np.nan),
            'Completion_Median': comp.get('median', np.nan),
            'Completion_SD': comp.get('sd', np.nan),
        }

        # Deliberation time (from timing results if available)
        delib = ps.get('deliberation', {})
        row['Deliberation_Mean'] = delib.get('mean', np.nan)
        row['Deliberation_Median'] = delib.get('median', np.nan)
        row['Deliberation_SD'] = delib.get('sd', np.nan)

        # RT proportion
        rt_prop = ps.get('rt_proportion', {})
        row['RT_Proportion_Mean'] = rt_prop.get('mean', np.nan)

        # Item estimates
        for i in range(1, 5):
            ei = ps.get(f'est_item{i}', {})
            row[f'Est_Item{i}_Mean'] = ei.get('mean', np.nan)
            row[f'Est_Item{i}_SD'] = ei.get('sd', np.nan)

        rows.append(row)

    if rows:
        pd.DataFrame(rows).to_csv(output_path, index=False)
        report(f"Descriptive table saved to: {output_path}")

def save_statistical_results(results, output_path):
    """Save all statistical test results to CSV."""
    rows = []

    # Q1: Prior vs uniform
    q1 = results.get('q1', {})
    ut = q1.get('uniform_test', {})
    if ut:
        rows.append({
            'Test': 'Q1: Prior vs Uniform (permutation)',
            'Statistic': ut.get('mean_diff', np.nan),
            'p_value': ut.get('p_value', np.nan),
            'Effect_Size': np.nan,
            'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': results.get('descriptives', {}).get('n_subjects', np.nan),
            'Significance': interpret_p_value(ut.get('p_value', 1))
        })

    # Q1: Bootstrap CIs for items
    for i in range(4):
        ci = q1.get(f'item{i + 1}_bootstrap_ci', (np.nan, np.nan))
        rows.append({
            'Test': f'Q1: Item {i + 1} mean bootstrap CI',
            'Statistic': q1.get('mean_response', [np.nan] * 4)[i] if q1.get('mean_response') else np.nan,
            'p_value': np.nan,
            'Effect_Size': np.nan,
            'CI_Lower': ci[0], 'CI_Upper': ci[1],
            'N': np.nan,
            'Significance': 'Sig' if (ci[0] > 3 or ci[1] < 3) else 'n.s.' if not np.isnan(ci[0]) else ''
        })

    # Friedman
    friedman = results.get('friedman', {})
    if friedman.get('statistic') is not None:
        rows.append({
            'Test': 'Friedman omnibus (4 phases)',
            'Statistic': friedman.get('statistic', np.nan),
            'p_value': friedman.get('p_value', np.nan),
            'Effect_Size': np.nan,
            'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': friedman.get('n_valid', np.nan),
            'Significance': interpret_p_value(friedman.get('p_value', 1))
        })

    # Friedman post-hoc pairwise
    for pw in friedman.get('pairwise', []):
        rows.append({
            'Test': f"Post-hoc Wilcoxon: {pw['comparison']}",
            'Statistic': pw.get('W', np.nan),
            'p_value': pw.get('p_bonferroni', np.nan),
            'Effect_Size': np.nan,
            'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': friedman.get('n_valid', np.nan),
            'Significance': interpret_p_value(pw.get('p_bonferroni', 1))
        })

    # Q2-Q5
    for qkey, qlabel in [('q2', 'Q2: Blind vs Icon'), ('q3', 'Q3: Icon vs T1'),
                          ('q4', 'Q4: T1 vs T2'), ('q5', 'Q5: Blind vs T2'),
                          ('Q_icon_t2', 'Q_icon_t2: Icon vs T2')]:
        q = results.get(qkey, {})
        pt = q.get('permutation_test', {})
        if pt:
            ci = q.get('improvement_ci', (np.nan, np.nan))
            rows.append({
                'Test': f'{qlabel} (permutation)',
                'Statistic': pt.get('observed_diff', np.nan),
                'p_value': pt.get('p_value', np.nan),
                'Effect_Size': q.get('cliffs_delta', np.nan),
                'CI_Lower': ci[0] if isinstance(ci, tuple) else np.nan,
                'CI_Upper': ci[1] if isinstance(ci, tuple) else np.nan,
                'N': q.get('n_valid', np.nan),
                'Significance': interpret_p_value(pt.get('p_value', 1))
            })

        wt = q.get('wilcoxon_test', {})
        if wt:
            rows.append({
                'Test': f'{qlabel} (Wilcoxon)',
                'Statistic': wt.get('statistic', np.nan),
                'p_value': wt.get('p_value', np.nan),
                'Effect_Size': np.nan,
                'CI_Lower': np.nan, 'CI_Upper': np.nan,
                'N': q.get('n_valid', np.nan),
                'Significance': interpret_p_value(wt.get('p_value', 1))
            })

    # Q6: Dom vs Rare
    dvr = results.get('q6', {}).get('dom_vs_rare', {})
    if dvr:
        rows.append({
            'Test': 'Q6: Dominant vs Rare (Mann-Whitney U)',
            'Statistic': dvr.get('statistic', np.nan),
            'p_value': dvr.get('p_value', np.nan),
            'Effect_Size': dvr.get('cliffs_delta', np.nan),
            'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': np.nan,
            'Significance': interpret_p_value(dvr.get('p_value', 1))
        })

    # Q7: Q3 understanding correlation
    q3c = results.get('q7', {}).get('q3_correlation', {})
    if q3c:
        rows.append({
            'Test': 'Q7: Understanding vs T2 SAD (Spearman)',
            'Statistic': q3c.get('rho', np.nan),
            'p_value': q3c.get('p_value', np.nan),
            'Effect_Size': np.nan,
            'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': np.nan,
            'Significance': interpret_p_value(q3c.get('p_value', 1))
        })

    # Timing vs Accuracy (T2)
    rt_res = results.get('rt', {})
    for measure, label in [('gen_rt_accuracy', 'RT vs SAD (T2)'),
                            ('gen_completion_time_accuracy', 'Completion vs SAD (T2)'),
                            ('deliberation_time_accuracy', 'Deliberation vs SAD (T2)')]:
        rta = rt_res.get(measure, {})
        if rta:
            rows.append({
                'Test': f'Timing: {label} (Spearman)',
                'Statistic': rta.get('rho', np.nan),
                'p_value': rta.get('p_value', np.nan),
                'Effect_Size': np.nan,
                'CI_Lower': np.nan, 'CI_Upper': np.nan,
                'N': np.nan,
                'Significance': interpret_p_value(rta.get('p_value', 1))
            })

    # Timing vs Accuracy (pooled)
    for measure, label in [('gen_rt_accuracy_pooled', 'RT vs SAD (pooled)'),
                            ('gen_completion_time_accuracy_pooled', 'Completion vs SAD (pooled)'),
                            ('deliberation_time_accuracy_pooled', 'Deliberation vs SAD (pooled)')]:
        rta = rt_res.get(measure, {})
        if rta:
            rows.append({
                'Test': f'Timing: {label} (Spearman)',
                'Statistic': rta.get('rho', np.nan),
                'p_value': rta.get('p_value', np.nan),
                'Effect_Size': np.nan,
                'CI_Lower': np.nan, 'CI_Upper': np.nan,
                'N': np.nan,
                'Significance': interpret_p_value(rta.get('p_value', 1))
            })

    # Deliberation Blind vs T2
    delib_comp = rt_res.get('delib_blind_vs_t2', {})
    if delib_comp:
        rows.append({
            'Test': 'Timing: Deliberation Blind vs T2 (permutation)',
            'Statistic': delib_comp.get('mean_diff', np.nan),
            'p_value': delib_comp.get('p_value', np.nan),
            'Effect_Size': delib_comp.get('cliffs_delta', np.nan),
            'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': np.nan,
            'Significance': interpret_p_value(delib_comp.get('p_value', 1))
        })

    # Prior-Test correlation
    ptc = results.get('prior_test_corr', {})
    if ptc:
        rows.append({
            'Test': 'Prior vs Test SAD (Spearman, combined phases)',
            'Statistic': ptc.get('rho', np.nan),
            'p_value': ptc.get('p_value', np.nan),
            'Effect_Size': np.nan,
            'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': ptc.get('n', np.nan),
            'Significance': interpret_p_value(ptc.get('p_value', 1))
        })

    # RT Friedman
    rt_fr = results.get('rt', {}).get('rt_friedman', {})
    if rt_fr:
        rows.append({
            'Test': 'RT Friedman (4-phase)',
            'Statistic': rt_fr.get('statistic', np.nan),
            'p_value': rt_fr.get('p_value', np.nan),
            'Effect_Size': np.nan, 'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': rt_fr.get('n', np.nan),
            'Significance': interpret_p_value(rt_fr.get('p_value', 1))
        })

    # RT pairwise
    for pw in results.get('rt', {}).get('rt_pairwise', []):
        rows.append({
            'Test': f"RT Wilcoxon {pw['comparison']} (Bonferroni)",
            'Statistic': pw.get('W', np.nan),
            'p_value': pw.get('p_bonf', np.nan),
            'Effect_Size': np.nan, 'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': np.nan,
            'Significance': interpret_p_value(pw.get('p_bonf', 1))
        })

    # Completion Friedman
    comp_fr = results.get('rt', {}).get('comp_friedman', {})
    if comp_fr:
        rows.append({
            'Test': 'Completion Time Friedman (4-phase)',
            'Statistic': comp_fr.get('statistic', np.nan),
            'p_value': comp_fr.get('p_value', np.nan),
            'Effect_Size': np.nan, 'CI_Lower': np.nan, 'CI_Upper': np.nan,
            'N': comp_fr.get('n', np.nan),
            'Significance': interpret_p_value(comp_fr.get('p_value', 1))
        })

    if rows:
        pd.DataFrame(rows).to_csv(output_path, index=False)
        report(f"Statistical results saved to: {output_path}")


# ============================================================================
# RESULTS SUMMARY TABLE - Executive summary for reports (v14)
# ============================================================================
# Auto-generates a single CSV with one row per key finding.
# Columns: Category, Question, Test, Statistic, p_value, Significance,
#   Effect_Size, Direction, Values, Comment

def _sig_stars(p):
    """Convert p-value to significance stars."""
    if p is None or np.isnan(p): return ''
    if p < 0.001: return '***'
    if p < 0.01: return '**'
    if p < 0.05: return '*'
    return 'n.s.'

def _fmt_p(p):
    if p is None or np.isnan(p): return ''
    return f'{p:.4f}'

def _fmt_d(d):
    if d is None or np.isnan(d): return ''
    mag = abs(d)
    label = 'negligible' if mag < 0.147 else 'small' if mag < 0.33 else 'medium' if mag < 0.474 else 'large'
    return f'{d:.3f} ({label})'


def generate_results_summary(results, n_subjects=0):
    """Generate a comprehensive results summary table as DataFrame."""
    rows = []

    def add(cat, question, test, stat_str, p, effect, direction, values, comment):
        rows.append({
            'Category': cat, 'Question': question, 'Test': test,
            'Statistic': stat_str, 'p_value': _fmt_p(p),
            'Significance': _sig_stars(p), 'Effect_Size': effect,
            'Direction': direction, 'Values': values, 'Comment': comment
        })

    # ---- Header row ----
    add('INFO', 'Sample size', '-', f'N = {n_subjects}', None, '', '', '', '')

    # ---- PRIOR (Q1) ----
    q1 = results.get('q1', {})
    ut = q1.get('uniform_test', {})
    observed_sad = ut.get('mean_diff')
    expected_null = ut.get('expected_null_sad')
    direction = ut.get('direction', '')
    stat_str = ''
    if observed_sad is not None:
        stat_str = f"observed mean SAD = {observed_sad:.2f}"
        if expected_null is not None:
            stat_str += f" (null expects {expected_null:.2f})"
    add('Prior', 'Is blind prior different from multinomial noise?',
        'Multinomial simulation (two-tailed, 10,000 draws)',
        stat_str,
        ut.get('p_value'), '', direction,
        f"p_greater={ut.get('p_greater','')}, p_less={ut.get('p_less','')}",
        'H0: responses drawn from uniform multinomial. Two-tailed: tests difference in either direction.')

    # Shape classification
    cc = q1.get('classification_counts', {})
    if cc:
        top = sorted(cc.items(), key=lambda x: -x[1])
        shape_str = ', '.join(f'{n}: {c} ({100*c/n_subjects:.0f}%)' for n, c in top) if n_subjects > 0 else str(cc)
        add('Prior', 'Prior shape distribution', 'Classification (SAD + chi-sq tiebreaker)',
            '', None, '', '', shape_str,
            f"Ties: {q1.get('n_ties', 0)} detected, {q1.get('n_ties_resolved', 0)} resolved by chi-sq")

    # Classification significance (v19)
    cb = q1.get('classification_binary', {})
    if cb.get('p_value') is not None:
        add('Prior', 'Is Uniform proportion significant?',
            'Simulation (two-tailed, 10,000 draws)',
            f"observed={cb['obs_pct']:.0f}% vs null={cb['null_mean_pct']:.1f}%",
            cb['p_value'], '', cb.get('direction', ''), '', '')

    ct2 = q1.get('classification_top2', {})
    if ct2.get('p_value') is not None:
        add('Prior', 'Is Uniform + Unimodal-mild proportion significant?',
            'Simulation (two-tailed, 10,000 draws)',
            f"observed={ct2['obs_pct']:.0f}% vs null={ct2['null_mean_pct']:.1f}%",
            ct2['p_value'], '', '', '', '')

    # ---- LEARNING (Q2-Q5) ----
    fr = results.get('friedman', {})
    fr_stat = fr.get('statistic')
    add('Learning', 'Does SAD decrease across phases?', 'Friedman omnibus',
        f"chi2(3) = {fr_stat:.3f}" if fr_stat is not None else '',
        fr.get('p_value'), '', f"N = {fr.get('n_valid', '')}",
        '',
        'H0: SAD distribution identical across 4 phases. Ranks within participant.')

    # Pairwise comparisons
    for q_label, key, cat_label in [
        ('Q2: Shape effect (Blind->Icon)', 'q2', 'Learning'),
        ('Q_blind_t1: Combined (Blind->T1)', 'q_blind_t1', 'Learning'),
        ('Q3: One-shot learning (Icon->T1)', 'q3', 'Learning'),
        ('Q4: Repetition (T1->T2)', 'q4', 'Learning'),
        ('Q5: Total learning (Blind->T2) [PRIMARY]', 'q5', 'Learning'),
        ('Q_icon_t2: Exposure learning (Icon->T2)', 'Q_icon_t2', 'Learning'),
    ]:
        qr = results.get(key, {})
        perm = qr.get('permutation_test', {})
        wilc = qr.get('wilcoxon_test', {})
        cd = qr.get('cliffs_delta', {})
        cd_val = cd.get('delta') if isinstance(cd, dict) else cd if isinstance(cd, (int, float)) else None
        diff = qr.get('mean_diff', np.nan)
        # Key is 'observed_diff' not 'observed_stat'
        obs_diff = perm.get('observed_diff', perm.get('observed_stat'))
        p_val = perm.get('p_value', wilc.get('p_value'))
        stat_str = ''
        if obs_diff is not None:
            stat_str = f"mean diff = {obs_diff:.2f}"
        elif diff is not None and not np.isnan(diff):
            stat_str = f"mean diff = {diff:.2f}"
        if wilc.get('statistic') is not None:
            stat_str += f", W = {wilc['statistic']:.1f}"

        add(cat_label, q_label, 'Paired permutation + Wilcoxon',
            stat_str, p_val,
            _fmt_d(cd_val) if cd_val is not None and not (isinstance(cd_val, float) and np.isnan(cd_val)) else '',
            f"{'decrease' if (diff or 0) > 0 else 'increase' if (diff or 0) < 0 else 'no change'}",
            f"n_improved={qr.get('n_improved', '')}, n_worsened={qr.get('n_worsened', '')}" if qr.get('n_improved') is not None else '',
            '')

    # Prior-test correlation (Q5b)
    q5b = results.get('q5b', {})
    if q5b.get('rho') is not None:
        add('Learning', 'Q5b: Prior predicts test?', 'Spearman rho',
            f"rho = {q5b['rho']:.3f}", q5b.get('p_value'),
            f"rho = {q5b['rho']:.3f}", '', '', 'Prior SAD (Blind+Icon) vs Test SAD (T1+T2)')

    # ---- ITEM ESTIMATION (Q6) ----
    q6 = results.get('q6', {})
    dvr = q6.get('dom_vs_rare', {})
    if dvr:
        dvr_cd = dvr.get('cliffs_delta')
        dvr_cd_val = dvr_cd if isinstance(dvr_cd, (int, float)) else dvr_cd.get('delta') if isinstance(dvr_cd, dict) else None
        add('Items', 'Q6: Dominant vs Rare error (T2)', 'Mann-Whitney U',
            f"U = {dvr.get('statistic', ''):.1f}" if dvr.get('statistic') is not None else '',
            dvr.get('p_value'),
            _fmt_d(dvr_cd_val) if dvr_cd_val is not None and not (isinstance(dvr_cd_val, float) and np.isnan(dvr_cd_val)) else '',
            f"Dom M={dvr.get('dom_mean', ''):.2f}, Rare M={dvr.get('rare_mean', ''):.2f}" if dvr.get('dom_mean') is not None else '',
            '', '')

    # Alternative errors
    alt = results.get('alt_errors', {}).get('friedman_tests', {})
    for exp, label in [(1.0, 'SAD p=1'), (1.72, 'CNS p=1.72'), (2.0, 'SSE p=2')]:
        ft = alt.get(exp, {})
        if ft.get('statistic') is not None:
            add('Items', f'Alt error ({label}): phase effect?', 'Friedman',
                f"chi2 = {ft['statistic']:.3f}", ft.get('p_value'), '', '', '', '')

    # Distribution fit
    df_res = results.get('dist_fit', {}).get('chi2_friedman', {})
    if df_res.get('statistic') is not None:
        add('Items', 'Chi-sq GoF improves across phases?', 'Friedman on chi-sq values',
            f"chi2 = {df_res['statistic']:.3f}", df_res.get('p_value'), '', '', '', '')

    # ---- ITEM-LEVEL PHASE TESTS ----
    ibi = results.get('q1', {}).get('item_blind_icon', {})
    for item_idx in range(1, 5):
        d = ibi.get(item_idx, {})
        if d.get('p_bonferroni') is not None:
            role = d.get('role', '')
            add('Items', f'Item {item_idx} ({role}): Blind vs Icon', 'Wilcoxon (Bonferroni)',
                f"W = {d['w_stat']:.1f}" if not np.isnan(d.get('w_stat', np.nan)) else '',
                d['p_bonferroni'],
                '', f"shift = {d['mean_shift']:+.2f}",
                f"Blind M={d['blind_mean']:.2f}, Icon M={d['icon_mean']:.2f}", '')

    # Interaction
    interaction = results.get('q1', {}).get('interaction_shift', {})
    if interaction.get('p_value') is not None:
        shifts_str = ', '.join(f"It{i+1}={interaction['mean_shifts'][i]:+.2f}" for i in range(4))
        add('Items', 'Interaction: shift differs by item?', 'Friedman on shifts',
            f"chi2 = {interaction['chi2']:.3f}", interaction['p_value'], '', '', shifts_str, '')

    # Per-item Friedman across 4 phases
    ipf = results.get('q1', {}).get('item_friedman_4phase', {})
    for item_idx in range(1, 5):
        d = ipf.get(item_idx, {})
        if d.get('p_bonferroni') is not None:
            means_str = ' -> '.join(f'{m:.2f}' for m in d.get('phase_means', []))
            add('Items', f'Item {item_idx} ({d.get("role","")}): changes across 4 phases?', 'Friedman (Bonferroni)',
                f"chi2 = {d['chi2']:.3f}", d['p_bonferroni'], '', '', means_str, '')

    # ---- EXACT MATCH (position-free) ----
    cm = results.get('exact_match', {}).get('count_match', {})
    if cm:
        for metric, label in [('has_6', 'Has count=6 (dominant)'), ('has_4', 'Has count=4 (medium)'),
                               ('has_1', 'Has count=1 (rare)'), ('full_sorted', 'Full sorted match [1,1,4,6]')]:
            vals = [cm.get(p, {}).get(metric, 0) for p in PHASE_ORDER]
            vals_str = f"Blind={vals[0]:.0f}%, Icon={vals[1]:.0f}%, T1={vals[2]:.0f}%, T2={vals[3]:.0f}%"
            cq = results.get('exact_match', {}).get('count_match_cochran', {}).get(label.split('(')[0].strip(), {})
            add('Exact Match', f'Position-free: {label}', 'Cochran Q' if cq else 'Descriptive',
                f"Q = {cq.get('Q', ''):.3f}" if cq.get('Q') is not None else '',
                cq.get('p_value'), '', '', vals_str, 'Position-free: value present anywhere in response')

    # ---- EXACT DISTRIBUTION BINOMIAL TESTS (v22) ----
    ds = results.get('dist_space', {})
    kdt = ds.get('key_dist_tests', {})
    for dist_key, label in [((3,3,3,3), 'Exact [3,3,3,3] (uniform)'), ((1,1,4,6), 'Exact [1,1,4,6] (true)')]:
        dt = kdt.get(dist_key, {})
        p_null = dt.get('p_null', 0)
        pc = dt.get('phase_counts', [0,0,0,0])
        # Report Blind for uniform, T2 for true
        if dist_key == (3,3,3,3):
            phase_test = dt.get('Blind', {})
            phase_label = 'Blind'
        else:
            phase_test = dt.get('T2', {})
            phase_label = 'T2'
        if phase_test.get('p_binom') is not None:
            add('Prior' if dist_key == (3,3,3,3) else 'Learning', f'{label} count ({phase_label})',
                f'Binomial (P_null={p_null:.4f})',
                f"count={phase_test['count']}/{n_subjects}",
                phase_test['p_binom'],
                '', '', f"Blind={pc[0]}, Icon={pc[1]}, T1={pc[2]}, T2={pc[3]}", '')

    # ---- MULTINOMIAL LOG-PROBABILITY (v19) ----
    mp = results.get('multinomial_prob', {})
    fr_lp = mp.get('friedman_log_true', {})
    if fr_lp.get('statistic') is not None:
        lr_means = mp.get('lr_phase_means', [])
        lr_str = f"LR: Blind={lr_means[0]:.2f}, Icon={lr_means[1]:.2f}, T1={lr_means[2]:.2f}, T2={lr_means[3]:.2f}" if len(lr_means) == 4 else ''
        add('Learning', 'Does log P(response|true) increase across phases?', 'Friedman on log-prob',
            f"chi2(3) = {fr_lp['statistic']:.3f}", fr_lp.get('p_value'), '', '', lr_str,
            'Sorted response, no position assignment. Positive LR = closer to true than uniform.')

    pw_lp = mp.get('pairwise_log_true', {})
    for pair_key, pair_label in [('Icon_vs_T1', 'Icon->T1'), ('Icon_vs_T2', 'Icon->T2'), ('Blind_vs_T2', 'Blind->T2')]:
        pw = pw_lp.get(pair_key, {})
        if pw.get('p_bonf') is not None:
            add('Learning', f'Log P(true) {pair_label}', 'Wilcoxon (Bonferroni)',
                f"diff = {pw['mean_diff']:+.3f}, W = {pw['w']:.1f}",
                pw['p_bonf'], '', '', '', '')

    # ---- TIMING ----
    rt_fr = results.get('rt', {}).get('rt_friedman', {})
    if rt_fr.get('statistic') is not None:
        add('Timing', 'RT changes across phases?', 'Friedman',
            f"chi2 = {rt_fr['statistic']:.3f}", rt_fr.get('p_value'), '', '', '', '')

    # ---- ESTIMATION TRENDS ----
    et = results.get('est_trends', {})
    for key, label in [('max_friedman', 'Max estimate trend'), ('dom_friedman', 'Dominant item trend')]:
        d = et.get(key, {})
        if d.get('statistic') is not None:
            add('Trends', label, 'Friedman',
                f"chi2 = {d['statistic']:.3f}", d.get('p_value'), '', '', '', '')

    for key, label in [('max_page', 'Max estimate monotonic trend'), ('dominant_page', 'Dominant item monotonic trend')]:
        d = et.get(key, {})
        if d.get('p_value') is not None:
            add('Trends', label, "Page's L",
                f"L = {d['L']:.1f}, Z = {d['Z']:.2f}", d['p_value'], '', '', '', 'One-tailed: Blind <= Icon <= T1 <= T2')

    # ---- FEEDBACK ----
    fb = results.get('feedback', {})
    ec = fb.get('error_correction', {})
    if ec.get('rho') is not None:
        add('Feedback', 'T1 error predicts improvement?', 'Spearman rho',
            f"rho = {ec['rho']:.3f}", ec.get('p_value'), f"rho = {ec['rho']:.3f}",
            '', '', 'Confounded by regression to mean')

    t1t2 = fb.get('t1_t2_correlation', {})
    if t1t2.get('rho') is not None:
        add('Feedback', 'T1 SAD stability (T1 vs T2)', 'Spearman rho',
            f"rho = {t1t2['rho']:.3f}", t1t2.get('p_value'), f"rho = {t1t2['rho']:.3f}",
            '', '', 'Positive = stable differences; negative = overcorrection')

    return pd.DataFrame(rows)


# ============================================================================
# EMAIL REPORT GENERATOR (v15)
# ============================================================================
# Auto-generates a formatted email report from analysis results.
# Pulls all numbers directly from the results dict.

def generate_email_report(results, n_subjects=0):
    """Generate formatted email report text from analysis results."""
    lines = []
    ln = lines.append

    # Helper to safely get nested values
    def g(d, *keys, default='___'):
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k, default)
            else:
                return default
        return default if d is None else d

    def fp(p):
        if p is None or (isinstance(p, float) and np.isnan(p)): return '___'
        if p < 0.001: return '< .001'
        return f'= {p:.3f}'

    def fd(d):
        if d is None or (isinstance(d, float) and np.isnan(d)): return '___'
        mag = abs(d)
        label = 'negligible' if mag < 0.147 else 'small' if mag < 0.33 else 'medium' if mag < 0.474 else 'large'
        return f'{d:.2f} ({label})'

    # Extract key results
    q1 = results.get('q1', {})
    fr = results.get('friedman', {})
    q2 = results.get('q2', {})
    q3 = results.get('q3', {})
    q4 = results.get('q4', {})
    q5 = results.get('q5', {})
    q6 = results.get('q6', {})
    et = results.get('est_trends', {})
    fb = results.get('feedback', {})
    em = results.get('exact_match', {})
    ut = q1.get('uniform_test', {})
    cc = q1.get('classification_counts', {})

    # Prior stats
    obs_sad = ut.get('mean_diff', np.nan)
    null_sad = ut.get('expected_null_sad', 4.65)
    p_prior = ut.get('p_value', np.nan)
    uniform_pct = 100 * cc.get('Uniform', 0) / max(n_subjects, 1) if cc else 0
    unimodal_pct = 100 * cc.get('Unimodal-mild', 0) / max(n_subjects, 1) if cc else 0

    # Learning stats
    fr_chi2 = fr.get('statistic', np.nan)
    fr_p = fr.get('p_value', np.nan)
    q5_diff = q5.get('mean_improvement', q5.get('mean_diff', q5.get('permutation_test', {}).get('observed_diff', np.nan)))
    q5_p = q5.get('permutation_test', {}).get('p_value', np.nan)
    q5_cd = q5.get('cliffs_delta', np.nan)
    q5_cd_val = q5_cd.get('delta') if isinstance(q5_cd, dict) else q5_cd if isinstance(q5_cd, (int, float)) else np.nan
    q5_pct_imp = q5.get('pct_improvement', np.nan)
    q4_diff = q4.get('mean_improvement', q4.get('mean_diff', q4.get('permutation_test', {}).get('observed_diff', np.nan)))
    q4_p = q4.get('permutation_test', {}).get('p_value', np.nan)
    q3_diff = q3.get('mean_improvement', q3.get('mean_diff', q3.get('permutation_test', {}).get('observed_diff', np.nan)))
    qbt = results.get('q_blind_t1', {})
    qbt_diff = qbt.get('mean_diff', np.nan)
    qbt_p = qbt.get('permutation_test', {}).get('p_value', np.nan)
    qit = results.get('Q_icon_t2', {})
    qit_diff = qit.get('mean_improvement', qit.get('permutation_test', {}).get('observed_diff', np.nan))
    qit_p = qit.get('permutation_test', {}).get('p_value', np.nan)

    # Item stats
    dvr = q6.get('dom_vs_rare', {})
    dvr_cd = dvr.get('cliffs_delta', np.nan)
    dvr_cd_val = dvr_cd if isinstance(dvr_cd, (int, float)) else dvr_cd.get('delta', np.nan) if isinstance(dvr_cd, dict) else np.nan

    # Count match
    cm = em.get('count_match', {})
    has6_blind = cm.get('blind_prior', {}).get('has_6', 0)
    has6_t2 = cm.get('exposure_gen_2', {}).get('has_6', 0)

    # Feedback
    ec = fb.get('error_correction', {})
    t1t2 = fb.get('t1_t2_correlation', {})

    # Page trend
    page_dom = et.get('dominant_page', {})

    # ================================================================
    # BUILD REPORT
    # ================================================================

    ln("=" * 70)
    ln("EXECUTIVE SUMMARY")
    ln("=" * 70)
    ln("")
    ln(f"We tested whether participants (N={n_subjects}) can extract a frequency")
    ln(f"distribution [1,1,4,6] from 1-2 brief visual exposures in a generation")
    ln(f"task. ", )
    if not np.isnan(q5_p):
        if q5_p < 0.05:
            ln(f"SAD decreased significantly from Blind to T2 (p {fp(q5_p)},")
            ln(f"Cliff's d = {fd(q5_cd_val)}).")
        else:
            ln(f"SAD did not decrease significantly from Blind to T2 (p {fp(q5_p)},")
            ln(f"Cliff's d = {fd(q5_cd_val)}).")
    if obs_sad < null_sad and not np.isnan(obs_sad):
        ln(f"The blind prior mean SAD ({obs_sad:.2f}) was lower than the")
        ln(f"multinomial null expectation ({null_sad:.2f}).")
    ln("")

    ln("")
    ln("=" * 70)
    ln("1. POPULATION PRIOR")
    ln("=" * 70)
    ln("")
    if cc:
        top_shapes = sorted(cc.items(), key=lambda x: -x[1])
        shape_desc = ', '.join(f'{n} ({100*c/max(n_subjects,1):.0f}%, n={c})' for n, c in top_shapes)
        ln(f"The blind prior was classified as: {shape_desc}.")
    ln(f"A multinomial simulation test (simulation draws from Multinomial(12,")
    ln(f"[.25,.25,.25,.25])) compared the observed mean SAD from uniform")
    ln(f"({obs_sad:.2f}) to the null expectation ({null_sad:.2f}).")
    if not np.isnan(p_prior):
        if p_prior < 0.05:
            if obs_sad > null_sad:
                ln(f"Two-tailed test: p {fp(p_prior)}. Reject H0.")
                ln(f"Observed mean SAD was higher than null expectation.")
            else:
                ln(f"Two-tailed test: p {fp(p_prior)}. Reject H0.")
                ln(f"Observed mean SAD was lower than null expectation.")
        else:
            ln(f"Two-tailed test: p {fp(p_prior)}. Fail to reject H0.")
            ln(f"Data consistent with multinomial sampling noise.")

    # Ties
    n_ties = q1.get('n_ties', 0)
    n_resolved = q1.get('n_ties_resolved', 0)
    if n_ties > 0:
        ln(f"Shape classification: {n_ties} tie(s) detected, {n_resolved} resolved by chi-square tiebreaker.")

    # Classification significance
    cb = q1.get('classification_binary', {})
    ct2 = q1.get('classification_top2', {})
    if cb.get('p_value') is not None:
        ln(f"")
        ln(f"Classification proportion significance (simulation, two-tailed):")
        ln(f"  Uniform: {cb['obs_pct']:.0f}% observed vs {cb['null_mean_pct']:.1f}% null, p {fp(cb['p_value'])}")
    if ct2.get('p_value') is not None:
        ln(f"  Uniform + Unimodal-mild: {ct2['obs_pct']:.0f}% observed vs {ct2['null_mean_pct']:.1f}% null, p {fp(ct2['p_value'])}")

    ln("")
    ln("")
    ln("=" * 70)
    ln("2. LEARNING ACROSS THE EXPERIMENT")
    ln("=" * 70)
    ln("")
    if not np.isnan(fr_chi2):
        ln(f"Friedman omnibus: chi2(3) = {fr_chi2:.3f}, p {fp(fr_p)}.")
        if fr_p < 0.05:
            ln(f"SAD differed significantly across the four phases.")
        else:
            ln(f"No significant omnibus phase effect.")
    ln("")
    ln(f"PRIMARY (Q5, Blind -> T2):")
    ln(f"  Mean SAD difference = {q5_diff:.2f}" if not np.isnan(q5_diff) else "  Mean SAD difference = ___")
    ln(f"  Permutation test: p {fp(q5_p)}")
    ln(f"  Cliff's delta = {fd(q5_cd_val)}")
    if not np.isnan(q5_pct_imp):
        ln(f"  Mean % change: {q5_pct_imp:.0f}%")
        ln(f"  Direction: {q5.get('n_improved', '?')} improved, {q5.get('n_worsened', '?')} worsened, {q5.get('n_no_change', '?')} no change")
    ln("")
    ln(f"Q3 (Icon -> T1): mean diff = {q3_diff:.2f}, p {fp(q3.get('permutation_test', {}).get('p_value'))}" if not np.isnan(q3_diff) else "")
    ln(f"Q4 (T1 -> T2):   mean diff = {q4_diff:.2f}, p {fp(q4_p)}" if not np.isnan(q4_diff) else "")
    ln(f"Blind -> T1 (combined icon+exposure): mean diff = {qbt_diff:.2f}, p {fp(qbt_p)}" if not np.isnan(qbt_diff) else "")
    ln(f"Icon -> T2 (exposure learning): mean diff = {qit_diff:.2f}, p {fp(qit_p)}" if not np.isnan(qit_diff) else "")

    # Page trend
    if page_dom.get('p_value') is not None:
        ln(f"")
        ln(f"Page's monotonic trend (dominant item): Z = {page_dom['Z']:.2f}, p {fp(page_dom['p_value'])}")

    ln("")
    ln("")
    ln("=" * 70)
    ln("3. ITEM ESTIMATION & EXACT MATCH")
    ln("=" * 70)
    ln("")
    if dvr:
        ln(f"Q6 (Dominant vs Rare error, T2):")
        ln(f"  Dom mean error = {dvr.get('dom_mean', np.nan):.2f}, Rare mean error = {dvr.get('rare_mean', np.nan):.2f}" if dvr.get('dom_mean') is not None else "")
        ln(f"  Mann-Whitney U = {dvr.get('statistic', np.nan):.1f}, p {fp(dvr.get('p_value'))}" if dvr.get('statistic') is not None else "")
        ln(f"  Cliff's delta = {fd(dvr_cd_val)}")

    ln("")
    ln(f"Position-free count match (% with value present in response):")
    for metric, label in [('has_6', 'Has 6 (dominant)'), ('has_4', 'Has 4 (medium)'),
                           ('has_1', 'Has 1 (rare)'), ('full_sorted', 'Full [1,1,4,6]')]:
        vals = [cm.get(p, {}).get(metric, 0) for p in ['blind_prior', 'prior_icon', 'exposure_gen_1', 'exposure_gen_2']]
        ln(f"  {label}: Blind={vals[0]:.0f}%, Icon={vals[1]:.0f}%, T1={vals[2]:.0f}%, T2={vals[3]:.0f}%")

    ln("")
    ln("")
    ln("=" * 70)
    ln("4. T1 TO T2 TRANSITION & FEEDBACK UTILIZATION")
    ln("=" * 70)
    ln("")
    ln(f"Q4 (T1 -> T2): mean diff = {q4_diff:.2f}, p {fp(q4_p)}" if not np.isnan(q4_diff) else "Q4: insufficient data")
    ln("")
    ln(f"Feedback utilization:")
    if ec.get('rho') is not None:
        ln(f"  T1 error -> improvement: rho = {ec['rho']:.3f}, p {fp(ec.get('p_value'))}")
        ln(f"  (Caveat: partially confounded by regression to the mean)")
    if t1t2.get('rho') is not None:
        ln(f"  T1 SAD vs T2 SAD stability: rho = {t1t2['rho']:.3f}, p {fp(t1t2.get('p_value'))}")

    # Item-level correction
    ic = fb.get('item_correction', {})
    if ic:
        ln(f"")
        ln(f"  Item-level correction direction (T1 -> T2):")
        for item_idx in range(1, 5):
            d = ic.get(item_idx, {})
            if d:
                role = ['rare', 'rare', 'medium', 'dominant'][item_idx - 1]
                ln(f"    Item {item_idx} ({role}): {d.get('pct_correct_direction', 0):.0f}% correct direction")

    ln("")
    ln("")
    ln("=" * 70)
    ln("KEY NUMBERS FOR SLIDES")
    ln("=" * 70)
    ln(f"  N = {n_subjects}")
    ln(f"  Prior: {uniform_pct:.0f}% Uniform, {unimodal_pct:.0f}% Unimodal-mild")
    ln(f"  Prior test (multinomial simulation): p {fp(p_prior)}")
    ln(f"  Friedman omnibus: p {fp(fr_p)}")
    ln(f"  Q5 (Blind->T2): p {fp(q5_p)}, d = {fd(q5_cd_val)}")
    ln(f"  Q4 (T1->T2): p {fp(q4_p)}")
    ln(f"  Has count=6: Blind={has6_blind:.0f}% -> T2={has6_t2:.0f}%")
    if ec.get('rho') is not None:
        ln(f"  Feedback rho = {ec['rho']:.3f}")
    ln("")

    return '\n'.join(lines)


# ============================================================================
# MARKDOWN + PDF REPORT GENERATOR (v15)
# ============================================================================
# 1. Generates a markdown report with figure references
# 2. Converts to PDF using only matplotlib (no external deps)

def generate_markdown_report(results, figure_paths, output_md_path, n_subjects=0):
    """Generate a markdown report referencing figures."""
    lines = []
    ln = lines.append

    def fp(p):
        if p is None or (isinstance(p, float) and np.isnan(p)): return '___'
        if p < 0.001: return '< .001'
        return f'= {p:.3f}'

    def fd(d):
        if d is None or (isinstance(d, float) and np.isnan(d)): return '___'
        mag = abs(d)
        label = 'negligible' if mag < 0.147 else 'small' if mag < 0.33 else 'medium' if mag < 0.474 else 'large'
        return f'{d:.2f} ({label})'

    # Extract results
    q1 = results.get('q1', {})
    fr = results.get('friedman', {})
    q3, q4, q5 = results.get('q3', {}), results.get('q4', {}), results.get('q5', {})
    q6 = results.get('q6', {})
    et = results.get('est_trends', {})
    fb = results.get('feedback', {})
    em = results.get('exact_match', {})
    ut = q1.get('uniform_test', {})
    cc = q1.get('classification_counts', {})

    obs_sad = ut.get('mean_diff', np.nan)
    null_sad = ut.get('expected_null_sad', 4.65)
    p_prior = ut.get('p_value', np.nan)
    q5_diff = q5.get('mean_improvement', q5.get('permutation_test', {}).get('observed_diff', np.nan))
    q5_p = q5.get('permutation_test', {}).get('p_value', np.nan)
    q5_cd = q5.get('cliffs_delta', np.nan)
    q5_cd_val = q5_cd.get('delta') if isinstance(q5_cd, dict) else q5_cd if isinstance(q5_cd, (int, float)) else np.nan
    q5_pct = q5.get('pct_improvement', np.nan)
    q4_diff = q4.get('mean_improvement', q4.get('permutation_test', {}).get('observed_diff', np.nan))
    q4_p = q4.get('permutation_test', {}).get('p_value', np.nan)
    q3_diff = q3.get('mean_improvement', q3.get('permutation_test', {}).get('observed_diff', np.nan))
    qbt = results.get('q_blind_t1', {})
    qbt_diff = qbt.get('mean_diff', np.nan)
    qbt_p = qbt.get('permutation_test', {}).get('p_value', np.nan)
    qit = results.get('Q_icon_t2', {})
    qit_diff = qit.get('mean_improvement', qit.get('permutation_test', {}).get('observed_diff', np.nan))
    qit_p = qit.get('permutation_test', {}).get('p_value', np.nan)
    dvr = q6.get('dom_vs_rare', {})
    dvr_cd = dvr.get('cliffs_delta', np.nan)
    dvr_cd_val = dvr_cd if isinstance(dvr_cd, (int, float)) else dvr_cd.get('delta', np.nan) if isinstance(dvr_cd, dict) else np.nan
    cm = em.get('count_match', {})
    ec = fb.get('error_correction', {})
    t1t2 = fb.get('t1_t2_correlation', {})
    page_dom = et.get('dominant_page', {})
    fr_chi2 = fr.get('statistic', np.nan)

    # ---- Build markdown ----
    ln(f'# OneShot Distributional Learning Report')
    ln(f'**N = {n_subjects} participants** | Paz Lab, Weizmann Institute')
    ln('')

    # Executive Summary
    ln(f'## Executive Summary')
    ln('')
    summary = f'We tested whether participants (N={n_subjects}) can extract a frequency distribution [1,1,4,6] from 1-2 brief visual exposures in a generation task. '
    if not np.isnan(q5_p):
        if q5_p < 0.05:
            summary += f"SAD decreased significantly from Blind to T2 (p {fp(q5_p)}, Cliff's d = {fd(q5_cd_val)}). "
        else:
            summary += f"SAD did not decrease significantly from Blind to T2 (p {fp(q5_p)}, Cliff's d = {fd(q5_cd_val)}). "
    if not np.isnan(obs_sad) and obs_sad < null_sad:
        summary += 'The blind prior mean SAD was lower than the multinomial null expectation.'
    ln(summary)
    ln('')
    ln(f'![Figure 1: Descriptive Overview]({figure_paths.get("fig1", "")})')
    ln('')

    # Section 1: Prior
    ln(f'## 1. Population Prior')
    ln('')
    if cc:
        top = sorted(cc.items(), key=lambda x: -x[1])
        shape_str = ', '.join(f'{n} ({100*c/max(n_subjects,1):.0f}%, n={c})' for n, c in top)
        ln(f'**Shape classification:** {shape_str}')
        ln('')
    ln(f'**Multinomial simulation test** (simulation draws from Multinomial(12, [.25,.25,.25,.25])):')
    ln(f'observed mean SAD = {obs_sad:.2f}, null expectation = {null_sad:.2f}, p {fp(p_prior)}')
    ln('')
    if not np.isnan(p_prior) and p_prior < 0.05:
        if not np.isnan(obs_sad) and obs_sad < null_sad:
            ln(f'Two-tailed test: reject H0 (p {fp(p_prior)}). Observed SAD ({obs_sad:.2f}) was lower than null ({null_sad:.2f}).')
        else:
            ln(f'Two-tailed test: reject H0 (p {fp(p_prior)}). Observed SAD ({obs_sad:.2f}) was higher than null ({null_sad:.2f}).')
    elif not np.isnan(p_prior):
        ln(f'Two-tailed test: fail to reject H0 (p {fp(p_prior)}). Data consistent with multinomial noise.')
    n_ties = q1.get('n_ties', 0)
    if n_ties > 0:
        ln(f'Shape classification: {n_ties} tie(s), {q1.get("n_ties_resolved", 0)} resolved by chi-sq.')
    ln('')
    ln(f'![Figure 2: Prior Analysis]({figure_paths.get("fig2", "")})')
    ln('')

    # Section 2: Learning
    ln(f'## 2. Learning Across the Experiment')
    ln('')
    if not np.isnan(fr_chi2):
        ln(f'**Friedman omnibus:** chi2(3) = {fr_chi2:.3f}, p {fp(fr.get("p_value"))}')
        ln('')
    ln(f'**PRIMARY (Q5, Blind -> T2):**')
    ln(f'- Mean SAD difference: {q5_diff:.2f}' if not np.isnan(q5_diff) else '- Mean SAD difference: ___')
    ln(f'- Permutation test: p {fp(q5_p)}')
    ln(f"- Cliff's delta: {fd(q5_cd_val)}")
    if not np.isnan(q5_pct):
        ln(f'- Mean % change: {q5_pct:.0f}%')
        ln(f'- Direction: {q5.get("n_improved", "?")} improved, {q5.get("n_worsened", "?")} worsened, {q5.get("n_no_change", "?")} no change')
    ln('')
    if not np.isnan(q3_diff):
        ln(f'**Q3 (Icon -> T1):** diff = {q3_diff:.2f}, p {fp(q3.get("permutation_test", {}).get("p_value"))}')
    if not np.isnan(q4_diff):
        ln(f'**Q4 (T1 -> T2):** diff = {q4_diff:.2f}, p {fp(q4_p)}')
    if not np.isnan(qbt_diff):
        ln(f'**Blind -> T1 (combined):** diff = {qbt_diff:.2f}, p {fp(qbt_p)}')
    if not np.isnan(qit_diff):
        ln(f'**Icon -> T2 (exposure):** diff = {qit_diff:.2f}, p {fp(qit_p)}')
    if page_dom.get('p_value') is not None:
        ln(f"**Page's trend (dominant):** Z = {page_dom['Z']:.2f}, p {fp(page_dom['p_value'])}")
    ln('')
    ln(f'![Figure 3: Learning Trajectory]({figure_paths.get("fig3", "")})')
    ln('')

    # Section 3: Items
    ln(f'## 3. Item Estimation & Exact Match')
    ln('')
    if dvr.get('p_value') is not None:
        ln(f'**Q6 (Dominant vs Rare error, T2):** U = {dvr.get("statistic", np.nan):.1f}, p {fp(dvr.get("p_value"))}, d = {fd(dvr_cd_val)}')
        ln('')
    ln(f'**Position-free count match:**')
    ln('')
    ln(f'| Metric | Blind | Icon | T1 | T2 |')
    ln(f'|--------|-------|------|----|----|')
    for metric, label in [('has_6', 'Has 6 (dom)'), ('has_4', 'Has 4 (med)'), ('has_1', 'Has 1 (rare)'), ('full_sorted', 'Full [1,1,4,6]')]:
        vals = [cm.get(p, {}).get(metric, 0) for p in ['blind_prior', 'prior_icon', 'exposure_gen_1', 'exposure_gen_2']]
        ln(f'| {label} | {vals[0]:.0f}% | {vals[1]:.0f}% | {vals[2]:.0f}% | {vals[3]:.0f}% |')
    ln('')
    ln(f'![Figure 4: Item Analysis]({figure_paths.get("fig4", "")})')
    ln('')

    # Section 4: T1-T2
    ln(f'## 4. T1 to T2 & Feedback Utilization')
    ln('')
    if not np.isnan(q4_diff):
        ln(f'**Q4 (T1 -> T2):** diff = {q4_diff:.2f}, p {fp(q4_p)}')
    if ec.get('rho') is not None:
        ln(f'**Error-correction:** rho = {ec["rho"]:.3f}, p {fp(ec.get("p_value"))} (caveat: regression to mean)')
    if t1t2.get('rho') is not None:
        ln(f'**T1-T2 stability:** rho = {t1t2["rho"]:.3f}, p {fp(t1t2.get("p_value"))}')
    ln('')
    ln(f'![Figure 7: Trends & Feedback]({figure_paths.get("fig7", "")})')
    ln('')

    # Key Numbers
    ln(f'## Key Numbers')
    ln('')
    uniform_pct = 100 * cc.get('Uniform', 0) / max(n_subjects, 1) if cc else 0
    has6_blind = cm.get('blind_prior', {}).get('has_6', 0)
    has6_t2 = cm.get('exposure_gen_2', {}).get('has_6', 0)
    ln(f'| Measure | Value |')
    ln(f'|---------|-------|')
    ln(f'| N | {n_subjects} |')
    ln(f'| Prior | {uniform_pct:.0f}% Uniform |')
    ln(f'| Prior test | p {fp(p_prior)} |')
    ln(f'| Friedman | p {fp(fr.get("p_value"))} |')
    ln(f'| Q5 (Blind->T2) | p {fp(q5_p)}, d = {fd(q5_cd_val)} |')
    ln(f'| Q4 (T1->T2) | p {fp(q4_p)} |')
    ln(f'| Has 6 | Blind={has6_blind:.0f}% -> T2={has6_t2:.0f}% |')

    md_text = '\n'.join(lines)
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write(md_text)
    report(f"Markdown report saved to: {output_md_path}")
    return md_text


def convert_md_report_to_pdf(md_path, figure_paths, output_pdf_path):
    """Convert markdown report to PDF using only matplotlib.
    Each section becomes a page with text rendered via fig.text() and figures embedded."""
    from matplotlib.backends.backend_pdf import PdfPages
    import textwrap

    # Read markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Split into sections by ## headers
    sections = []
    current_title = 'Cover'
    current_lines = []
    current_fig = None

    for line in md_text.split('\n'):
        if line.startswith('## '):
            if current_lines or current_title:
                sections.append({'title': current_title, 'text': '\n'.join(current_lines), 'figure': current_fig})
            current_title = line.replace('## ', '').strip()
            current_lines = []
            current_fig = None
        elif line.startswith('!['):
            # Extract figure path
            start = line.find('(') + 1
            end = line.find(')')
            if start > 0 and end > start:
                fig_path = line[start:end]
                if fig_path and Path(fig_path).exists():
                    current_fig = fig_path
        elif line.startswith('# '):
            current_lines.append(line.replace('# ', '').strip())
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({'title': current_title, 'text': '\n'.join(current_lines), 'figure': current_fig})

    with PdfPages(str(output_pdf_path)) as pdf:
        for sec in sections:
            title = sec['title']
            text = sec['text'].strip()
            fig_path = sec.get('figure')

            if fig_path and Path(fig_path).exists():
                # Page with figure + text above
                fig = plt.figure(figsize=(11, 16))

                # Title
                fig.text(0.05, 0.97, title, fontsize=14, fontweight='bold',
                         color='#16213e', va='top', fontfamily='sans-serif')

                # Clean text (remove markdown formatting)
                clean = text.replace('**', '').replace('*', '')
                clean = '\n'.join(l for l in clean.split('\n') if not l.startswith('|') or 'Metric' in l or 'Measure' in l or '---' not in l)
                # Keep only non-table, non-empty lines
                text_lines = [l for l in clean.split('\n') if l.strip() and not l.startswith('|') and '---' not in l]
                body = '\n'.join(text_lines[:15])  # Limit text above figure
                wrapped = textwrap.fill(body, width=100)

                fig.text(0.05, 0.94, wrapped, fontsize=8, va='top',
                         fontfamily='serif', linespacing=1.5,
                         transform=fig.transFigure)

                # Calculate text height (approximate)
                n_text_lines = wrapped.count('\n') + 1
                text_bottom = 0.94 - (n_text_lines * 0.015)
                fig_top = min(text_bottom - 0.02, 0.82)

                # Embed figure image
                try:
                    img = plt.imread(fig_path)
                    ax = fig.add_axes([0.02, 0.03, 0.96, fig_top])
                    ax.imshow(img)
                    ax.axis('off')
                except Exception:
                    pass

                pdf.savefig(fig, dpi=150)
                plt.close(fig)
            else:
                # Text-only page
                fig = plt.figure(figsize=(11, 8.5))
                fig.text(0.05, 0.95, title, fontsize=16, fontweight='bold',
                         color='#16213e', va='top', fontfamily='sans-serif')

                clean = text.replace('**', '').replace('*', '')
                text_lines = [l for l in clean.split('\n') if l.strip()]
                body = '\n'.join(text_lines)
                wrapped = textwrap.fill(body, width=90)

                fig.text(0.05, 0.88, wrapped, fontsize=10, va='top',
                         fontfamily='serif', linespacing=1.6)

                pdf.savefig(fig, dpi=150)
                plt.close(fig)

    report(f"PDF report saved to: {output_pdf_path}")


# ============================================================================
# FIGURE 7: ESTIMATION TRENDS + FEEDBACK UTILIZATION (3x3)
# ============================================================================
# Row 1: 7.1 Slope: Max  7.2 Slope: Dominant  7.3 Stacked bar: dom bins
# Row 2: 7.4 CDF        7.5 Near-miss         7.6 Conditional probability
# Row 3: 7.7 T1 vs T2   7.8 Error-correction   7.9 Band improvement

def create_figure7(df, summary_df, results, save_path=None):
    """Figure 7: Estimation trends + feedback utilization (3x3)."""
    fig, axes = plt.subplots(3, 3, figsize=(18, 16))
    fig.suptitle('Figure 7: Estimation Trends & Feedback Utilization', fontsize=14, fontweight='bold')
    from matplotlib.lines import Line2D
    et = results.get('est_trends', {})
    fb = results.get('feedback', {})
    x_phases = np.arange(4)
    phase_labels = [PHASE_SHORT[p] for p in PHASE_ORDER]

    # ---- 7.1: Slope chart - Max estimate ----
    ax = axes[0, 0]
    max_m = et.get('max_matrix', np.array([]))
    if max_m.size > 0:
        for i in range(max_m.shape[0]):
            row = max_m[i]
            if not np.any(np.isnan(row)):
                ax.plot(x_phases, row, 'o-', color='gray', alpha=0.3, markersize=4, lw=0.8)
        means = np.nanmean(max_m, axis=0)
        ax.plot(x_phases, means, 'D-', color='black', markersize=8, lw=2.5, zorder=10, label='Mean')
        ax.axhline(y=6, color='red', ls=':', lw=1, label='True max (6)')
    ax.set_xticks(x_phases); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('Max Estimate (of 4 items)'); ax.set_title('7.1 Max Estimate Trend')
    ax.legend(fontsize=7)
    mf = et.get('max_friedman', {}); mp = et.get('max_page', {})
    stats_t = ''
    if mf.get('p_value') is not None:
        stats_t += f"Friedman: p={mf['p_value']:.3f} {interpret_p_value(mf['p_value'])}"
    if mp.get('p_value') is not None:
        stats_t += f"\nPage trend: Z={mp['Z']:.2f}, p={mp['p_value']:.3f} {interpret_p_value(mp['p_value'])}"
    if stats_t:
        add_stats_text(ax, stats_t, loc='lower right', fontsize=7)

    # ---- 7.2: Slope chart - Dominant item ----
    ax = axes[0, 1]
    dom_m = et.get('dom_matrix', np.array([]))
    if dom_m.size > 0:
        for i in range(dom_m.shape[0]):
            row = dom_m[i]
            if not np.any(np.isnan(row)):
                ax.plot(x_phases, row, 'o-', color='gray', alpha=0.3, markersize=4, lw=0.8)
        means = np.nanmean(dom_m, axis=0)
        ax.plot(x_phases, means, 'D-', color=COLORS['exposure_gen_2'], markersize=8, lw=2.5, zorder=10, label='Mean')
        ax.axhline(y=6, color='red', ls=':', lw=1, label='True (6)')
    ax.set_xticks(x_phases); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('Dominant Item Estimate'); ax.set_title('7.2 Dominant Item (true=6) Trend')
    ax.legend(fontsize=7)
    df2 = et.get('dom_friedman', {}); dp = et.get('dominant_page', {})
    stats_t = ''
    if df2.get('p_value') is not None:
        stats_t += f"Friedman: p={df2['p_value']:.3f} {interpret_p_value(df2['p_value'])}"
    if dp.get('p_value') is not None:
        stats_t += f"\nPage trend: Z={dp['Z']:.2f}, p={dp['p_value']:.3f} {interpret_p_value(dp['p_value'])}"
    if stats_t:
        add_stats_text(ax, stats_t, loc='lower right', fontsize=7)

    # ---- 7.3: Stacked bar - Dominant item bins ----
    ax = axes[0, 2]
    dom_bins = et.get('dom_bins', {})
    bin_labels = et.get('bin_labels', ['0-1','2-3','4-5','6','7+'])
    bin_colors = ['#d32f2f', '#ff9800', '#ffeb3b', '#4caf50', '#9c27b0']
    if dom_bins:
        bottom = np.zeros(4)
        for b_idx, b_label in enumerate(bin_labels):
            pcts = [dom_bins.get(p, {}).get('pcts', [0]*5)[b_idx] for p in PHASE_ORDER]
            ax.bar(x_phases, pcts, bottom=bottom, label=b_label,
                   color=bin_colors[b_idx], edgecolor='white', linewidth=0.5, width=0.7)
            bottom += pcts
    ax.set_xticks(x_phases); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('% of Participants'); ax.set_title('7.3 Dominant Item Distribution')
    ax.legend(title='Estimate', fontsize=6, title_fontsize=7, loc='upper right'); ax.set_ylim(0, 105)

    # ---- 7.4: CDF - Dominant item ----
    ax = axes[1, 0]
    for phase in PHASE_ORDER:
        pdf = df[df['trial_type'] == phase]
        vals = np.sort(pdf['gen_est_item4'].dropna().values)
        if len(vals) > 0:
            cdf = np.arange(1, len(vals) + 1) / len(vals)
            ax.step(vals, cdf, where='post', color=COLORS[phase], lw=2, label=PHASE_SHORT[phase])
    ax.axvline(x=6, color='red', ls=':', lw=1, alpha=0.7)
    ax.set_xlabel('Dominant Item Estimate'); ax.set_ylabel('Cumulative Proportion')
    ax.set_title('7.4 CDF of Dominant Item Estimates'); ax.legend(fontsize=7)
    ax.text(6.2, 0.1, 'True=6', fontsize=7, color='red')

    # ---- 7.5: Near-miss stacked bar ----
    ax = axes[1, 1]
    precision = et.get('precision', {})
    bar_w = 0.35
    for r_idx, (role, offset) in enumerate([('dominant', -bar_w/2), ('medium', bar_w/2)]):
        role_data = precision.get(role, {})
        if role_data:
            exact_pcts = [role_data.get(p, {}).get('exact_pct', 0) for p in PHASE_ORDER]
            near_pcts = [role_data.get(p, {}).get('near_pct', 0) for p in PHASE_ORDER]
            far_pcts = [role_data.get(p, {}).get('far_pct', 0) for p in PHASE_ORDER]
            ax.bar(x_phases + offset, exact_pcts, bar_w, label=f'{role.title()} exact', color='#4caf50' if r_idx==0 else '#2196f3', alpha=0.9, edgecolor='white')
            ax.bar(x_phases + offset, near_pcts, bar_w, bottom=exact_pcts, label=f'{role.title()} near', color='#4caf50' if r_idx==0 else '#2196f3', alpha=0.4, edgecolor='white')
            ax.bar(x_phases + offset, far_pcts, bar_w, bottom=[e+n for e,n in zip(exact_pcts, near_pcts)], label=f'{role.title()} far', color='gray', alpha=0.2, edgecolor='white')
    ax.set_xticks(x_phases); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('% of Participants'); ax.set_title('7.5 Precision: Exact / Near-Miss / Far')
    ax.legend(fontsize=5.5, ncol=2); ax.set_ylim(0, 105)
    nc_d = et.get('near_cochran_dominant', {}); nc_m = et.get('near_cochran_medium', {})
    ann = []
    if nc_d.get('p_value') is not None: ann.append(f"Dom Q: p={nc_d['p_value']:.3f}")
    if nc_m.get('p_value') is not None: ann.append(f"Med Q: p={nc_m['p_value']:.3f}")
    if ann: add_stats_text(ax, '\n'.join(ann), loc='upper left', fontsize=6)

    # ---- 7.6: Conditional probability ----
    ax = axes[1, 2]
    jh = et.get('joint_hits', {})
    if jh:
        p6 = [jh.get(p, {}).get('p_hit6', 0) for p in PHASE_ORDER]
        p4 = [jh.get(p, {}).get('p_hit4', 0) for p in PHASE_ORDER]
        pb = [jh.get(p, {}).get('p_both', 0) for p in PHASE_ORDER]
        ax.plot(x_phases, p6, 'D-', color=COLORS['dominant'], lw=2, markersize=7, label='P(hit 6)')
        ax.plot(x_phases, p4, 's-', color=COLORS['medium'], lw=2, markersize=7, label='P(hit 4)')
        ax.plot(x_phases, pb, '^-', color='black', lw=2, markersize=7, label='P(both)')
    ax.set_xticks(x_phases); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('Probability'); ax.set_title('7.6 Joint & Marginal Hit Rates')
    ax.legend(fontsize=7); ax.set_ylim(-0.05, 1.05)
    jc = et.get('joint_cochran', {})
    if jc.get('p_value') is not None:
        add_stats_text(ax, f"Joint Cochran Q: p={jc['p_value']:.3f}", loc='upper left', fontsize=7)

    # ---- 7.7: T1 SAD vs T2 SAD scatter (identity line) ----
    ax = axes[2, 0]
    t1 = fb.get('t1_sad', np.array([]))
    t2 = fb.get('t2_sad', np.array([]))
    if len(t1) > 0:
        ax.scatter(t1, t2, s=60, alpha=0.6, color=COLORS['exposure_gen_1'], edgecolor='black', linewidth=0.5, zorder=5)
        lim = max(max(t1), max(t2), 14) + 1
        ax.plot([0, lim], [0, lim], 'k--', lw=1, alpha=0.4, label='Identity (no change)')
        ax.set_xlim(0, lim); ax.set_ylim(0, lim)
        # Shade improvement zone
        ax.fill_between([0, lim], [0, 0], [0, lim], alpha=0.04, color='green')
        ax.text(lim*0.7, lim*0.3, 'Improved', fontsize=8, color='green', alpha=0.6, style='italic')
    ax.set_xlabel('T1 SAD (error signal)'); ax.set_ylabel('T2 SAD')
    ax.set_title('7.7 T1 vs T2 SAD')
    corr = fb.get('t1_t2_correlation', {})
    if corr.get('rho') is not None:
        add_stats_text(ax, f"Spearman rho={corr['rho']:.3f}\np={corr['p_value']:.3f}", loc='upper left', fontsize=7)
    ax.legend(fontsize=7, loc='lower right')

    # ---- 7.8: T1 SAD vs Improvement (T1-T2) ----
    ax = axes[2, 1]
    imp = fb.get('improvement', np.array([]))
    if len(t1) > 0 and len(imp) > 0:
        colors_imp = ['green' if i > 0 else 'red' for i in imp]
        ax.scatter(t1, imp, s=60, c=colors_imp, alpha=0.6, edgecolor='black', linewidth=0.5, zorder=5)
        ax.axhline(y=0, color='black', lw=0.8, ls='-')
        # Regression line if enough data
        if len(t1) >= 5:
            z = np.polyfit(t1, imp, 1)
            x_line = np.linspace(min(t1), max(t1), 50)
            ax.plot(x_line, np.polyval(z, x_line), '--', color='orange', lw=2, alpha=0.7)
        ax.fill_between(ax.get_xlim(), 0, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 5, alpha=0.03, color='green')
        ax.fill_between(ax.get_xlim(), ax.get_ylim()[0] if ax.get_ylim()[0] < 0 else -5, 0, alpha=0.03, color='red')
    ax.set_xlabel('T1 SAD (error signal)'); ax.set_ylabel('Improvement (T1 SAD - T2 SAD)')
    ax.set_title('7.8 Error-Correction Relationship')
    ec = fb.get('error_correction', {})
    note = ''
    if ec.get('rho') is not None:
        note = f"rho={ec['rho']:.3f}, p={ec['p_value']:.3f}\n(includes RTM*)"
    add_stats_text(ax, note, loc='upper left', fontsize=7)
    ax.text(0.98, 0.02, '*Regression to mean\n  inflates this correlation', transform=ax.transAxes,
            fontsize=5.5, ha='right', va='bottom', color='gray', style='italic')

    # ---- 7.9: Improvement by T1 Feedback Band ----
    ax = axes[2, 2]
    band_stats = fb.get('band_stats', {})
    band_order = ['Low (0-2)', 'Mid (3-4)', 'High (5-6)', 'VHigh (7+)']
    band_colors_map = {'Low (0-2)': '#4CAF50', 'Mid (3-4)': '#FF9800', 'High (5-6)': '#FF5722', 'VHigh (7+)': '#D32F2F'}
    if band_stats:
        x_bands = np.arange(len(band_order))
        means_b = [band_stats.get(b, {}).get('imp_mean', 0) for b in band_order]
        ns = [band_stats.get(b, {}).get('n', 0) for b in band_order]
        colors_b = [band_colors_map.get(b, 'gray') for b in band_order]
        bars = ax.bar(x_bands, means_b, color=colors_b, alpha=0.8, edgecolor='black', linewidth=0.5)
        for i, (m, n) in enumerate(zip(means_b, ns)):
            if n > 0:
                ax.text(i, m + (0.15 if m >= 0 else -0.3), f'n={n}', ha='center', fontsize=7)
        ax.axhline(y=0, color='black', lw=0.8)
        ax.set_xticks(x_bands); ax.set_xticklabels(band_order, fontsize=8)
        # Hypothesis tests: Jonckheere-Terpstra trend across ordered bands +
        # continuous (un-binned) Spearman rho (T1 SAD vs improvement). RTM caveat.
        jt = fb.get('jt_trend', {})
        ec = fb.get('error_correction', {})
        lines = []
        if jt:
            lines.append(f"J-T trend: z={jt['z']:.2f}, p={jt['p_value']:.3f} "
                         f"{interpret_p_value(jt['p_value'])}")
        if ec.get('rho') is not None and not np.isnan(ec.get('rho', np.nan)):
            lines.append(f"T1 vs Imp (cont.): rho={ec['rho']:.3f}, "
                         f"p={ec['p_value']:.3f} {interpret_p_value(ec['p_value'])}")
        if lines:
            add_stats_text(ax, '\n'.join(lines), loc='upper left', fontsize=6)
        ax.text(0.98, 0.02, 'exploratory; RTM inflates band differences', transform=ax.transAxes,
                fontsize=5.5, ha='right', va='bottom', color='gray', style='italic')
    ax.set_xlabel('T1 Feedback Band (SAD range)'); ax.set_ylabel('Mean Improvement (T1-T2)')
    ax.set_title('7.9 Improvement by Feedback Band')

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 7 saved to: {save_path}")
    return fig


# ============================================================================
# FIGURE 8: RANGE CONVERGENCE & ALLUVIAL (1x3)
# ============================================================================
# 8.1 Proportion in [4,6] boxplot  8.2 % in [4,6] by role  8.3 Alluvial

def create_figure8(df, summary_df, results, save_path=None):
    """Figure 8: Range convergence and alluvial flow (1x3)."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Figure 8: Range Convergence & Category Flow', fontsize=14, fontweight='bold')
    from matplotlib.lines import Line2D
    et = results.get('est_trends', {})
    x_phases = np.arange(4)
    phase_labels = [PHASE_SHORT[p] for p in PHASE_ORDER]

    # ---- 8.1: Proportion in [4,6] per participant, boxplot ----
    ax = axes[0]
    pir = et.get('prop_in_range', np.array([]))
    if pir.size > 0:
        box_data = [pir[:, i][~np.isnan(pir[:, i])] for i in range(4)]
        bp = ax.boxplot(box_data, positions=np.arange(1, 5), patch_artist=True, widths=0.5)
        for patch, phase in zip(bp['boxes'], PHASE_ORDER):
            patch.set_facecolor(COLORS[phase]); patch.set_alpha(0.6)
        # Strip dots
        rng_j = np.random.default_rng(42)
        for i, vals in enumerate(box_data):
            jx = rng_j.uniform(-0.15, 0.15, size=len(vals))
            ax.scatter(i + 1 + jx, vals, s=15, alpha=0.5, color=COLORS[PHASE_ORDER[i]], edgecolor='black', linewidth=0.2, zorder=5)
    ax.set_xticks(np.arange(1, 5)); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('Proportion of Items in [4,6]'); ax.set_title('8.1 Range Convergence (per participant)')
    ax.set_ylim(-0.05, 1.05)
    rf = et.get('range_friedman', {})
    if rf.get('p_value') is not None:
        add_stats_text(ax, f"Friedman: p={rf['p_value']:.3f} {interpret_p_value(rf['p_value'])}", loc='upper left', fontsize=7)

    # ---- 8.2: % in [4,6] by item role ----
    ax = axes[1]
    rir = et.get('role_in_range', {})
    if rir:
        w = 0.22
        for r_idx, (role, color) in enumerate([('dominant', COLORS['dominant']), ('medium', COLORS['medium']), ('rare', COLORS['rare'])]):
            vals = rir.get(role, [0]*4)
            ax.bar(x_phases + (r_idx - 1) * w, vals, w, label=role.title(), color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.set_xticks(x_phases); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('% in [4,6] Range'); ax.set_title('8.2 Range Convergence by Item Role')
    ax.legend(fontsize=7); ax.set_ylim(0, 105)
    # Cochran's Q annotations
    cochran_lines = []
    for role in ['dominant', 'medium', 'rare']:
        cq = et.get(f'cochran_{role}', {})
        if cq.get('p_value') is not None:
            cochran_lines.append(f"{role.title()}: Q={cq['Q']:.1f}, p={cq['p_value']:.3f}")
    if cochran_lines:
        add_stats_text(ax, '\n'.join(cochran_lines), loc='upper right', fontsize=6)

    # ---- 8.3: Alluvial - Dominant item category flow ----
    ax = axes[2]
    dom_bins = et.get('dom_bins', {})
    bin_labels = et.get('bin_labels', ['0-1','2-3','4-5','6','7+'])
    bin_colors = ['#d32f2f', '#ff9800', '#ffeb3b', '#4caf50', '#9c27b0']

    # Build per-participant category sequence
    categories = []
    for _, row in summary_df.iterrows():
        cat_row = []
        for prefix in ['Blind', 'Icon', 'T1', 'T2']:
            est = row.get(f'{prefix}_est4', np.nan)
            if pd.isna(est):
                cat_row.append(-1)
            elif est <= 1: cat_row.append(0)
            elif est <= 3: cat_row.append(1)
            elif est <= 5: cat_row.append(2)
            elif est == 6: cat_row.append(3)
            else: cat_row.append(4)
        categories.append(cat_row)
    categories = np.array(categories)

    # Draw alluvial: for each transition (phase i -> i+1), draw ribbons
    n_bins = 5
    for trans in range(3):
        x_left = trans
        x_right = trans + 1
        # Count transitions
        trans_counts = np.zeros((n_bins, n_bins))
        for row in categories:
            if row[trans] >= 0 and row[trans + 1] >= 0:
                trans_counts[int(row[trans]), int(row[trans + 1])] += 1

        # Draw ribbons
        y_left = np.zeros(n_bins)
        for b in range(n_bins):
            y_left[b] = trans_counts[b, :].sum()
        y_right = np.zeros(n_bins)
        for b in range(n_bins):
            y_right[b] = trans_counts[:, b].sum()

        # Normalize positions
        total = max(categories.shape[0], 1)
        cum_left = np.cumsum([0] + [y_left[b]/total for b in range(n_bins)])
        cum_right = np.cumsum([0] + [y_right[b]/total for b in range(n_bins)])

        # Draw stacked bars at each position
        for b in range(n_bins):
            ax.barh(cum_left[b] + y_left[b]/(2*total), 0.08, height=y_left[b]/total,
                    left=x_left - 0.04, color=bin_colors[b], edgecolor='white', linewidth=0.5, alpha=0.8)
            ax.barh(cum_right[b] + y_right[b]/(2*total), 0.08, height=y_right[b]/total,
                    left=x_right - 0.04, color=bin_colors[b], edgecolor='white', linewidth=0.5, alpha=0.8)

        # Draw flow ribbons between categories
        offset_left = np.zeros(n_bins)
        for b_from in range(n_bins):
            offset_right_local = np.zeros(n_bins)
            for b_to in range(n_bins):
                count = trans_counts[b_from, b_to]
                if count > 0:
                    h = count / total
                    y1 = cum_left[b_from] + offset_left[b_from]
                    y2 = cum_right[b_to] + sum(trans_counts[:b_from, b_to]) / total
                    # Bezier-like ribbon
                    xs = np.linspace(x_left + 0.04, x_right - 0.04, 50)
                    t = (xs - x_left - 0.04) / (x_right - x_left - 0.08)
                    y_top = y1 + h + (y2 + h - y1 - h) * (3 * t**2 - 2 * t**3)
                    y_bot = y1 + (y2 - y1) * (3 * t**2 - 2 * t**3)
                    ax.fill_between(xs, y_bot, y_top, color=bin_colors[b_from], alpha=0.15)
                    offset_left[b_from] += h

    ax.set_xlim(-0.2, 3.2); ax.set_ylim(-0.02, 1.02)
    ax.set_xticks(range(4)); ax.set_xticklabels(phase_labels)
    ax.set_ylabel('Proportion'); ax.set_title('8.3 Dominant Item Category Flow')
    # Legend outside plot to avoid overlay
    handles = [plt.Rectangle((0,0),1,1, color=bin_colors[i], alpha=0.8) for i in range(n_bins)]
    ax.legend(handles, bin_labels, fontsize=6, title='Est. bin', title_fontsize=7,
              loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight'); report(f"Figure 8 saved to: {save_path}")
    return fig


# ============================================================================
# MAIN ANALYSIS PIPELINE
# ============================================================================
# Order: Descriptives (Fig 1) -> Prior + Exact Match (Fig 2) ->
#   Friedman + Q2-Q5 + Q5b Learning (Fig 3) -> Q6 Items + Alt Errors + Dist Fit (Fig 4) ->
#   Timing with RT stats (Fig 5) -> Q7 Self-report (Fig 6) ->
#   Estimation Trends (Fig 7) -> Range Convergence (Fig 8)
# Outputs: 8 figures, 3 CSVs, 1 text report.

def run_analysis(source=None, use_gui=False, output_dir=None,
                 save_figures=True, save_subfigures=False):
    """Run complete pipeline. Returns df, summary_df, results, 8 figures.

    save_figures:    when False, figures are created in memory but not written to
                     disk (useful for interactive viewing in Spyder). Figure
                     objects are still returned.
    save_subfigures: when True, each panel/subplot of every figure is saved as a
                     separate PNG under <output_dir>/subfigures/. Independent of
                     save_figures.
    """
    clear_report()

    report("=" * 70)
    report("ONESHOT EXPERIMENT ANALYSIS")
    report(f"Version 29.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report("=" * 70)

    # ---- 1. Load ----
    report("\n" + "-" * 50)
    report("LOADING DATA")
    report("-" * 50)
    df = load_data(source=source, use_gui=use_gui)
    report(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # ---- 2. Preprocess ----
    report("\nPreprocessing...")
    df = preprocess_data(df)

    # ---- 3. Validate ----
    validation = validate_data(df)

    # ---- 4. Subject summary ----
    report("\nCreating subject summary...")
    summary_df = get_subject_summary(df)
    report(f"Summary created for {len(summary_df)} subjects")

    # ---- 5. Output setup ----
    if output_dir is None:
        if isinstance(source, str):
            output_dir = Path(source).parent
        elif isinstance(source, (list, tuple)) and len(source) > 0:
            output_dir = Path(source[0]).parent
        else:
            output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    n_subjects = len(summary_df)
    prefix = f"OneShot_S{summary_df['subject_nr'].iloc[0]}" if n_subjects == 1 else f"OneShot_N{n_subjects}"

    # ============================================================
    # ANALYSIS - ordered by figure grouping
    # ============================================================
    results = {}

    # ---- Figure 1: Descriptives ----
    results['descriptives'] = run_descriptives(df, summary_df)

    # ---- Figure 2: Prior Analysis ----
    results['q1'] = analyze_population_prior(df, summary_df)        # Q1: prior shape
    results['exact_match'] = analyze_exact_matches(df, summary_df)  # Exact match rates

    # ---- Multinomial Log-Probability (v19) ----
    results['multinomial_prob'] = analyze_multinomial_probability(df, summary_df)

    # ---- Distribution Space (v22) ----
    results['dist_space'] = analyze_distribution_space(df, summary_df)

    # ---- Prior Fingerprint, Bayesian Model, Prior Predicts Learning (v23) ----
    results['fingerprint'] = analyze_prior_fingerprint(df, summary_df)
    results['bayesian'] = analyze_bayesian_model(df, summary_df)
    results['prior_learning'] = analyze_prior_predicts_learning(df, summary_df)

    # ---- Figure 3: Learning Trajectory ----
    results['friedman'] = run_friedman_omnibus(summary_df)           # Omnibus
    results['q2'] = analyze_shape_effect(df, summary_df)             # Blind -> Icon
    results['q_blind_t1'] = analyze_blind_vs_t1(df, summary_df)      # Blind -> T1 (icon+exposure)
    results['q3'] = analyze_exposure_effect(df, summary_df)          # Icon -> T1
    results['q4'] = analyze_repetition_effect(df, summary_df)        # T1 -> T2
    results['q5'] = analyze_total_learning(df, summary_df)           # Blind -> T2 [PRIMARY]
    results['Q_icon_t2'] = analyze_icon_vs_t2(df, summary_df)        # Icon -> T2 (exposure learning)

    # Q5b: Prior-Test correlation
    report("\n--- Prior Quality vs Test Quality ---")
    prior_test = {}
    prior_means = ((summary_df['Blind_sad'] + summary_df['Icon_sad']) / 2).dropna()
    test_means = ((summary_df['T1_sad'] + summary_df['T2_sad']) / 2).dropna()
    valid_idx = prior_means.index.intersection(test_means.index)
    if len(valid_idx) > 2:
        rho, p = stats.spearmanr(prior_means.loc[valid_idx], test_means.loc[valid_idx])
        prior_test = {'rho': rho, 'p_value': p, 'n': len(valid_idx)}
        report(f"Prior SAD (Blind+Icon mean) vs Test SAD (T1+T2 mean): rho={rho:.3f}, p={p:.4f} {interpret_p_value(p)}")
    results['prior_test_corr'] = prior_test

    # ---- Figure 4: Item Estimation ----
    results['q6'] = analyze_item_learning(df, summary_df)
    results['alt_errors'] = analyze_alternative_errors(df, summary_df)
    results['dist_fit'] = analyze_distribution_fit(df, summary_df)

    # ---- Figure 5: Timing (RT, completion, deliberation) ----
    results['rt'] = analyze_rt(df, summary_df)

    # ---- Figure 6: Self-Report ----
    results['q7'] = analyze_self_report(df, summary_df)

    # ---- Figures 7-8: Estimation Trends ----
    results['est_trends'] = analyze_estimation_trends(df, summary_df)

    # ---- Feedback Utilization ----
    results['feedback'] = analyze_feedback_utilization(df, summary_df)

    # ============================================================
    # FIGURES (8 figures, thematically organized)
    # ============================================================
    report("\n" + "-" * 50)
    report("CREATING FIGURES")
    report("-" * 50)

    # When save_figures is False, pass save_path=None so figures stay in memory.
    def _fig_path(name):
        return (output_dir / f"{prefix}_{name}_{timestamp}.png") if save_figures else None

    fig1_path = _fig_path("Fig1_Descriptives")
    fig2_path = _fig_path("Fig2_Prior")
    fig3_path = _fig_path("Fig3_Learning")
    fig4_path = _fig_path("Fig4_Items")
    fig5_path = _fig_path("Fig5_Timing")
    fig6_path = _fig_path("Fig6_SelfReport")
    fig7_path = _fig_path("Fig7_EstTrends")
    fig8_path = _fig_path("Fig8_RangeFlow")

    fig1 = create_figure1(df, summary_df, results, save_path=fig1_path)
    fig2 = create_figure2(df, summary_df, results, save_path=fig2_path)
    fig3 = create_figure3(df, summary_df, results, save_path=fig3_path)
    fig4 = create_figure4(df, summary_df, results, save_path=fig4_path)
    fig5 = create_figure5(df, summary_df, results, save_path=fig5_path)
    fig6 = create_figure6(df, summary_df, results, save_path=fig6_path)
    fig7 = create_figure7(df, summary_df, results, save_path=fig7_path)
    fig8 = create_figure8(df, summary_df, results, save_path=fig8_path)

    # ---- Figure 9: Distribution Space (v22) ----
    fig9_path = _fig_path("Fig9_DistSpace")
    fig9 = create_figure_distribution_space(df, summary_df, results, save_path=fig9_path)

    # ---- Optional: export each subplot as a standalone PNG ----
    if save_subfigures:
        for _fig, _name in [(fig1, 'Fig1'), (fig2, 'Fig2'), (fig3, 'Fig3'),
                            (fig4, 'Fig4'), (fig5, 'Fig5'), (fig6, 'Fig6'),
                            (fig7, 'Fig7'), (fig8, 'Fig8'), (fig9, 'Fig9')]:
            if _fig is not None:
                save_individual_panels(_fig, _name, output_dir, timestamp)

    # ============================================================
    # SAVE OUTPUTS
    # ============================================================
    report("\n" + "-" * 50)
    report("SAVING OUTPUTS")
    report("-" * 50)

    save_summary_table(summary_df, output_dir / f"{prefix}_Summary_{timestamp}.csv")
    save_descriptive_table(results, output_dir / f"{prefix}_Descriptives_{timestamp}.csv")
    save_statistical_results(results, output_dir / f"{prefix}_Statistics_{timestamp}.csv")

    # ---- Results Summary Table (v14) ----
    results_table = generate_results_summary(results, n_subjects=len(summary_df))
    results_table_path = output_dir / f"{prefix}_ResultsSummary_{timestamp}.csv"
    results_table.to_csv(results_table_path, index=False, encoding='utf-8-sig')
    report(f"Results summary table saved to: {results_table_path}")

    # ---- Email Report (v15) ----
    email_text = generate_email_report(results, n_subjects=len(summary_df))
    email_path = output_dir / f"{prefix}_EmailReport_{timestamp}.txt"
    with open(email_path, 'w', encoding='utf-8') as f:
        f.write(email_text)
    report(f"Email report saved to: {email_path}")

    # ---- PDF Report with embedded figures (v15) ----
    # When save_figures=False the PNGs were never written, so emit empty paths:
    # the .md writes harmless empty image links and the PDF converter's
    # Path(fig_path).exists() guard cleanly skips them.
    if save_figures:
        figure_paths = {
            'fig1': str(output_dir / f"{prefix}_Fig1_Descriptives_{timestamp}.png"),
            'fig2': str(output_dir / f"{prefix}_Fig2_Prior_{timestamp}.png"),
            'fig3': str(output_dir / f"{prefix}_Fig3_Learning_{timestamp}.png"),
            'fig4': str(output_dir / f"{prefix}_Fig4_Items_{timestamp}.png"),
            'fig5': str(output_dir / f"{prefix}_Fig5_Timing_{timestamp}.png"),
            'fig7': str(output_dir / f"{prefix}_Fig7_EstTrends_{timestamp}.png"),
        }
    else:
        figure_paths = {k: '' for k in ('fig1', 'fig2', 'fig3', 'fig4', 'fig5', 'fig7')}
    md_path = output_dir / f"{prefix}_Report_{timestamp}.md"
    pdf_path = output_dir / f"{prefix}_Report_{timestamp}.pdf"
    try:
        generate_markdown_report(results, figure_paths, md_path, n_subjects=len(summary_df))
        convert_md_report_to_pdf(md_path, figure_paths, pdf_path)
    except Exception as e:
        report(f"Report generation failed: {e}")

    report_path = output_dir / f"{prefix}_Report_{timestamp}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(REPORT_LINES))
    report(f"Report saved to: {report_path}")

    report("\n" + "=" * 70)
    report("ANALYSIS COMPLETE")
    report("=" * 70)

    return df, summary_df, results, (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8)


# ============================================================================
# ENTRY POINT - Command-line interface
# ============================================================================
# Usage: py oneshot_analysis_v11.py [files] [-o output_dir] [-g]
# No args: opens GUI file picker (if tkinter available).

def main():
    """Command-line entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='OneShot Experiment Analysis v7.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python oneshot_analysis_v11.py                          # GUI
  python oneshot_analysis_v11.py data.csv                 # Single file
  python oneshot_analysis_v11.py s1.csv s2.csv            # Multiple files
  python oneshot_analysis_v11.py *.csv -o ./results       # All CSVs
        """
    )
    parser.add_argument('files', nargs='*', help='CSV file(s)')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('-g', '--gui', action='store_true', help='GUI file dialog')

    args = parser.parse_args()

    if args.files:
        source = args.files if len(args.files) > 1 else args.files[0]
        use_gui = False
    elif args.gui:
        source, use_gui = None, True
    else:
        if HAS_TKINTER:
            source, use_gui = None, True
        else:
            parser.print_help()
            sys.exit(1)

    try:
        df, summary_df, results, figures = run_analysis(
            source=source, use_gui=use_gui, output_dir=args.output)
        plt.show()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
