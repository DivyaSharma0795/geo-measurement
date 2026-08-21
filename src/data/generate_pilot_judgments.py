"""
generate_pilot_judgments.py

This pilot dataset was produced by having Claude act as the judge model,
following the exact rubric in src/judge.py's JUDGE_PROMPT_TEMPLATE, on all
30 questions in question_bank.csv. It exists so the repo ships with a real,
inspectable result set without requiring an API key or spend before you've
decided whether the method is worth scaling up.

To reproduce or extend this with a live model (recommended before drawing
any real conclusions - one judge model, unvalidated, is a pilot, not proof):
    export ANTHROPIC_API_KEY=sk-ant-...
    python ../src/judge.py --content-dir ../content --questions question_bank.csv \
        --out judgments_live.csv --model claude-sonnet-4-6
"""

import csv

# (question_id, baseline_score, optimized_score, winner, reasoning)
PILOT_JUDGMENTS = [
    ("Q01", 8, 88, "optimized", "Optimized has a dedicated '1 week before' section answering this directly; baseline never mentions a timeline."),
    ("Q02", 5, 93, "optimized", "Optimized's header is a near-exact match to the question and lists the exact documents; baseline mentions no documents at all."),
    ("Q03", 5, 92, "optimized", "Optimized answers with a specific 10-14 day window; baseline never mentions utilities."),
    ("Q04", 10, 90, "optimized", "Optimized IS a timeline-structured checklist matching the query intent; baseline only asserts a checklist exists without showing one."),
    ("Q05", 5, 91, "optimized", "Optimized has a dedicated header naming exactly what to photograph and why; baseline has no relevant content."),
    ("Q06", 8, 75, "optimized", "Optimized covers photographing rooms and testing utilities on move-in day, though not framed as a dedicated 'inspection walkthrough' section."),
    ("Q07", 6, 85, "optimized", "Optimized gives a specific booking window (3-4 weeks) under a clear timeline; baseline is silent on timing."),
    ("Q08", 5, 40, "optimized", "Neither page is an app/service comparison; optimized is at least a usable standalone checklist resource, baseline offers nothing extractable."),
    ("Q09", 6, 55, "optimized", "Optimized functions as a plannable checklist itself, giving partial relevance; baseline is pure brand copy."),
    ("Q10", 4, 22, "optimized", "Neither page compares movers vs. DIY; optimized's brief mover-booking bullet gives a thin edge over baseline's total silence."),
    ("Q11", 8, 94, "optimized", "Optimized's header matches the question exactly and gives a direct yes/no-shaped answer with the lease-requirement nuance; baseline never answers the question."),
    ("Q12", 6, 95, "optimized", "Optimized gives a clean 3-part coverage breakdown; baseline never states what's covered."),
    ("Q13", 5, 96, "optimized", "Optimized gives a specific $15-30/month figure; baseline avoids all numbers."),
    ("Q14", 5, 80, "optimized", "Theft is explicitly named in optimized's coverage bullet; baseline doesn't mention theft or any peril."),
    ("Q15", 5, 93, "optimized", "Optimized has a dedicated header contrasting renters vs. landlord coverage; baseline doesn't address landlord insurance at all."),
    ("Q16", 5, 92, "optimized", "Optimized directly answers 'no, it's a lease requirement not a law'; baseline doesn't address legality."),
    ("Q17", 5, 82, "optimized", "Optimized explicitly states roommates need their own policy; baseline has no equivalent detail."),
    ("Q18", 6, 58, "optimized", "Optimized's price range is useful for a cost-driven query even without provider comparisons; baseline gives no pricing signal."),
    ("Q19", 5, 20, "optimized", "Neither page is a purchase/directory page; optimized's structure gives only a marginal edge."),
    ("Q20", 18, 14, "tie", "This is a 'best providers' roundup query - neither single-brand page is a good fit, and optimized's detailed FAQ structure doesn't compensate for the missing comparison content."),
    ("Q21", 6, 94, "optimized", "Optimized's header exactly matches the question with a specific document list; baseline never mentions documents."),
    ("Q22", 6, 93, "optimized", "Optimized gives specific freight timelines (4-8 weeks ocean, 1-2 weeks air); baseline never discusses shipping mechanics."),
    ("Q23", 8, 90, "optimized", "The entire optimized page is structured as this checklist; baseline only asserts expertise without showing a checklist."),
    ("Q24", 6, 92, "optimized", "Optimized directly answers '3 months minimum, driven by visa processing'; baseline gives no timeline."),
    ("Q25", 5, 78, "optimized", "Housing search guidance (guarantor/deposit norms) appears as a specific bullet in optimized; baseline doesn't address housing."),
    ("Q26", 4, 89, "optimized", "The 4-8 week ocean freight figure appears twice in optimized, directly and repeatably answering this; baseline has no shipping detail."),
    ("Q27", 4, 76, "optimized", "Optimized has a specific, if brief, bullet on notifying banks and checking account accessibility; baseline has nothing relevant."),
    ("Q28", 5, 35, "optimized", "Neither page names or compares moving companies; optimized's 'get quotes from two forwarders' advice is only marginally more useful than baseline's silence."),
    ("Q29", 6, 45, "optimized", "Optimized is topically closer (a relocation checklist) but still not a services directory; moderate, not strong, relevance."),
    ("Q30", 4, 28, "optimized", "Optimized's volume-vs-weight pricing note is a real fact but far short of an actual cost comparison; baseline offers nothing."),
]


def main():
    import pathlib
    qmap = {}
    with open(pathlib.Path(__file__).parent / "question_bank.csv") as f:
        for row in csv.DictReader(f):
            qmap[row["question_id"]] = row

    out_path = pathlib.Path(__file__).parent / "pilot_judgments.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question_id", "topic", "query_type", "question",
            "baseline_score", "optimized_score", "winner", "reasoning",
        ])
        writer.writeheader()
        for qid, base, opt, winner, reasoning in PILOT_JUDGMENTS:
            q = qmap[qid]
            writer.writerow({
                "question_id": qid,
                "topic": q["topic"],
                "query_type": q["query_type"],
                "question": q["question"],
                "baseline_score": base,
                "optimized_score": opt,
                "winner": winner,
                "reasoning": reasoning,
            })
    print(f"Wrote {len(PILOT_JUDGMENTS)} pilot judgments to {out_path}")


if __name__ == "__main__":
    main()
