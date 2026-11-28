from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    TOKENIZER_NOTE,
    check_token_budget,
    verify_q1_predict_output,
    verify_q2_diagnose_failure,
    verify_q3_boundary_policy,
)


class TestSLMScenarioAssessment(unittest.TestCase):
    def test_q1_predict_output_budget_3_four_tokens(self):
        """Q1 executable check: budget 3 with 'one two three four' retains 3 and removes 1."""
        result = verify_q1_predict_output()
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["retained_count"], 3)
        self.assertEqual(result["removed_count"], 1)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["tokenizer_note"], TOKENIZER_NOTE)

    def test_q2_diagnose_failure_negative_budget(self):
        """Q2 executable check: negative budget fails with ValueError rather than silent slicing."""
        msg = verify_q2_diagnose_failure()
        self.assertIn("ValueError raised as expected", msg)
        with self.assertRaises(ValueError):
            check_token_budget("one two", budget=-1)

    def test_q3_choose_boundary_policy_exact_and_zero(self):
        """Q3 executable check: len==budget keeps all tokens; budget=0 drops all tokens."""
        exact_fit, zero_limit = verify_q3_boundary_policy()
        self.assertEqual(exact_fit["removed_count"], 0)
        self.assertFalse(exact_fit["truncated"])
        self.assertEqual(zero_limit["retained_tokens"], [])
        self.assertEqual(zero_limit["removed_count"], 1)
        self.assertTrue(zero_limit["truncated"])

    def test_empty_input_retains_none(self):
        """Empty and whitespace-only inputs retain zero tokens with no truncation."""
        for text in ("", "   \t\n"):
            result = check_token_budget(text, budget=3)
            self.assertEqual(result["retained_tokens"], [])
            self.assertEqual(result["retained_count"], 0)
            self.assertEqual(result["removed_count"], 0)
            self.assertFalse(result["truncated"])

    def test_invalid_argument_types_rejected(self):
        with self.assertRaises(TypeError):
            check_token_budget("one", budget=True)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            check_token_budget(42, budget=2)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
