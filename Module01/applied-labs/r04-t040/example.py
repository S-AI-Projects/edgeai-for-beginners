"""
Token-Budget Preflight: Direct Implementation vs. Independent Oracle.

Checks prompt length against a configured token budget using a deterministic
whitespace tokenizer (teaching approximation, not a model's real tokenizer).
Contracts:
  - Budget 3 with "one two three four" retains ["one", "two", "three"] and reports 1 removed token.
  - Empty input retains none (empty list) and reports 0 removed tokens.
  - Negative budget is rejected with ValueError.
  - Compares the direct implementation with an independent reference oracle.
"""

from typing import Dict, Any, List, Optional
import json


class TokenBudgetPreflight:
    """
    Direct preflight checker using whitespace tokenization.
    Explicitly labeled as a teaching approximation, not a model's BPE/WordPiece tokenizer.
    """

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple whitespace-based tokenization approximation."""
        if not text:
            return []
        return text.strip().split()

    @classmethod
    def apply_budget(cls, text: str, budget: int) -> Dict[str, Any]:
        """
        Validates budget, tokenizes input, and applies preflight bounds.
        """
        if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
            raise ValueError(f"Token budget must be a non-negative integer, got: {budget}")

        tokens = cls.tokenize(text)
        total_tokens = len(tokens)

        if total_tokens <= budget:
            retained = tokens
            removed_count = 0
            is_truncated = False
        else:
            retained = tokens[:budget]
            removed_count = total_tokens - budget
            is_truncated = True

        return {
            "budget": budget,
            "total_tokens": total_tokens,
            "retained_tokens": retained,
            "retained_count": len(retained),
            "removed_count": removed_count,
            "truncated": is_truncated,
            "reconstructed_text": " ".join(retained),
        }


# ---------------------------------------------------------------------------
# Independent Reference Oracle (Alternative Calculation / Expected-Result Table)
# ---------------------------------------------------------------------------
def independent_oracle_check(text: str, budget: int) -> Dict[str, Any]:
    """
    Independent functional calculation using python slicing and bounds.
    """
    if budget < 0:
        raise ValueError("Budget cannot be negative")
    toks = [t for t in text.strip().split() if t] if text else []
    n = len(toks)
    kept = toks[:max(0, budget)]
    return {
        "budget": budget,
        "total_tokens": n,
        "retained_tokens": kept,
        "retained_count": len(kept),
        "removed_count": max(0, n - budget),
        "truncated": n > budget,
        "reconstructed_text": " ".join(kept),
    }


def run_demo() -> Dict[str, Any]:
    # Canonical scenario 1: budget 3, "one two three four"
    res1 = TokenBudgetPreflight.apply_budget("one two three four", 3)
    oracle1 = independent_oracle_check("one two three four", 3)

    # Canonical scenario 2: empty input
    res2 = TokenBudgetPreflight.apply_budget("", 3)
    oracle2 = independent_oracle_check("", 3)

    # Negative budget scenario
    err = None
    try:
        TokenBudgetPreflight.apply_budget("one two", -1)
    except ValueError as e:
        err = str(e)

    return {
        "scenario_1": {"direct": res1, "oracle": oracle1, "agrees": res1 == oracle1},
        "scenario_2": {"direct": res2, "oracle": oracle2, "agrees": res2 == oracle2},
        "negative_budget_error": err
    }


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
