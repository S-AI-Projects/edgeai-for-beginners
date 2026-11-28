"""
Token-Budget Preflight — Scenario Assessment (Teaching Approximation)

NOTE: This module uses deterministic whitespace splitting (`prompt.split()`) as
a teaching approximation to demonstrate SLM preflight token-budget enforcement
and three applied scenario-assessment questions. It is NOT the model's real
tokenizer (such as BPE, WordPiece, or SentencePiece) and makes no claims about
real hardware, cloud services, or trained-model performance.
"""

from __future__ import annotations

from typing import Any


TOKENIZER_NOTE = (
    "Teaching approximation (whitespace split), not the model's real tokenizer."
)


def check_token_budget(prompt: str, budget: int) -> dict[str, Any]:
    """Check prompt length against a configured whitespace-token budget."""
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a str.")
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise TypeError("budget must be an int (>= 0).")
    if budget < 0:
        raise ValueError("budget must be non-negative (>= 0).")

    tokens = prompt.split()
    retained_tokens = tokens[:budget]
    removed_count = max(0, len(tokens) - budget)

    return {
        "retained_tokens": retained_tokens,
        "retained_count": len(retained_tokens),
        "removed_count": removed_count,
        "truncated": removed_count > 0,
        "tokenizer_note": TOKENIZER_NOTE,
    }


def verify_q1_predict_output() -> dict[str, Any]:
    """Q1 (Predict an output): budget=3 on 'one two three four' retains 3 and removes 1."""
    result = check_token_budget("one two three four", budget=3)
    assert result["retained_tokens"] == ["one", "two", "three"]
    assert result["removed_count"] == 1
    assert result["truncated"] is True
    return result


def verify_q2_diagnose_failure() -> str:
    """Q2 (Diagnose a failure): negative budget raises ValueError instead of negative slicing."""
    try:
        check_token_budget("alpha beta", budget=-2)
    except ValueError as exc:
        return f"ValueError raised as expected: {exc}"
    raise AssertionError("Expected ValueError for negative budget.")


def verify_q3_boundary_policy() -> tuple[dict[str, Any], dict[str, Any]]:
    """Q3 (Choose a boundary policy): exact fit (<=) is un-truncated; budget=0 drops all."""
    exact_fit = check_token_budget("one two three", budget=3)
    zero_limit = check_token_budget("one", budget=0)
    assert exact_fit["retained_tokens"] == ["one", "two", "three"]
    assert exact_fit["removed_count"] == 0
    assert exact_fit["truncated"] is False
    assert zero_limit["retained_tokens"] == []
    assert zero_limit["removed_count"] == 1
    assert zero_limit["truncated"] is True
    return exact_fit, zero_limit


if __name__ == "__main__":
    print("=== R04-T030 Token-Budget Preflight Scenario Assessment ===")
    q1 = verify_q1_predict_output()
    q2 = verify_q2_diagnose_failure()
    q3_exact, q3_zero = verify_q3_boundary_policy()
    print("Q1 (predict output):", q1)
    print("Q2 (diagnose failure):", q2)
    print("Q3 (boundary exact):", q3_exact)
    print("Q3 (boundary zero):", q3_zero)
