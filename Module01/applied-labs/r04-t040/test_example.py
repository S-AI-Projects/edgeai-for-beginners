"""
Unit tests for Token-Budget Preflight Comparison.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import TokenBudgetPreflight, independent_oracle_check, run_demo


class TestTokenBudgetPreflight(unittest.TestCase):

    def test_budget_3_with_four_tokens(self):
        """Budget 3 with 'one two three four' retains [one, two, three] and reports 1 removed token."""
        res = TokenBudgetPreflight.apply_budget("one two three four", 3)
        self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(res["removed_count"], 1)
        self.assertEqual(res["total_tokens"], 4)
        self.assertTrue(res["truncated"])

    def test_empty_input_retains_none(self):
        """Empty input retains none."""
        res = TokenBudgetPreflight.apply_budget("", 3)
        self.assertEqual(res["retained_tokens"], [])
        self.assertEqual(res["retained_count"], 0)
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["truncated"])

        res_spaces = TokenBudgetPreflight.apply_budget("   ", 3)
        self.assertEqual(res_spaces["retained_tokens"], [])

    def test_reject_negative_budget(self):
        """Negative budget is rejected with ValueError."""
        with self.assertRaises(ValueError):
            TokenBudgetPreflight.apply_budget("hello world", -1)

    def test_compare_direct_with_independent_oracle(self):
        """Compare direct implementation with independent reference calculation on identical inputs."""
        test_cases = [
            ("one two three four", 3),
            ("one two three four", 4),
            ("one two three four", 10),
            ("", 5),
            ("   leading and trailing spaces   ", 2),
            ("alpha beta gamma", 0),
        ]
        for text, budget in test_cases:
            direct_out = TokenBudgetPreflight.apply_budget(text, budget)
            oracle_out = independent_oracle_check(text, budget)
            self.assertEqual(direct_out, oracle_out)

    def test_deliberate_wrong_result_fails(self):
        """Deliberate wrong assertion fails."""
        res = TokenBudgetPreflight.apply_budget("one two three four", 3)
        self.assertNotEqual(res["retained_tokens"], ["one", "two", "three", "four"])


if __name__ == "__main__":
    unittest.main()
