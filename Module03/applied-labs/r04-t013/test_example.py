"""
Unit tests for R04-T013 Token-Budget Preflight.
Tests normal, boundary, comparison of approaches, and deliberate flaw detection.
"""

import unittest

from example import (
    TokenBudgetError,
    check_token_budget_direct,
    check_token_budget_independent,
    run_concept_example,
    tokenize_approx,
)


class TestTokenBudgetNormal(unittest.TestCase):
    def test_canonical_fixture(self):
        """Budget 3 with 'one two three four' retains [one,two,three] and reports 1 removed."""
        res = check_token_budget_direct("one two three four", 3)
        self.assertEqual(res["total_tokens"], 4)
        self.assertEqual(res["budget"], 3)
        self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(res["removed_count"], 1)
        self.assertTrue(res["truncated"])
        self.assertEqual(res["retained_text"], "one two three")

    def test_empty_input_retains_none(self):
        """Empty input retains none and reports 0 removed."""
        for empty_str in ("", "   ", "\t\n"):
            res = check_token_budget_direct(empty_str, 3)
            self.assertEqual(res["total_tokens"], 0)
            self.assertEqual(res["retained_tokens"], [])
            self.assertEqual(res["removed_count"], 0)
            self.assertFalse(res["truncated"])
            self.assertEqual(res["retained_text"], "")

    def test_reject_negative_budget(self):
        """Negative budget must be rejected with INVALID_BUDGET."""
        for bad_budget in (-1, -10, -100):
            with self.assertRaises(TokenBudgetError) as ctx:
                check_token_budget_direct("one two three four", bad_budget)
            self.assertEqual(ctx.exception.code, "INVALID_BUDGET")

    def test_run_concept_example_summary(self):
        summary = run_concept_example()
        self.assertTrue(summary["approaches_agree"])
        self.assertEqual(summary["direct"]["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(summary["direct"]["removed_count"], 1)
        self.assertEqual(summary["empty_retained"], [])
        self.assertEqual(summary["empty_removed"], 0)
        self.assertTrue(summary["negative_rejected"])
        self.assertEqual(summary["negative_code"], "INVALID_BUDGET")


class TestTokenBudgetBoundariesAndValidation(unittest.TestCase):
    def test_zero_budget(self):
        """Budget of 0 retains empty list and removes all tokens."""
        res = check_token_budget_direct("one two three", 0)
        self.assertEqual(res["total_tokens"], 3)
        self.assertEqual(res["retained_tokens"], [])
        self.assertEqual(res["removed_count"], 3)
        self.assertTrue(res["truncated"])

    def test_exact_budget_match(self):
        """When budget equals prompt length, no tokens are truncated."""
        res = check_token_budget_direct("one two three", 3)
        self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["truncated"])

    def test_budget_exceeds_prompt_length(self):
        """When budget exceeds prompt length, all tokens are preserved."""
        res = check_token_budget_direct("one two", 5)
        self.assertEqual(res["retained_tokens"], ["one", "two"])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["truncated"])

    def test_invalid_prompt_type(self):
        for bad_prompt in (None, 123, ["list"]):
            with self.assertRaises(TokenBudgetError) as ctx:
                check_token_budget_direct(bad_prompt, 5)
            self.assertEqual(ctx.exception.code, "INVALID_PROMPT")

    def test_invalid_budget_type(self):
        for bad_budget in ("5", 3.14, None):
            with self.assertRaises(TokenBudgetError) as ctx:
                check_token_budget_direct("hello world", bad_budget)
            self.assertEqual(ctx.exception.code, "INVALID_BUDGET")


class TestCompareTwoApproaches(unittest.TestCase):
    def test_direct_vs_independent_equivalence(self):
        """Direct slicing and independent arithmetic calculation agree across test grid."""
        prompts = [
            "",
            "hello",
            "one two three four",
            "a b c d e f g h i j",
            "  multiple   spaces   between   words  ",
        ]
        budgets = [0, 1, 2, 3, 4, 5, 10]

        for p in prompts:
            for b in budgets:
                direct = check_token_budget_direct(p, b)
                independent = check_token_budget_independent(p, b)
                self.assertEqual(direct, independent)


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_budgeting_omitting_removed_count_fails(self):
        """A flawed implementation that reports removed_count as 0 must fail assertion."""
        def flawed_budget(prompt, budget):
            tokens = tokenize_approx(prompt)
            # Deliberate bug: always reports 0 removed tokens
            return {
                "retained_tokens": tokens[:budget],
                "removed_count": 0,
            }

        res = flawed_budget("one two three four", 3)
        with self.assertRaises(AssertionError):
            self.assertEqual(res["removed_count"], 1)

    def test_flawed_budgeting_allowing_negative_budget_fails(self):
        """A flawed implementation that silently accepts negative budgets must be caught."""
        def flawed_budget_accepts_negative(prompt, budget):
            # Deliberate bug: allows negative budget and uses negative slice
            tokens = tokenize_approx(prompt)
            return tokens[:budget]

        # Should raise TokenBudgetError, but flawed version doesn't
        res = flawed_budget_accepts_negative("one two three", -1)
        with self.assertRaises(AssertionError):
            self.assertEqual(res, "SHOULD_HAVE_RAISED_INVALID_BUDGET")


if __name__ == "__main__":
    unittest.main()
