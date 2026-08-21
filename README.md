# GEO Citation Lift: Does Optimizing Content for AI Search Actually Work?

### Problem statement

A growing share of searches never reach a website at all - the user (including me) reads an AI-generated answer (Google AI Overviews, ChatGPT, Perplexity) and moves on. For a content or marketing team, the question is no longer just "does this page rank," but "does this page get *cited* when an AI answers the question it addresses." 

Generative Engine Optimization (GEO) is the emerging practice of structuring content for that outcome - but most GEO advice is a list of tactics with no attached measurement. This project treats it as a measurement problem instead - the question asked here is **does restructuring content around known GEO tactics actually increase citation-likelihood, and does the effect hold up the same way across different kinds of questions?**

### Business context (simulated)

SettleIn is a fictional relocation-services company that provides moving services, and their website contains pages about new movers including move-in checklists, details on renters insurance, international relocation. In today's AI-summarized world, hardly anyone visits these pages and prefers the AI summary provided after the first search. 

To ensure that the resources provided by SettleIn reach their targeted audience, a data scientist recommends GEO (Generative Engine Optimization) on their pages to allow for it to show up in the AI Overviews. 

The current analysis uses three pages of traditional (baseline) marketing copies and each rewritten from typical brand-forward copy into a GEO-optimized version -
  -  move-in checklists
  -  renters insurance
  -  international relocation

### Method

1. **Content pairs** (`content/`): three topics, each with a *baseline* version (typical brand-led marketing copy) and a *GEO-optimized* version applying the tactics with the strongest published evidence behind them - an answer-first opening, question-shaped subheadings that mirror real search queries, specific and sourced facts in place of vague claims, and scannable structure
2. **Question bank** (`data/question_bank.csv`): 30 realistic questions a first-time renter or relocating professional might actually ask an AI assistant, split across the three topics and tagged `informational` vs. `transactional` (comparison/"best of" queries)
3. **LLM-judge harness** (`src/judge.py`): for each question, an LLM is shown both versions (order randomized to control for position bias) and asked to rate each page's citation-likelihood 0-100, the same way it would implicitly weigh sources when constructing a real AI-generated answer. Ships with a `--dry-run` offline heuristic fallback (`src/heuristic_audit.py`) so the pipeline runs end-to-end with no API key
4. **Paired significance test** (`src/analyze_results.py`): each question is a matched pair (baseline score, optimized score) - a **Wilcoxon signed-rank test** on the paired scores, broken out by query type and topic

## Results (pilot run, n=30)

The `data/pilot_judgments.csv` in this repo is a real pilot run - Claude acting as the judge model, following the exact rubric in `judge.py`, on all 30 questions.

| | Baseline (mean) | GEO-optimized (mean) | Lift | Win rate | Wilcoxon p |
|---|---|---|---|---|---|
| **Overall (n=30)** | 6.1 | 72.5 | +66.4 pts | 97% | p < 0.0001 |
| Informational (n=21) | - | - | +82.5 pts | 100% | p < 0.0001 |
| Transactional (n=9) | - | - | +28.7 pts | 89% | p = 0.0078 |

![Citation lift summary](results/citation_lift_summary.png)

**The headline lift is real but the interesting part is the segment split.** GEO restructuring helps most where it's designed to help - direct, answer-shaped informational questions ("what does renters insurance cover") saw the biggest gains, because the optimized pages have a header and a direct answer for almost exactly that question. Transactional / "best of" / comparison queries ("best renters insurance providers 2026") showed a much smaller lift, because no amount of restructuring fixes a content-*type* mismatch: a single-brand FAQ page, however well structured, is a poor fit for a query that expects a roundup of competitors. One question (`Q20`) came out a near-tie for exactly this reason. 

**The practical takeaway: GEO tactics are a content-structure fix for content-structure problems - they don't substitute for publishing the right content type for the query intent in the first place.**

### Limitations

- **This is a judge-model proxy, not scraped AI Overviews.** It measures "would an LLM judge say this looks citable," which is a reasonable stand-in but not a guarantee of real-world citation rates - the same gap between a lab experiment and a field result
- **Single judge, single pilot run, n=30.** Before trusting this beyond "the method works," the natural next steps are: run it against a live model via `judge.py` (no `--dry-run`) at a larger question-bank size, and ideally cross-check with a second judge model to rule out one model's idiosyncratic preferences
- **`heuristic_audit.py` is a structural sanity check, not a substitute for the LLM judge** - it can't tell whether content actually *answers* a question, only whether it's shaped like content that would

### Reproduce or extend

```bash
pip install -r requirements.txt

# Regenerate the pilot dataset (no API key needed)
python data/generate_pilot_judgments.py

# Run the offline heuristic judge end-to-end
python src/judge.py --content-dir content --questions data/question_bank.csv \
    --out data/judgments_dryrun.csv --dry-run

# Run the real LLM judge (requires ANTHROPIC_API_KEY)
python src/judge.py --content-dir content --questions data/question_bank.csv \
    --out data/judgments_live.csv --model claude-sonnet-4-6

# Analyze any judgments file
python src/analyze_results.py data/pilot_judgments.csv --chart results/citation_lift_summary.png
```

### Repo structure

```
geo-citation-lift/
├── content/            # baseline vs. GEO-optimized page pairs (3 topics)
├── data/
│   ├── question_bank.csv          # 30 target-audience questions, tagged by type
│   ├── generate_pilot_judgments.py
│   └── pilot_judgments.csv        # the pilot result set used above
├── src/
│   ├── judge.py            # LLM-judge harness (live API or --dry-run)
│   ├── heuristic_audit.py  # standalone rule-based GEO structure scorer
│   └── analyze_results.py  # paired Wilcoxon test + chart
├── results/
│   ├── citation_lift_summary.png
│   └── heuristic_scores.csv
└── requirements.txt
```

**Tools:** Python, pandas, scipy, matplotlib, Anthropic API · 

**Methods:** Paired Experimental Design, Wilcoxon Signed-Rank Test, LLM-as-Judge Evaluation, Generative Engine Optimization (GEO)
