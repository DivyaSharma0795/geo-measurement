"""
heuristic_audit.py

A lightweight, API-free auditor that scores a piece of content on the
structural GEO (Generative Engine Optimization) tactics with the strongest
published evidence behind them:

  - Answer-first opening (does the piece state a direct answer in the
    first ~60 words, rather than building up to it?)
  - Question-shaped subheadings (AI systems pattern-match headers to the
    queries they're trying to answer)
  - Specific, checkable facts (numbers, ranges, dates) rather than vague claims
  - Explicit source/attribution language
  - Scannable structure (lists, short paragraphs)

This is NOT a substitute for judge.py's LLM-based evaluation - it can't tell
you whether an AI would actually *cite* a page. What it gives you is a fast,
free, reproducible proxy you can run on every draft before it ever reaches
an LLM judge (or a real search engine).

Usage:
    python heuristic_audit.py ../content/moving_checklist_baseline.md
    python heuristic_audit.py ../content/*.md --csv ../results/heuristic_scores.csv
"""

import argparse
import csv
import glob
import re
from pathlib import Path

WEIGHTS = {
    "answer_first": 25,
    "question_headers": 20,
    "specific_facts": 25,
    "attribution": 15,
    "scannability": 15,
}


def score_answer_first(text: str) -> tuple[float, str]:
    """Does a direct-answer-shaped sentence appear in the first ~60 words?"""
    words = text.split()
    opening = " ".join(words[:60])
    signals = [
        r"\bquick answer\b",
        r"\btl;?dr\b",
        r"^\*\*",  # bolded lead sentence, common answer-first pattern
    ]
    hit = any(re.search(p, opening, re.IGNORECASE | re.MULTILINE) for p in signals)
    return (1.0 if hit else 0.0, "direct-answer marker found in opening" if hit else "no direct-answer marker in first ~60 words")


def score_question_headers(text: str) -> tuple[float, str]:
    """Fraction of headers that are phrased as questions (end in '?')."""
    headers = re.findall(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)
    if not headers:
        return (0.0, "no headers found")
    q_headers = [h for h in headers if h.strip().endswith("?")]
    frac = len(q_headers) / len(headers)
    return (frac, f"{len(q_headers)}/{len(headers)} headers are question-shaped")


def score_specific_facts(text: str) -> tuple[float, str]:
    """Density of numbers/ranges/dollar figures per 100 words - capped."""
    words = len(text.split())
    numbers = re.findall(r"\$?\d[\d,]*(\.\d+)?%?", text)
    density = len(numbers) / max(words, 1) * 100
    # cap: 3+ specific figures per 100 words scores full marks
    frac = min(density / 3.0, 1.0)
    return (frac, f"{len(numbers)} specific figures across {words} words")


def score_attribution(text: str) -> tuple[float, str]:
    """Presence of an explicit sources/attribution line."""
    hit = bool(re.search(r"\*sources?:|\*figures?\s+reflect|\*timelines?\s+reflect", text, re.IGNORECASE))
    return (1.0 if hit else 0.0, "attribution line present" if hit else "no attribution line")


def score_scannability(text: str) -> tuple[float, str]:
    """Share of paragraphs that are bullet/numbered list items."""
    lines = [l for l in text.split("\n") if l.strip()]
    list_lines = [l for l in lines if re.match(r"^\s*[-*]\s+", l)]
    frac = min(len(list_lines) / max(len(lines) * 0.3, 1), 1.0)
    return (frac, f"{len(list_lines)} list lines out of {len(lines)} content lines")


def audit(path: str) -> dict:
    text = Path(path).read_text()
    checks = {
        "answer_first": score_answer_first(text),
        "question_headers": score_question_headers(text),
        "specific_facts": score_specific_facts(text),
        "attribution": score_attribution(text),
        "scannability": score_scannability(text),
    }
    total = sum(checks[k][0] * WEIGHTS[k] for k in checks)
    return {
        "file": Path(path).name,
        "geo_score": round(total, 1),
        **{f"{k}_note": v[1] for k, v in checks.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="Markdown files to audit (globs OK)")
    ap.add_argument("--csv", help="Optional path to write results as CSV")
    args = ap.parse_args()

    paths = []
    for f in args.files:
        paths.extend(sorted(glob.glob(f)))

    rows = [audit(p) for p in paths]
    for r in rows:
        print(f"{r['file']:45s}  GEO score: {r['geo_score']:5.1f} / 100")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nWrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
