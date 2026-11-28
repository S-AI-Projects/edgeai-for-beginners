from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import TOKENIZER_NOTE, check_token_budget


class TestSLMOpsTokenBudgetBoundaries(unittest.TestCase):
    def test_smallest_valid_empty_prompt_zero_budget(self):
        result = check_token_budget("", budget=0)
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["retained_count"], 0)
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])
        self.assertEqual(result["boundary_case"], "smallest_valid_empty")
        self.assertEqual(result["tokenizer_note"], TOKENIZER_NOTE)

    def test_smallest_valid_single_token(self):
        result = check_token_budget("edge", budget=1)
        self.assertEqual(result["retained_tokens"], ["edge"])
        self.assertEqual(result["retained_count"], 1)
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])
        self.assertEqual(result["boundary_case"], "exact_budget_boundary")

    def test_exact_boundary_keeps_all_tokens(self):
        result = check_token_budget("one two three", budget=3)
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])
        self.assertEqual(result["boundary_case"], "exact_budget_boundary")

    def test_over_budget_by_one_truncates_fourth_token(self):
        result = check_token_budget("one two three four", budget=3)
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["retained_count"], 3)
        self.assertEqual(result["removed_count"], 1)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["boundary_case"], "over_budget_truncated")
        self.assertIn("teaching approximation", result["tokenizer_note"].lower())

    def test_zero_budget_with_non_empty_prompt_drops_all(self):
        result = check_token_budget("one", budget=0)
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["removed_count"], 1)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["boundary_case"], "zero_budget_boundary")

    def test_whitespace_only_input_retains_none(self):
        result = check_token_budget("   \n\t ", budget=3)
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_invalid_negative_budget_rejected(self):
        with self.assertRaises(ValueError):
            check_token_budget("one two", budget=-1)

    def test_invalid_types_rejected(self):
        with self.assertRaises(TypeError):
            check_token_budget("one two", budget=True)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            check_token_budget(123, budget=2)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
