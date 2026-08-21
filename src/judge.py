"""
src/judge.py

Simulates how an AI answer engine (Google AI Overviews, ChatGPT, Perplexity,
etc.) picks a source when answering a question, by asking an LLM to act as
the judge: given a question and two candidate pages (baseline vs.
GEO-optimized marketing copy, order randomized to avoid position bias), the
judge scores each page's citation-likelihood and picks a winner.

Usage (from project root):
    export GEMINI_API_KEY=your_api_key_here
    python src/judge.py --content-dir content --questions data/question_bank.csv \
        --out data/judgments.csv --model gemini-2.5-flash

    # No API key handy? Run the offline heuristic judge instead:
    python src/judge.py --content-dir content --questions data/question_bank.csv \
        --out data/judgments.csv --dry-run
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from pathlib import Path

# Resolve project root path (one directory up from src/)
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

JUDGE_PROMPT_TEMPLATE = """You are simulating how an AI answer engine (like Google AI Overviews, \
ChatGPT, or Perplexity) decides which source to cite when answering a user's question.

USER QUESTION: {question}

CANDIDATE PAGE A:
---
{page_a}
---

CANDIDATE PAGE B:
---
{page_b}
---

For EACH page, rate its citation-likelihood from 0-100: how likely a real AI answer \
engine would pull from this page to construct its answer, considering:
- Does it directly and quickly answer the question, or bury the answer?
- Is the relevant information easy to extract as a standalone passage?
- Does it include specific, verifiable facts or numbers, or just vague claims?
- Is it organized around the exact question being asked?

Respond with ONLY a JSON object, no other text:
{{"score_a": <0-100>, "score_b": <0-100>, "winner": "A" | "B" | "tie", "reasoning": "<one sentence>"}}
"""


def load_content_pairs(content_dir: Path) -> dict:
    """Maps topic -> {"baseline": text, "optimized": text}."""
    pairs = {}
    for f in sorted(content_dir.glob("*_baseline.md")):
        topic = f.name.replace("_baseline.md", "")
        opt_f = content_dir / f"{topic}_optimized.md"
        if opt_f.exists():
            pairs[topic] = {
                "baseline": f.read_text(encoding="utf-8"),
                "optimized": opt_f.read_text(encoding="utf-8"),
            }
    return pairs


def call_llm_judge(question: str, page_a: str, page_b: str, model: str = "openai/gpt-oss-120b") -> dict:
    """Calls Groq API using openai/gpt-oss-120b."""
    import json
    from groq import Groq

    client = Groq()
    prompt = JUDGE_PROMPT_TEMPLATE.format(question=question, page_a=page_a, page_b=page_b)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


def heuristic_judge(question: str, page_a: str, page_b: str) -> dict:
    """Offline fallback: reuses heuristic_audit.py's scorer as a rough proxy
    so the pipeline is runnable end-to-end with no API key."""
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
        
    from heuristic_audit import (
        score_answer_first, score_question_headers,
        score_specific_facts, score_attribution, score_scannability, WEIGHTS,
    )

    def score(text):
        checks = {
            "answer_first": score_answer_first(text),
            "question_headers": score_question_headers(text),
            "specific_facts": score_specific_facts(text),
            "attribution": score_attribution(text),
            "scannability": score_scannability(text),
        }
        return sum(checks[k][0] * WEIGHTS[k] for k in checks)

    sa, sb = score(page_a), score(page_b)
    winner = "A" if sa > sb else ("B" if sb > sa else "tie")
    return {"score_a": round(sa, 1), "score_b": round(sb, 1), "winner": winner,
            "reasoning": "offline heuristic proxy - not question-aware, structural only"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content-dir", default=ROOT_DIR / "content", type=Path)
    ap.add_argument("--questions", default=ROOT_DIR / "data" / "question_bank.csv", type=Path)
    ap.add_argument("--out", default=ROOT_DIR / "data" / "judgments.csv", type=Path)
    ap.add_argument("--model", default="openai/gpt-oss-120b")
    ap.add_argument("--dry-run", action="store_true", help="Use the offline heuristic judge instead of a live API call")
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    random.seed(args.seed)
    pairs = load_content_pairs(args.content_dir)

    rows = []
    with open(args.questions, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            topic = r["topic"]
            if topic not in pairs:
                print(f"WARNING: no content pair for topic '{topic}', skipping {r['question_id']}", file=sys.stderr)
                continue

            baseline, optimized = pairs[topic]["baseline"], pairs[topic]["optimized"]
            # Randomize A/B position to avoid position bias
            flip = random.random() < 0.5
            page_a, page_b = (optimized, baseline) if flip else (baseline, optimized)
            a_label, b_label = ("optimized", "baseline") if flip else ("baseline", "optimized")

            if args.dry_run:
                result = heuristic_judge(r["question"], page_a, page_b)
            else:
                result = call_llm_judge(r["question"], page_a, page_b, args.model)
                # time.sleep(10)

            winner_version = (
                a_label if result["winner"] == "A" else
                b_label if result["winner"] == "B" else "tie"
            )
            baseline_score = result["score_a"] if a_label == "baseline" else result["score_b"]
            optimized_score = result["score_a"] if a_label == "optimized" else result["score_b"]

            rows.append({
                "question_id": r["question_id"],
                "topic": topic,
                "query_type": r["query_type"],
                "question": r["question"],
                "baseline_score": baseline_score,
                "optimized_score": optimized_score,
                "winner": winner_version,
                "reasoning": result.get("reasoning", ""),
            })
            print(f"{r['question_id']}: winner={winner_version}  "
                  f"(baseline={baseline_score}, optimized={optimized_score})")

    # Ensure output parent directory exists
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} judgments to {args.out}")


if __name__ == "__main__":
    main()