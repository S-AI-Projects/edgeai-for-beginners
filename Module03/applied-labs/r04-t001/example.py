#!/usr/bin/env python3
"""
Token Budget Preflight - Runnable Concept Example (R04-T001)
Module 03: SLM Advanced Learning - Foundations and Optimization

Concept:
In edge AI deployments, Small Language Models (SLMs) have strict context
and memory boundaries (e.g. 2048 or 4096 tokens). A preflight check verifies
prompt token usage against a allocated budget before allocating KV cache or
launching local inference, avoiding unexpected runtime out-of-memory or
silent mid-thought truncation.

Note:
This implementation uses deterministic whitespace splitting as a teaching
approximation to illustrate preflight accounting and boundary decisions.
It is NOT the model's production subword tokenizer (e.g. BPE, SentencePiece).
"""

from typing import List, Dict, Any


class TokenBudgetPreflight:
    """
    Evaluates prompt token counts against a configured budget before model invocation.
    """

    def __init__(self, budget: int):
        if budget < 0:
            raise ValueError(f"Token budget cannot be negative: {budget}")
        self.budget = budget
        self.tokenizer_type = "teaching_approximation_whitespace"

    def tokenize(self, text: str) -> List[str]:
        """
        Deterministic whitespace tokenizer used as a teaching approximation.
        Empty or whitespace-only input returns an empty list.
        """
        cleaned = text.strip()
        if not cleaned:
            return []
        return cleaned.split()

    def check(self, prompt: str) -> Dict[str, Any]:
        """
        Executes preflight check of prompt against configured budget.

        Returns a dictionary reporting:
          - prompt: original input string
          - budget: configured token budget limit
          - total_tokens: tokens parsed from input
          - total_token_count: total token count
          - retained_tokens: tokens retained within budget
          - retained_count: count of retained tokens
          - removed_tokens: tokens discarded due to budget overflow
          - removed_count: count of removed tokens
          - truncated: boolean flag indicating if truncation happened
          - tokenizer_note: clarification of teaching approximation
        """
        tokens = self.tokenize(prompt)
        total_count = len(tokens)

        if total_count <= self.budget:
            retained = list(tokens)
            removed = []
        else:
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
            "tokenizer_note": "Teaching approximation (whitespace tokenization), not model's production BPE tokenizer",
        }


def run_demo() -> None:
    print("--- SLM Token Budget Preflight Demonstration ---")
    checker = TokenBudgetPreflight(budget=3)
    
    # Standard prompt with overflow
    prompt = "one two three four"
    result = checker.check(prompt)
    print(f"Prompt: {prompt!r}")
    print(f"Budget: {result['budget']}")
    print(f"Retained Tokens ({result['retained_count']}): {result['retained_tokens']}")
    print(f"Removed Tokens ({result['removed_count']}): {result['removed_tokens']}")
    print(f"Truncated: {result['truncated']}")
    print(f"Tokenizer Note: {result['tokenizer_note']}\n")

    # Empty prompt
    empty_result = checker.check("")
    print(f"Empty prompt retained count: {empty_result['retained_count']}, removed count: {empty_result['removed_count']}")


if __name__ == "__main__":
    run_demo()
