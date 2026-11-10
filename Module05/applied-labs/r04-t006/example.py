#!/usr/bin/env python3
"""
Token Budget Preflight - Refactor the Teaching Example (R04-T006)
Module 05: Introduction to SLMOps

Concept:
In SLMOps, prompt engineering and input governance require modular,
maintainable preflight validation services. Monolithic checkers couple tokenization,
budget comparison, and truncation policy into single blocks.

Focus:
Implements a baseline monolithic implementation, extracts the single named
responsibility 'TruncationPolicy', and proves strict before/after behavioral
equivalence across all inputs.

Notice:
Uses deterministic whitespace tokenization as a teaching approximation,
not the production subword/BPE tokenizer.
"""

from typing import List, Dict, Any, Tuple


class BaselineTokenBudgetPreflight:
    """
    Monolithic baseline implementation where tokenization, budget evaluation,
    and truncation logic are intertwined in a single method.
    """

    def __init__(self, budget: int):
        if budget < 0:
            raise ValueError(f"Token budget cannot be negative: {budget}")
        self.budget = budget
        self.tokenizer_type = "teaching_approximation_whitespace"

    def check(self, prompt: str) -> Dict[str, Any]:
        cleaned = prompt.strip()
        tokens = cleaned.split() if cleaned else []
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


class TruncationPolicy:
    """
    Extracted named responsibility: Encapsulates pure token partitioning logic
    given an input sequence and a non-negative budget limit.
    """

    @staticmethod
    def partition(tokens: List[str], budget: int) -> Tuple[List[str], List[str]]:
        """
        Splits a token list into retained tokens (up to budget) and removed tokens.
        """
        if len(tokens) <= budget:
            return list(tokens), []
        return tokens[:budget], tokens[budget:]


class RefactoredTokenBudgetPreflight:
    """
    Refactored preflight checker delegating truncation decisions to the
    extracted TruncationPolicy component.
    """

    def __init__(self, budget: int, policy: TruncationPolicy = TruncationPolicy()):
        if budget < 0:
            raise ValueError(f"Token budget cannot be negative: {budget}")
        self.budget = budget
        self.policy = policy
        self.tokenizer_type = "teaching_approximation_whitespace"

    def tokenize(self, text: str) -> List[str]:
        cleaned = text.strip()
        return cleaned.split() if cleaned else []

    def check(self, prompt: str) -> Dict[str, Any]:
        tokens = self.tokenize(prompt)
        retained, removed = self.policy.partition(tokens, self.budget)

        return {
            "prompt": prompt,
            "budget": self.budget,
            "total_tokens": tokens,
            "total_token_count": len(tokens),
            "retained_tokens": retained,
            "retained_count": len(retained),
            "removed_tokens": removed,
            "removed_count": len(removed),
            "truncated": len(removed) > 0,
            "tokenizer_note": "Teaching approximation (whitespace tokenization), not model's production BPE tokenizer",
        }


# Canonical alias for client usage
TokenBudgetPreflight = RefactoredTokenBudgetPreflight


def run_demo() -> None:
    print("=== Module 05: SLMOps Token Budget Preflight Refactoring Demo ===")
    prompt = "one two three four"
    budget = 3

    baseline = BaselineTokenBudgetPreflight(budget)
    refactored = RefactoredTokenBudgetPreflight(budget)

    base_res = baseline.check(prompt)
    ref_res = refactored.check(prompt)

    print(f"Prompt: {prompt!r}, Budget: {budget}")
    print(f"Baseline Retained: {base_res['retained_tokens']}, Removed: {base_res['removed_count']}")
    print(f"Refactored Retained: {ref_res['retained_tokens']}, Removed: {ref_res['removed_count']}")
    print(f"Equivalence Confirmed: {base_res == ref_res}")


if __name__ == "__main__":
    run_demo()
