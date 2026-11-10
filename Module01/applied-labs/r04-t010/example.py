#!/usr/bin/env python3
"""
Token Budget Preflight - Scenario Assessment (R04-T010)
Module 01: Real-World Case Studies

Concept:
Real-world edge AI case studies (e.g. mobile health assistants, industrial monitoring)
rely on predictable memory profiles. Token budget preflight filters input prompts
to prevent buffer overflows on constrained hardware.

Focus:
Scenario assessment with three applied questions:
1. Predict an output (prompt overflow behavior).
2. Diagnose a failure (negative budget error and remediation).
3. Choose a boundary policy (exact-capacity policy decision).
Provides factual rationale and executable checks for each.

Notice:
Uses deterministic whitespace splitting as a teaching approximation,
not the production subword/BPE tokenizer.
"""

from typing import List, Dict, Any, Tuple


class TokenBudgetPreflight:
    """
    Evaluates prompt lengths against a configured token budget.
    """

    def __init__(self, budget: int):
        if budget < 0:
            raise ValueError(f"Token budget cannot be negative: {budget}")
        self.budget = budget
        self.tokenizer_type = "teaching_approximation_whitespace"

    def tokenize(self, text: str) -> List[str]:
        cleaned = text.strip()
        return cleaned.split() if cleaned else []

    def check(self, prompt: str) -> Dict[str, Any]:
        tokens = self.tokenize(prompt)
        total = len(tokens)

        if total <= self.budget:
            retained = list(tokens)
            removed = []
        else:
            retained = tokens[:self.budget]
            removed = tokens[self.budget:]

        return {
            "prompt": prompt,
            "budget": self.budget,
            "total_tokens": tokens,
            "total_token_count": total,
            "retained_tokens": retained,
            "retained_count": len(retained),
            "removed_tokens": removed,
            "removed_count": len(removed),
            "truncated": len(removed) > 0,
            "tokenizer_note": "Teaching approximation (whitespace tokenization), not model's production BPE tokenizer",
        }


# =====================================================================
# Scenario Assessment: Questions, Rationales, and Executable Checks
# =====================================================================

SCENARIO_QUESTIONS = [
    {
        "id": "Q1_PREDICT_OUTPUT",
        "question": "Given budget=3 and prompt='edge ai on device inference', what tokens are retained and removed?",
        "expected_retained": ["edge", "ai", "on"],
        "expected_removed": ["device", "inference"],
        "expected_truncated": True,
        "rationale": "The first 3 tokens satisfy the budget limit of 3; the remaining 2 tokens are discarded.",
    },
    {
        "id": "Q2_DIAGNOSE_FAILURE",
        "question": "A deployment script initializes TokenBudgetPreflight(budget=-5). What failure occurs and why?",
        "expected_exception": "ValueError",
        "expected_msg_fragment": "Token budget cannot be negative",
        "rationale": "Memory token allocations must be non-negative integers; negative budgets represent invalid hardware allocations.",
    },
    {
        "id": "Q3_CHOOSE_BOUNDARY_POLICY",
        "question": "When prompt tokens exactly equal the configured budget (e.g. 5 tokens for budget 5), what is the truncation decision?",
        "expected_truncated": False,
        "expected_removed_count": 0,
        "rationale": "The exact boundary (tokens == budget) satisfies the constraint without exceeding memory limits; no truncation is needed.",
    },
]


def evaluate_assessment_question_1() -> Dict[str, Any]:
    checker = TokenBudgetPreflight(budget=3)
    res = checker.check("edge ai on device inference")
    q = SCENARIO_QUESTIONS[0]
    passed = (
        res["retained_tokens"] == q["expected_retained"]
        and res["removed_tokens"] == q["expected_removed"]
        and res["truncated"] == q["expected_truncated"]
    )
    return {"id": q["id"], "passed": passed, "actual": res, "rationale": q["rationale"]}


def evaluate_assessment_question_2() -> Dict[str, Any]:
    q = SCENARIO_QUESTIONS[1]
    caught = False
    try:
        TokenBudgetPreflight(budget=-5)
    except ValueError as e:
        caught = q["expected_msg_fragment"] in str(e)
    return {"id": q["id"], "passed": caught, "rationale": q["rationale"]}


def evaluate_assessment_question_3() -> Dict[str, Any]:
    checker = TokenBudgetPreflight(budget=5)
    res = checker.check("one two three four five")
    q = SCENARIO_QUESTIONS[2]
    passed = (
        res["truncated"] == q["expected_truncated"]
        and res["removed_count"] == q["expected_removed_count"]
    )
    return {"id": q["id"], "passed": passed, "actual": res, "rationale": q["rationale"]}


def run_demo() -> None:
    print("=== Module 01: Real-World Case Studies Scenario Assessment ===")
    print("Executing Scenario Assessment Checks:")
    q1 = evaluate_assessment_question_1()
    print(f"  Q1 (Predict Output): Passed={q1['passed']}")
    q2 = evaluate_assessment_question_2()
    print(f"  Q2 (Diagnose Failure): Passed={q2['passed']}")
    q3 = evaluate_assessment_question_3()
    print(f"  Q3 (Boundary Policy): Passed={q3['passed']}")


if __name__ == "__main__":
    run_demo()
