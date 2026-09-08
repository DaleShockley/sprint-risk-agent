"""Scores a classifier's predictions against the hand-labeled eval set.

Run the baseline report with:
    python -m eval.score

To score the live agent instead of the baseline: run `run_agent(repo)`
against the same repo these issues came from, build a
{issue_number: risk_or_"none"} dict from the verdicts (any issue not
returned by the agent counts as "none"), and pass it to
`score_predictions` alongside `load_eval_set()`. That step needs a
live ANTHROPIC_API_KEY and isn't wired into CI on purpose -- it costs
real API calls and depends on network access.
"""

import json
from pathlib import Path

from eval.baseline import classify

EVAL_SET_PATH = Path(__file__).parent / "labeled_issues.json"


def load_eval_set() -> list[dict]:
    return json.loads(EVAL_SET_PATH.read_text())


def score_predictions(predictions: dict[int, str], eval_set: list[dict]) -> dict:
    """predictions: {issue_number: predicted_risk}, using "none" for not-flagged."""
    total = len(eval_set)
    correct = 0
    per_category: dict[str, dict[str, int]] = {}

    for record in eval_set:
        number = record["issue"]["number"]
        expected = record["expected_risk"]
        predicted = predictions.get(number, "none")
        is_correct = int(predicted == expected)
        correct += is_correct

        bucket = per_category.setdefault(expected, {"total": 0, "correct": 0})
        bucket["total"] += 1
        bucket["correct"] += is_correct

    return {
        "accuracy": correct / total if total else 0.0,
        "total": total,
        "correct": correct,
        "per_category": per_category,
    }


def score_baseline() -> dict:
    eval_set = load_eval_set()
    predictions = {
        record["issue"]["number"]: classify(record["issue"], record["comments"]) or "none"
        for record in eval_set
    }
    return score_predictions(predictions, eval_set)


if __name__ == "__main__":
    results = score_baseline()
    print(f"Baseline accuracy: {results['correct']}/{results['total']} "
          f"({results['accuracy']:.0%})")
    for category, stats in sorted(results["per_category"].items()):
        print(f"  {category:<18} {stats['correct']}/{stats['total']}")
