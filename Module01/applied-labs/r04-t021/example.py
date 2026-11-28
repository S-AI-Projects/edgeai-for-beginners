"""
Token-Budget Preflight Example (Teaching Approximation)

NOTE: This module uses simple whitespace splitting (.split()) as a deterministic
teaching approximation to demonstrate preflight budget checks on resource-constrained
edge devices. It is NOT a real model tokenizer (such as BPE or WordPiece).
"""


def check_token_budget(prompt: str, budget: int) -> dict:
    """
    Check a prompt against a configured whitespace-token budget.

    Args:
        prompt: Input text string to evaluate.
        budget: Maximum allowed number of whitespace tokens (must be >= 0).

    Returns:
        A dictionary reporting:
            - retained_tokens: list of tokens kept within the budget
            - retained_count: number of kept tokens
            - removed_count: number of tokens truncated due to budget limit
            - truncated: boolean indicating whether any tokens were removed
            - tokenizer_note: explicit label noting this is a teaching approximation

    Raises:
        ValueError: If budget is negative.
    """
    if budget < 0:
        raise ValueError("Budget must be non-negative (>= 0).")

    # Teaching approximation: split by whitespace rather than using a model tokenizer
    tokens = prompt.split()
    retained_tokens = tokens[:budget]
    removed_count = max(0, len(tokens) - budget)

    return {
        "retained_tokens": retained_tokens,
        "retained_count": len(retained_tokens),
        "removed_count": removed_count,
        "truncated": removed_count > 0,
        "tokenizer_note": "Teaching approximation (whitespace split), not a real model tokenizer.",
    }


if __name__ == "__main__":
    sample_prompt = "one two three four"
    sample_budget = 3
    result = check_token_budget(sample_prompt, sample_budget)
    print(f"Prompt: {sample_prompt!r} | Budget: {sample_budget}")
    print("Preflight Result:", result)
