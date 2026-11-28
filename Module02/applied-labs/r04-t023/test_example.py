from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    EXPLICIT_EXPECTED_TABLE,
    FIXTURE_DISCLAIMER,
    SYNTHETIC_MANIFEST,
    compare_selection_approaches,
    independent_eligible_calculation,
    select_eligible_models,
)


class TestGemmaManifestSelectionComparison(unittest.TestCase):
    def test_primary_fixture_admits_only_model_a(self):
        """Budget RAM 6 and requested context 1024 admits only Model-A and reports why Model-B fails."""
        result = select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=6, requested_context=1024)
        self.assertEqual(result["eligible"], ["Model-A"])
        self.assertIn("Model-B", result["excluded"])
        self.assertTrue(
            any("ram_exceeds_budget" in reason for reason in result["excluded"]["Model-B"])
        )
        self.assertEqual(result["fixture_note"], FIXTURE_DISCLAIMER)

    def test_direct_matches_independent_and_expected_table_across_all_rows(self):
        """Direct implementation agrees with independent predicate and expected-result table."""
        for (ram_budget, req_ctx), (exp_eligible, exp_excluded) in EXPLICIT_EXPECTED_TABLE.items():
            comparison = compare_selection_approaches(ram_budget, req_ctx)
            self.assertTrue(comparison["matches_independent"])
            self.assertTrue(comparison["matches_expected_table"])
            self.assertEqual(comparison["direct"]["eligible"], exp_eligible)
            self.assertEqual(comparison["direct"]["excluded"], exp_excluded)

    def test_boundary_exact_ram_and_context_match(self):
        """Exact resource match (RAM=4, context=2048) admits Model-A and excludes Model-B."""
        direct = select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=4, requested_context=2048)
        indep_eligible, indep_excluded = independent_eligible_calculation(
            SYNTHETIC_MANIFEST, ram_budget_gb=4, requested_context=2048
        )
        self.assertEqual(direct["eligible"], ["Model-A"])
        self.assertEqual(direct["eligible"], indep_eligible)
        self.assertEqual(direct["excluded"], indep_excluded)

    def test_context_and_ram_combined_failure_reasons(self):
        """When RAM and context both fail, both failure reasons are reported."""
        result = select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=2, requested_context=8192)
        self.assertEqual(result["eligible"], [])
        self.assertEqual(len(result["excluded"]["Model-A"]), 2)
        self.assertEqual(len(result["excluded"]["Model-B"]), 2)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=0, requested_context=1024)
        with self.assertRaises(ValueError):
            select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb=6, requested_context=-1)
        with self.assertRaises(ValueError):
            select_eligible_models([{"name": "Broken"}], ram_budget_gb=6, requested_context=1024)


if __name__ == "__main__":
    unittest.main()
