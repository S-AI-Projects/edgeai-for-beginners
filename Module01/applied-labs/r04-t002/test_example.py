"""
Unit Tests for Token Budget Preflight Boundary Extension (R04-T002)
Module 01: EdgeAI Fundamentals
"""

import unittest

try:
    from .example import TokenBudgetPreflight
except ImportError:
    from example import TokenBudgetPreflight


class TestTokenBudgetPreflightBoundary(unittest.TestCase):
    def setUp(self):
        self.checker = TokenBudgetPreflight(budget=3)

    def test_acceptance_criteria_overflow(self):
        """Budget 3 with 'one two three four' retains [one,two,three] and reports one removed token."""
        res = self.checker.check("one two three four")
        self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(res["retained_count"], 3)
        self.assertEqual(res["removed_tokens"], ["four"])
        self.assertEqual(res["removed_count"], 1)
        self.assertTrue(res["truncated"])
        self.assertIn("OVER_BUDGET", res["boundary_decision"])

    def test_acceptance_criteria_empty_input(self):
        """Empty input retains none."""
        res = self.checker.check("")
        self.assertEqual(res["retained_tokens"], [])
        self.assertEqual(res["retained_count"], 0)
        self.assertEqual(res["removed_tokens"], [])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["truncated"])
        self.assertIn("EMPTY_INPUT", res["boundary_decision"])

    def test_acceptance_criteria_negative_budget(self):
        """Reject a negative budget."""
        with self.assertRaises(ValueError):
            TokenBudgetPreflight(budget=-1)

    def test_smallest_valid_single_token(self):
        """Smallest valid non-empty input is safely retained."""
        res = self.checker.check("alpha")
        self.assertEqual(res["retained_tokens"], ["alpha"])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["truncated"])
        self.assertIn("UNDER_BUDGET", res["boundary_decision"])

    def test_exact_boundary_limit(self):
        """Total tokens exactly equal to budget should not truncate."""
        res = self.checker.check("one two three")
        self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["truncated"])
        self.assertIn("EXACT_CAPACITY", res["boundary_decision"])

    def test_zero_budget_boundary(self):
        """Budget of 0 removes all tokens for any non-empty input."""
        zero_checker = TokenBudgetPreflight(budget=0)
        res = zero_checker.check("item")
        self.assertEqual(res["retained_tokens"], [])
        self.assertEqual(res["removed_tokens"], ["item"])
        self.assertEqual(res["removed_count"], 1)
        self.assertTrue(res["truncated"])

    def test_invalid_none_input(self):
        """None input raises TypeError."""
        with self.assertRaises(TypeError):
            self.checker.check(None)

    def test_tokenizer_teaching_approximation_label(self):
        """Tokenizer note clarifies this is a teaching approximation."""
        res = self.checker.check("hello world")
        self.assertIn("teaching approximation", res["tokenizer_note"].lower())


if __name__ == "__main__":
    unittest.main()
