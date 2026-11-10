"""
Unit Tests for SLMOps Token Budget Preflight Refactoring (R04-T006)
Module 05: Introduction to SLMOps
"""

import unittest

try:
    from .example import (
        BaselineTokenBudgetPreflight,
        RefactoredTokenBudgetPreflight,
        TruncationPolicy,
    )
except ImportError:
    from example import (
        BaselineTokenBudgetPreflight,
        RefactoredTokenBudgetPreflight,
        TruncationPolicy,
    )


class TestRefactoredTokenBudgetPreflight(unittest.TestCase):
    def setUp(self):
        self.budget = 3
        self.baseline = BaselineTokenBudgetPreflight(self.budget)
        self.refactored = RefactoredTokenBudgetPreflight(self.budget)

    def test_acceptance_criteria_overflow(self):
        """Budget 3 with 'one two three four' retains [one,two,three] and reports 1 removed token."""
        for model in (self.baseline, self.refactored):
            res = model.check("one two three four")
            self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
            self.assertEqual(res["retained_count"], 3)
            self.assertEqual(res["removed_tokens"], ["four"])
            self.assertEqual(res["removed_count"], 1)
            self.assertTrue(res["truncated"])

    def test_acceptance_criteria_empty_input(self):
        """Empty input retains none and reports 0 removed tokens."""
        for model in (self.baseline, self.refactored):
            res = model.check("")
            self.assertEqual(res["retained_tokens"], [])
            self.assertEqual(res["retained_count"], 0)
            self.assertEqual(res["removed_tokens"], [])
            self.assertEqual(res["removed_count"], 0)
            self.assertFalse(res["truncated"])

    def test_acceptance_criteria_negative_budget(self):
        """Negative budget is rejected by both implementations."""
        with self.assertRaises(ValueError):
            BaselineTokenBudgetPreflight(-1)
        with self.assertRaises(ValueError):
            RefactoredTokenBudgetPreflight(-1)

    def test_before_and_after_refactoring_equivalence(self):
        """Prove before/after equivalence between baseline and refactored versions across diverse fixtures."""
        test_fixtures = [
            "",
            "   ",
            "one",
            "one two",
            "one two three",
            "one two three four",
            "alpha beta gamma delta epsilon",
            "a b c d e f g",
        ]

        for budget_val in [0, 1, 3, 5, 10]:
            base_checker = BaselineTokenBudgetPreflight(budget_val)
            ref_checker = RefactoredTokenBudgetPreflight(budget_val)
            for text in test_fixtures:
                base_out = base_checker.check(text)
                ref_out = ref_checker.check(text)
                self.assertEqual(
                    base_out,
                    ref_out,
                    f"Mismatch between baseline and refactored on input '{text}' with budget {budget_val}",
                )

    def test_extracted_truncation_policy_responsibility(self):
        """Verify the extracted TruncationPolicy class directly."""
        tokens = ["a", "b", "c", "d"]
        retained, removed = TruncationPolicy.partition(tokens, budget=2)
        self.assertEqual(retained, ["a", "b"])
        self.assertEqual(removed, ["c", "d"])

    def test_tokenizer_approximation_label_present(self):
        """Outputs identify whitespace tokenization as a teaching approximation."""
        res = self.refactored.check("test prompt")
        self.assertIn("teaching approximation", res["tokenizer_note"].lower())


if __name__ == "__main__":
    unittest.main()
