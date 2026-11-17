"""
R04-T013: Token-Budget Preflight - Compare Two Approaches
Companion applied lab for Module03/03.DeployingSLMinCloud.md.

Demonstrates deterministic prompt length budgeting and truncation preflight:
- Tokenizer: whitespace-based splitting (explicitly labeled as a teaching approximation).
- Enforces non-negative budget; rejects negative budget.
- Computes retained tokens and explicitly reports removed/truncated count.
- Compares the direct slicing implementation against an independent reference calculation.

Prerequisites: Python 3 standard library only.
"""

from typing import Any, Dict, List


class TokenBudgetError(Exception):
    """Raised when token budget configuration or prompt input is invalid."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def tokenize_approx(text: str) -> List[str]:
    """
    Teaching approximation tokenizer: splits on whitespace.
    NOTE: This is a bounded pedagogical approximation, not a subword BPE or
    production SLM tokenizer (such as Phi-4's 200K TikToken/SentencePiece tokenizer).
    """
    if not isinstance(text, str):
        raise TokenBudgetError("INVALID_PROMPT", f"Prompt must be a string, got {type(text).__name__}.")
    stripped = text.strip()
    return stripped.split() if stripped else []


def check_token_budget_direct(prompt: str, budget: int) -> Dict[str, Any]:
    """
    Direct implementation: tokenizes prompt and slices to budget limit.
    """
    if not isinstance(budget, int) or budget < 0:
        raise TokenBudgetError("INVALID_BUDGET", f"Token budget must be a non-negative integer, got: {budget!r}")

    tokens = tokenize_approx(prompt)
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
        "total_tokens": total_tokens,
        "budget": budget,
        "retained_tokens": retained,
        "removed_count": removed_count,
        "truncated": is_truncated,
        "retained_text": " ".join(retained),
    }


def check_token_budget_independent(prompt: str, budget: int) -> Dict[str, Any]:
    """
    Independent calculation approach: uses arithmetic bounds min/max
    to verify direct slicing invariants on identical inputs.
    """
    if not isinstance(budget, int) or budget < 0:
        raise TokenBudgetError("INVALID_BUDGET", f"Token budget must be a non-negative integer, got: {budget!r}")

    tokens = tokenize_approx(prompt)
    total = len(tokens)
    retained_count = min(total, budget)
    removed_count = max(0, total - budget)
    retained = [tokens[i] for i in range(retained_count)]

    return {
        "total_tokens": total,
        "budget": budget,
        "retained_tokens": retained,
        "removed_count": removed_count,
        "truncated": removed_count > 0,
        "retained_text": " ".join(retained),
    }


# Canonical entry point
check_token_budget = check_token_budget_direct


def run_concept_example() -> Dict[str, Any]:
    """Runs the canonical fixture and edge cases."""
    canonical_prompt = "one two three four"
    canonical_budget = 3

    # Direct approach
    direct_res = check_token_budget_direct(canonical_prompt, canonical_budget)

    # Independent reference approach
    independent_res = check_token_budget_independent(canonical_prompt, canonical_budget)

    # Empty prompt check
    empty_res = check_token_budget_direct("", canonical_budget)

    # Negative budget check
    negative_rejected = False
    negative_code = None
    try:
        check_token_budget_direct(canonical_prompt, -1)
    except TokenBudgetError as exc:
        negative_rejected = True
        negative_code = exc.code

    return {
        "direct": direct_res,
        "independent": independent_res,
        "approaches_agree": direct_res == independent_res,
        "empty_retained": empty_res["retained_tokens"],
        "empty_removed": empty_res["removed_count"],
        "negative_rejected": negative_rejected,
        "negative_code": negative_code,
    }


if __name__ == "__main__":
    result = run_concept_example()
    print("=== Token-Budget Preflight Example ===")
    print(f"Direct result: retained={result['direct']['retained_tokens']}, removed={result['direct']['removed_count']}")
    print(f"Independent result: retained={result['independent']['retained_tokens']}, removed={result['independent']['removed_count']}")
    print(f"Both approaches agree: {result['approaches_agree']}")
    print(f"Empty prompt result: retained={result['empty_retained']}, removed={result['empty_removed']}")
    print(f"Negative budget rejected: {result['negative_rejected']} (code: {result['negative_code']})")
    print("\n[NOTE] Tokenizer is a whitespace teaching approximation, not production model tokenizer.")
