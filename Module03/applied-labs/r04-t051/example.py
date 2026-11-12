#!/usr/bin/env python3
"""
Token Budget Preflight - Runnable Concept Example (R04-T051)
Module 03: Containerized Cloud Deployment - Production-Scale Solutions

Concept:
In containerized cloud deployments (e.g., vLLM or ONNX Runtime endpoints),
SLM inference instances operate under strict memory limits and sequence bounds
(such as `--max-model-len 4096`). Dispatching prompts that exceed context limits
can trigger silent truncation, degraded reasoning, or container out-of-memory (OOM)
crashes. A preflight token budget check enforces admission control before requests
hit the container service.

Focus:
Implement the minimal complete local example of a deterministic token budget
preflight check and connect each public input/output to the lesson concept.

Pedagogical Notice:
Deterministic whitespace tokenization (str.split) is used as an explicit
teaching approximation to illustrate token counting, boundary conditions,
and preflight telemetry without external model dependencies. Production
deployments must use the model's native subword/BPE tokenizer (e.g. Hugging Face
or vLLM tokenizer).
"""

from typing import Any, Dict, List


class TokenBudgetPreflight:
    """Evaluates prompt lengths against a configured token budget before container dispatch.

    Attributes:
        budget: Maximum number of tokens permitted in the prompt payload.
        tokenizer_type: Identifier indicating the tokenizer implementation.
    """

    def __init__(self, budget: int) -> None:
        """Initialize the preflight checker with a token budget.

        Args:
            budget: Non-negative integer representing maximum allowable tokens.

        Raises:
            ValueError: If budget is negative.
        """
        if budget < 0:
            raise ValueError(f"Token budget cannot be negative: {budget}")
        self.budget = budget
        self.tokenizer_type = "teaching_approximation_whitespace"

    def tokenize(self, text: str) -> List[str]:
        """Split input text into tokens using whitespace splitting (teaching approximation).

        Args:
            text: Raw input string.

        Returns:
            List of string tokens.
        """
        cleaned = text.strip()
        return cleaned.split() if cleaned else []

    def check(self, prompt: str) -> Dict[str, Any]:
        """Inspect prompt against budget and produce a preflight admission report.

        Args:
            prompt: Incoming user prompt string to validate.

        Returns:
            Dictionary containing:
                - prompt: Original input string.
                - budget: Configured token capacity.
                - total_tokens: Extracted token list.
                - total_token_count: Number of extracted tokens.
                - retained_tokens: Tokens admitted within the budget.
                - retained_count: Number of retained tokens.
                - removed_tokens: Tokens truncated to enforce budget limit.
                - removed_count: Number of truncated tokens.
                - truncated: True if any token was removed, False otherwise.
                - tokenizer_note: Clarification that this is a teaching approximation.
        """
        tokens = self.tokenize(prompt)
        total = len(tokens)

        if total <= self.budget:
            retained = list(tokens)
            removed = []
        else:
            retained = tokens[: self.budget]
            removed = tokens[self.budget :]

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
            "tokenizer_note": (
                "Teaching approximation (whitespace tokenization), "
                "not the model's real tokenizer"
            ),
        }


def explain_mapping() -> Dict[str, str]:
    """Map each public input/output field to its containerized cloud deployment concept."""
    return {
        "budget": "Container sequence limit / memory budget (e.g., vLLM --max-model-len)",
        "prompt": "Incoming raw inference query submitted to the container endpoint",
        "total_tokens": "Extracted tokens from incoming query prior to admission",
        "total_token_count": "Total token workload before applying admission limits",
        "retained_tokens": "Admitted token slice passed to the container inference engine",
        "retained_count": "Sequence length sent to model worker context buffer",
        "removed_tokens": "Tokens dropped to prevent container buffer overflow or OOM",
        "removed_count": "Explicit count of discarded tokens for telemetry and auditing",
        "truncated": "Preflight admission status flag (True if payload was pruned)",
        "tokenizer_note": "Pedagogical transparency marking local approximation vs real BPE",
    }


def main() -> None:
    """Run CLI demonstration of token budget preflight checks."""
    print("=" * 70)
    print("Token Budget Preflight - Containerized Deployment Admission Control")
    print("=" * 70)

    checker = TokenBudgetPreflight(budget=3)
    sample_prompt = "one two three four"
    report = checker.check(sample_prompt)

    print(f"\n1. Overflow Scenario:")
    print(f"   Input prompt:     {report['prompt']!r}")
    print(f"   Budget limit:     {report['budget']}")
    print(f"   Total tokens:     {report['total_tokens']} (count: {report['total_token_count']})")
    print(f"   Retained tokens:  {report['retained_tokens']} (count: {report['retained_count']})")
    print(f"   Removed tokens:   {report['removed_tokens']} (count: {report['removed_count']})")
    print(f"   Truncated flag:   {report['truncated']}")
    print(f"   Tokenizer note:   {report['tokenizer_note']}")

    print(f"\n2. Empty Input Scenario:")
    empty_report = checker.check("")
    print(f"   Input prompt:     {empty_report['prompt']!r}")
    print(f"   Retained count:   {empty_report['retained_count']}")
    print(f"   Removed count:    {empty_report['removed_count']}")
    print(f"   Truncated flag:   {empty_report['truncated']}")

    print(f"\n3. Negative Budget Scenario:")
    try:
        TokenBudgetPreflight(budget=-1)
    except ValueError as e:
        print(f"   Rejected negative budget correctly: {e}")

    print("\n" + "=" * 70)
    print("Concept Mapping (Public Fields -> Container Deployment Concepts):")
    print("=" * 70)
    for field, concept in explain_mapping().items():
        print(f" - {field:<18} : {concept}")
    print("=" * 70)


if __name__ == "__main__":
    main()
