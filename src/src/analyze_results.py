"""
analyze_results.py

Treats each question as a matched pair (baseline score, optimized score) and
tests whether GEO optimization produces a statistically significant lift in
citation-likelihood, using a Wilcoxon signed-rank test (the right test for
paired, non-normal scores - the same paired-comparison logic used throughout
this portfolio's other experiments).

Usage:
    python analyze_results.py ../data/pilot_judgments.csv
"""

import argparse
import sys

import pandas as pd
from scipy import stats


def analyze(path: str):
    df = pd.read_csv(path)
    df["delta"] = df["optimized_score"] - df["baseline_score"]

    print(f"N = {len(df)} paired questions\n")

    # Overall paired test
    stat, p = stats.wilcoxon(df["optimized_score"], df["baseline_score"])
    win_rate = (df["winner"] == "optimized").mean()
    tie_rate = (df["winner"] == "tie").mean()
    print("=== Overall ===")
    print(f"Mean baseline score:  {df['baseline_score'].mean():.1f}")
    print(f"Mean optimized score: {df['optimized_score'].mean():.1f}")
    print(f"Mean lift:             {df['delta'].mean():+.1f} pts")
    print(f"Optimized win rate:    {win_rate:.0%}  (ties: {tie_rate:.0%})")
    print(f"Wilcoxon signed-rank:  W={stat:.1f}, p={p:.5f}")
    print()

    # Breakdown by query type - the segment-level story
    print("=== By query type ===")
    for qtype, sub in df.groupby("query_type"):
        s, p_sub = stats.wilcoxon(sub["optimized_score"], sub["baseline_score"])
        print(f"{qtype:15s}  n={len(sub):2d}  mean lift={sub['delta'].mean():+6.1f} pts  "
              f"win rate={((sub['winner'] == 'optimized').mean()):.0%}  p={p_sub:.5f}")
    print()

    # Breakdown by topic
    print("=== By topic ===")
    for topic, sub in df.groupby("topic"):
        print(f"{topic:25s}  n={len(sub):2d}  mean lift={sub['delta'].mean():+6.1f} pts  "
              f"win rate={((sub['winner'] == 'optimized').mean()):.0%}")

    return df


def make_chart(df: pd.DataFrame, out_path: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # Left: overall score distributions
    axes[0].boxplot(
        [df["baseline_score"], df["optimized_score"]],
        tick_labels=["Baseline", "GEO-optimized"],
        patch_artist=True,
        boxprops=dict(facecolor="#cfe2f3"),
    )
    axes[0].set_ylabel("LLM-judge citation-likelihood score")
    axes[0].set_title("Citation-likelihood: baseline vs. optimized")

    # Right: lift by query type
    by_type = df.groupby("query_type")["delta"].mean().sort_values()
    axes[1].barh(by_type.index, by_type.values, color="#6fa8dc")
    axes[1].set_xlabel("Mean lift in citation-likelihood (pts)")
    axes[1].set_title("Lift by query type")
    axes[1].axvline(0, color="black", linewidth=0.8)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"\nSaved chart to {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("judgments_csv")
    ap.add_argument("--chart", default=None, help="Optional path to save a summary chart")
    args = ap.parse_args()

    df = analyze(args.judgments_csv)
    if args.chart:
        make_chart(df, args.chart)
