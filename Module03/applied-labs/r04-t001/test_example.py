"""
Unit Tests for Token Budget Preflight (R04-T001)
Module 03: SLM Advanced Learning
"""

import unittest
try:
    from .example import TokenBudgetPreflight
except ImportError:
    from example import TokenBudgetPreflight


class TestTokenBudgetPreflight(unittest.TestCase):
    def setUp(self):
        self.checker = TokenBudgetPreflight(budget=3)

    def test_budget_overflow_truncation(self):
        """Budget 3 with 'one two three four' retains [one,two,three] and reports 1 removed token."""
        result = self.checker.check("one two three four")
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["retained_count"], 3)
        self.assertEqual(result["removed_tokens"], ["four"])
        self.assertEqual(result["removed_count"], 1)
        self.assertTrue(result["truncated"])

    def test_empty_input_retains_none(self):
        """Empty input retains no tokens and reports 0 removed tokens."""
        result = self.checker.check("")
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["retained_count"], 0)
        self.assertEqual(result["removed_tokens"], [])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_whitespace_only_input(self):
        """Whitespace-only string produces empty token list without error."""
        result = self.checker.check("    \t\n   ")
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["retained_count"], 0)
        self.assertFalse(result["truncated"])

    def test_negative_budget_rejected(self):
        """Negative budget must raise ValueError."""
        with self.assertRaises(ValueError):
            TokenBudgetPreflight(budget=-1)

    def test_exact_budget_match(self):
        """Prompt matching budget exactly is retained with zero removed tokens."""
        result = self.checker.check("apple banana orange")
        self.assertEqual(result["retained_tokens"], ["apple", "banana", "orange"])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_zero_budget(self):
        """Budget of zero retains nothing and removes all tokens."""
        zero_checker = TokenBudgetPreflight(budget=0)
        result = zero_checker.check("first second")
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["retained_count"], 0)
        self.assertEqual(result["removed_tokens"], ["first", "second"])
        self.assertEqual(result["removed_count"], 2)
        self.assertTrue(result["truncated"])

    def test_tokenizer_approximation_label_present(self):
        """Output explicitly identifies tokenizer as a teaching approximation."""
        result = self.checker.check("sample prompt")
        self.assertIn("teaching approximation", result["tokenizer_note"].lower())


if __name__ == "__main__":
    unittest.main()
