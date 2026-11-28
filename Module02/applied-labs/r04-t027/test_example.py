from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    EXPECTED_WORKED_OUTPUT,
    WORKED_MANIFEST,
    run_worked_example,
    select_eligible_models,
)


class TestPhiManifestWorkedExample(unittest.TestCase):
    def test_exact_worked_example_regression(self):
        """Regression test executing the exact published input-to-output worked example."""
        actual = run_worked_example()
        self.assertEqual(actual, EXPECTED_WORKED_OUTPUT)
        self.assertEqual(actual["eligible"], ["Model-A"])
        self.assertIn("Model-B", actual["excluded"])

    def test_exact_boundary_both_admitted(self):
        """Budget RAM 8 and requested context 2048 admits both Model-A and Model-B."""
        result = select_eligible_models(WORKED_MANIFEST, ram_budget_gb=8, requested_context=2048)
        self.assertEqual(result["eligible"], ["Model-A", "Model-B"])
        self.assertEqual(result["excluded"], {})

    def test_context_exclusion_reported(self):
        """Budget RAM 8 with requested context 3072 excludes Model-A for insufficient context."""
        result = select_eligible_models(WORKED_MANIFEST, ram_budget_gb=8, requested_context=3072)
        self.assertEqual(result["eligible"], ["Model-B"])
        self.assertEqual(
            result["excluded"],
            {"Model-A": ["context_below_request (max 2048 < requested 3072)"]},
        )

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            select_eligible_models(WORKED_MANIFEST, ram_budget_gb=-1, requested_context=1024)
        with self.assertRaises(ValueError):
            select_eligible_models(WORKED_MANIFEST, ram_budget_gb=6, requested_context=0)
        with self.assertRaises(ValueError):
            select_eligible_models([{"name": "Incomplete"}], ram_budget_gb=6, requested_context=1024)


if __name__ == "__main__":
    unittest.main()
