"""Smoke test for oneshot_analysis_v29.

Runs the full analysis pipeline against a set of subject CSVs and prints the
keys produced for the learning comparisons (q_blind_t1, Q_icon_t2, q3, q4).

Data location resolution (first match wins):
  1. command-line argument: python _run_v27_smoke.py <glob_or_dir>
  2. environment variable:   ONESHOT_DATA=<glob_or_dir>
  3. default:                ./sample_data/oneshot_subject_*.csv
"""
import matplotlib
matplotlib.use('Agg')
import glob
import os
import sys

import oneshot_analysis_v29 as m


def resolve_csvs():
    arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('ONESHOT_DATA')
    if not arg:
        arg = os.path.join(os.path.dirname(__file__), 'sample_data')
    # Accept either a directory or a glob pattern.
    if os.path.isdir(arg):
        pattern = os.path.join(arg, 'oneshot_subject_*.csv')
    else:
        pattern = arg
    return sorted(glob.glob(pattern))


csvs = resolve_csvs()
print("CSV count:", len(csvs))
if not csvs:
    sys.exit("No subject CSVs found. Pass a directory or glob as the first arg, "
             "or set ONESHOT_DATA.")

out = "_scratch_v29_out"
os.makedirs(out, exist_ok=True)
df, summary_df, results, figures = m.run_analysis(
    source=csvs, output_dir=out, save_subfigures=True)
print("RUN DONE")
print("q_blind_t1 keys:", list(results.get('q_blind_t1', {}).keys()))
print("Q_icon_t2 keys:", list(results.get('Q_icon_t2', {}).keys()))
print("q3 keys:", list(results.get('q3', {}).keys()))
print("q4 keys:", list(results.get('q4', {}).keys()))
