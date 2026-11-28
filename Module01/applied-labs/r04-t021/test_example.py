from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import check_token_budget


class TestTokenBudgetPreflight(unittest.TestCase):
    def test_truncation_over_budget(self):
        """Budget 3 with 'one two three four' retains 3 tokens and removes 1."""
        result = check_token_budget("one two three four", budget=3)
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["retained_count"], 3)
        self.assertEqual(result["removed_count"], 1)
        self.assertTrue(result["truncated"])
        self.assertIn("teaching approximation", result["tokenizer_note"].lower())

    def test_within_budget_no_truncation(self):
        """Prompt strictly within budget retains all tokens and removes none."""
        result = check_token_budget("edge ai", budget=5)
        self.assertEqual(result["retained_tokens"], ["edge", "ai"])
        self.assertEqual(result["retained_count"], 2)
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_exact_boundary_budget(self):
        """Prompt matching exact budget boundary retains all tokens without truncation."""
        result = check_token_budget("one two three", budget=3)
        self.assertEqual(result["retained_tokens"], ["one", "two", "three"])
        self.assertEqual(result["removed_count"], 0)
        self.assertFalse(result["truncated"])

    def test_empty_input_retains_none(self):
        """Empty or whitespace-only input retains no tokens."""
        for raw in ("", "   \t\n  "):
            result = check_token_budget(raw, budget=3)
            self.assertEqual(result["retained_tokens"], [])
            self.assertEqual(result["retained_count"], 0)
            self.assertEqual(result["removed_count"], 0)
            self.assertFalse(result["truncated"])

    def test_zero_budget_truncates_all(self):
        """Zero budget is valid and truncates all tokens."""
        result = check_token_budget("one two", budget=0)
        self.assertEqual(result["retained_tokens"], [])
        self.assertEqual(result["removed_count"], 2)
        self.assertTrue(result["truncated"])

    def test_negative_budget_rejected(self):
        """Negative budget raises ValueError."""
        with self.assertRaises(ValueError):
            check_token_budget("one two", budget=-1)


if __name__ == "__main__":
    unittest.main()
