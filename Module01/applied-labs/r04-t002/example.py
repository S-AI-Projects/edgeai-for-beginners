#!/usr/bin/env python3
"""
Token Budget Preflight - Boundary-Case Lesson Extension (R04-T002)
Module 01: EdgeAI Fundamentals

Concept:
Edge AI systems operate under strict compute and memory budgets. Token budget
preflight checks prevent unmanaged prompt expansions from overflowing on-device
buffers. This lab emphasizes the smallest valid, boundary, and invalid cases
in token accounting to clarify exact boundary decisions.

Notice:
This tokenizer uses deterministic whitespace splitting as a teaching approximation,
not the production subword tokenizer (e.g. SentencePiece or Byte-Pair Encoding).
"""

from typing import List, Dict, Any


class TokenBudgetPreflight:
    """
    Evaluates prompt lengths against a configured token budget, categorizing
    and enforcing exact boundary decisions.
    """

    def __init__(self, budget: int):
        if budget < 0:
            raise ValueError(f"Token budget cannot be negative: {budget}")
        self.budget = budget
        self.tokenizer_type = "teaching_approximation_whitespace"

    def tokenize(self, text: str) -> List[str]:
        """
        Deterministic whitespace tokenizer for teaching purposes.
        """
        if text is None:
            raise TypeError("Prompt must be a string, got None")
        cleaned = text.strip()
        if not cleaned:
            return []
        return cleaned.split()

    def check(self, prompt: str) -> Dict[str, Any]:
        """
        Evaluates prompt against token budget and provides detailed boundary decision analysis.
        """
        tokens = self.tokenize(prompt)
        total_count = len(tokens)

        # Boundary categorization
        if total_count == 0:
            boundary_decision = "EMPTY_INPUT: Smallest valid input, 0 tokens consumed."
            retained = []
            removed = []
        elif total_count < self.budget:
            boundary_decision = f"UNDER_BUDGET: {total_count}/{self.budget} tokens used."
            retained = list(tokens)
            removed = []
        elif total_count == self.budget:
            boundary_decision = f"EXACT_CAPACITY: {total_count}/{self.budget} tokens used (exact boundary match)."
            retained = list(tokens)
            removed = []
        else:
            overflow = total_count - self.budget
            boundary_decision = f"OVER_BUDGET: Truncating {overflow} excess token(s) to fit budget of {self.budget}."
            retained = tokens[:self.budget]
            removed = tokens[self.budget:]

        return {
            "prompt": prompt,
            "budget": self.budget,
            "total_tokens": tokens,
            "total_token_count": total_count,
            "retained_tokens": retained,
            "retained_count": len(retained),
            "removed_tokens": removed,
            "removed_count": len(removed),
            "truncated": len(removed) > 0,
            "boundary_decision": boundary_decision,
            "tokenizer_note": "Teaching approximation (whitespace tokenization), not model's production BPE tokenizer",
        }


def run_demo() -> None:
    print("=== Module 01: Token Budget Preflight Boundary Extension ===")
    checker = TokenBudgetPreflight(budget=3)

    scenarios = [
        ("Smallest valid (empty)", ""),
        ("Smallest valid (single token)", "word"),
        ("Exact boundary match", "one two three"),
        ("Boundary overflow (+1 token)", "one two three four"),
    ]

    for label, prompt in scenarios:
        res = checker.check(prompt)
        print(f"\nScenario: {label}")
        print(f"Prompt: {prompt!r}")
        print(f"Retained: {res['retained_tokens']} (count: {res['retained_count']})")
        print(f"Removed: {res['removed_tokens']} (count: {res['removed_count']})")
        print(f"Decision: {res['boundary_decision']}")


if __name__ == "__main__":
    run_demo()
