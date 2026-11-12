#!/usr/bin/env python3
"""
Unit tests for Token Budget Preflight (R04-T051)
Module 03: Containerized Cloud Deployment - Production-Scale Solutions
"""

import unittest
from example import TokenBudgetPreflight, explain_mapping


class TestTokenBudgetPreflight(unittest.TestCase):
    """Test suite verifying contract compliance of TokenBudgetPreflight."""

    def setUp(self) -> None:
        """Initialize standard fixture with budget of 3 tokens."""
        self.checker = TokenBudgetPreflight(budget=3)

    def test_budget_overflow_truncation(self) -> None:
        """Budget 3 with 'one two three four' retains [one,two,three] and reports 1 removed token."""
        result = self.checker.check("one two three four")
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["retained_count"], 3)
        self.assertEqual(result["removed_tokens"], ["four"])
        self.assertEqual(result["removed_count"], 1)
        self.assertTrue(result["truncated"])

    def test_empty_input_retains_none(self) -> None:
        """Empty input retains no tokens and reports 0 removed tokens."""
        result = self.checker.check("")
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["retained_count"], 0)
        self.assertEqual(result["removed_tokens"], [])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_whitespace_only_input_retains_none(self) -> None:
        """Whitespace-only input yields empty tokens and zero retained/removed."""
        result = self.checker.check("   \t\n  \r ")
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["retained_count"], 0)
        self.assertEqual(result["removed_tokens"], [])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_negative_budget_raises_value_error(self) -> None:
        """Rejecting negative budget with ValueError."""
        with self.assertRaises(ValueError) as ctx:
            TokenBudgetPreflight(budget=-1)
        self.assertIn("cannot be negative", str(ctx.exception))

        with self.assertRaises(ValueError):
            TokenBudgetPreflight(budget=-10)

    def test_exact_budget_match_retains_all(self) -> None:
        """Prompt matching budget exactly is retained with zero removed tokens."""
        result = self.checker.check("vllm phi4 container")
        self.assertEqual(result["retained_tokens"], ["vllm", "phi4", "container"])
        self.assertEqual(result["retained_count"], 3)
        self.assertEqual(result["removed_tokens"], [])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_under_budget_retains_all(self) -> None:
        """Prompt smaller than budget is fully retained without truncation."""
        result = self.checker.check("edge deploy")
        self.assertEqual(result["retained_tokens"], ["edge", "deploy"])
        self.assertEqual(result["retained_count"], 2)
        self.assertEqual(result["removed_tokens"], [])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_zero_budget_boundary(self) -> None:
        """Budget 0 retains no tokens and reports all prompt tokens as removed."""
        zero_checker = TokenBudgetPreflight(budget=0)
        result = zero_checker.check("token1 token2")
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["retained_count"], 0)
        self.assertEqual(result["removed_tokens"], ["token1", "token2"])
        self.assertEqual(result["removed_count"], 2)
        self.assertTrue(result["truncated"])

    def test_tokenizer_approximation_label_present(self) -> None:
        """Report explicitly labels tokenizer as a teaching approximation and not real tokenizer."""
        result = self.checker.check("phi4 reasoning test")
        self.assertIn("teaching approximation", result["tokenizer_note"].lower())
        self.assertIn("not the model's real tokenizer", result["tokenizer_note"].lower())

    def test_concept_mapping_covers_public_fields(self) -> None:
        """Ensure all report fields map to containerized cloud deployment concepts."""
        report = self.checker.check("one two three four")
        mapping = explain_mapping()
        for key in report.keys():
            self.assertIn(key, mapping, f"Missing lesson concept mapping for {key}")


if __name__ == "__main__":
    unittest.main()
