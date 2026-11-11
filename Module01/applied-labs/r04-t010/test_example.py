"""
Unit Tests for Token Budget Scenario Assessment (R04-T010)
Module 01: Real-World Case Studies
"""

import unittest

try:
    from .example import (
        TokenBudgetPreflight,
        evaluate_assessment_question_1,
        evaluate_assessment_question_2,
        evaluate_assessment_question_3,
        SCENARIO_QUESTIONS,
    )
except ImportError:
    from example import (
        TokenBudgetPreflight,
        evaluate_assessment_question_1,
        evaluate_assessment_question_2,
        evaluate_assessment_question_3,
        SCENARIO_QUESTIONS,
    )


class TestTokenBudgetScenarioAssessment(unittest.TestCase):
    def setUp(self):
        self.checker = TokenBudgetPreflight(budget=3)

    def test_acceptance_criteria_budget_overflow(self):
        """Budget 3 with 'one two three four' retains [one,two,three] and reports 1 removed token."""
        res = self.checker.check("one two three four")
        self.assertEqual(res["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(res["retained_count"], 3)
        self.assertEqual(res["removed_tokens"], ["four"])
        self.assertEqual(res["removed_count"], 1)
        self.assertTrue(res["truncated"])

    def test_acceptance_criteria_empty_input(self):
        """Empty input retains none."""
        res = self.checker.check("")
        self.assertEqual(res["retained_tokens"], [])
        self.assertEqual(res["retained_count"], 0)
        self.assertEqual(res["removed_tokens"], [])
        self.assertEqual(res["removed_count"], 0)
        self.assertFalse(res["truncated"])

    def test_acceptance_criteria_negative_budget(self):
        """Reject a negative budget."""
        with self.assertRaises(ValueError):
            TokenBudgetPreflight(budget=-1)

    def test_assessment_question_1_predict_output(self):
        """Question 1 executable check: Predict prompt overflow output."""
        eval_res = evaluate_assessment_question_1()
        self.assertTrue(eval_res["passed"])
        self.assertIn("rationale", eval_res)

    def test_assessment_question_2_diagnose_failure(self):
        """Question 2 executable check: Diagnose negative budget initialization failure."""
        eval_res = evaluate_assessment_question_2()
        self.assertTrue(eval_res["passed"])
        self.assertIn("rationale", eval_res)

    def test_assessment_question_3_boundary_policy(self):
        """Question 3 executable check: Exact capacity boundary policy."""
        eval_res = evaluate_assessment_question_3()
        self.assertTrue(eval_res["passed"])
        self.assertIn("rationale", eval_res)

    def test_tokenizer_approximation_label_present(self):
        """Output explicitly marks tokenizer as a teaching approximation."""
        res = self.checker.check("test prompt")
        self.assertIn("teaching approximation", res["tokenizer_note"].lower())


if __name__ == "__main__":
    unittest.main()
