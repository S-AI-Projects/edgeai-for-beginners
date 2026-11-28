"""
Token-Budget Preflight Boundary-Case Example (Teaching Approximation)

NOTE: This module uses deterministic whitespace splitting (`prompt.split()`) as
a teaching approximation to demonstrate SLMOps preflight budget gating on
smallest valid, exact-boundary, and invalid inputs. It is NOT a real model
tokenizer (such as BPE, WordPiece, or SentencePiece) and makes no claims about
real hardware memory, latency, or trained model accuracy.
"""

from __future__ import annotations

from typing import Any


TOKENIZER_NOTE = (
    "Teaching approximation (whitespace split), not the model's real tokenizer."
)


def check_token_budget(prompt: str, budget: int) -> dict[str, Any]:
    """Evaluate a prompt against a token budget and classify the boundary decision.

    Boundary rule:
        - Reject invalid inputs: non-string prompt -> TypeError;
          boolean or non-int budget -> TypeError; negative budget (< 0) -> ValueError.
        - If token_count <= budget: retain all tokens, removed_count = 0, truncated = False.
        - If token_count > budget: retain tokens[:budget],
          removed_count = token_count - budget, truncated = True.
    """
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a str.")
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise TypeError("budget must be an int (>= 0).")
    if budget < 0:
        raise ValueError("budget must be non-negative (>= 0).")

    tokens = prompt.split()
    token_count = len(tokens)
    retained_tokens = tokens[:budget]
    removed_count = max(0, token_count - budget)
    truncated = removed_count > 0

    if token_count == 0:
        boundary_case = "smallest_valid_empty"
    elif budget == 0:
        boundary_case = "zero_budget_boundary"
    elif token_count == budget:
        boundary_case = "exact_budget_boundary"
    elif token_count < budget:
        boundary_case = "within_budget"
    else:
        boundary_case = "over_budget_truncated"

    return {
        "input_token_count": token_count,
        "budget": budget,
        "retained_tokens": retained_tokens,
        "retained_count": len(retained_tokens),
        "removed_count": removed_count,
        "truncated": truncated,
        "boundary_case": boundary_case,
        "tokenizer_note": TOKENIZER_NOTE,
    }


def run_boundary_suite() -> list[dict[str, Any]]:
    """Run smallest-valid, exact-boundary, over-boundary, and invalid fixtures."""
    cases = [
        ("smallest_valid_empty", "", 0),
        ("smallest_valid_single", "edge", 1),
        ("exact_boundary", "one two three", 3),
        ("over_budget_by_one", "one two three four", 3),
        ("zero_budget_non_empty", "one", 0),
    ]
    outputs: list[dict[str, Any]] = []
    for label, prompt, budget in cases:
        result = check_token_budget(prompt, budget)
        outputs.append({"label": label, "prompt": prompt, "result": result})
    return outputs


if __name__ == "__main__":
    print("=== R04-T022 Token-Budget Preflight (Teaching Approximation) ===")
    for item in run_boundary_suite():
        print(
            f"[{item['label']}] prompt={item['prompt']!r} -> "
            f"retained={item['result']['retained_tokens']}, "
            f"removed={item['result']['removed_count']}, "
            f"truncated={item['result']['truncated']}, "
            f"case={item['result']['boundary_case']}"
        )
    try:
        check_token_budget("one two", -1)
    except ValueError as exc:
        print(f"[invalid_negative_budget] budget=-1 -> ValueError: {exc}")
