"""
Unit tests for Model-Manifest Selection and Invariant State Trace.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import ManifestSelector, run_demo


class TestManifestSelection(unittest.TestCase):

    def setUp(self):
        self.fixtures = [
            {"id": "Fixture-A", "required_ram_gb": 4, "max_context": 2048},
            {"id": "Fixture-B", "required_ram_gb": 8, "max_context": 4096},
        ]
        self.selector = ManifestSelector(self.fixtures)

    def test_ram6_context1024_admits_only_a(self):
        """
        Verify: Budget RAM 6 and requested context 1024 admits only Fixture A.
        Fixture B is excluded due to RAM exceeding 6GB.
        """
        res = self.selector.select(available_ram_gb=6, requested_context=1024)
        eligible_ids = [m["id"] for m in res["eligible"]]
        self.assertEqual(eligible_ids, ["Fixture-A"])

        excluded_ids = [m["model_id"] for m in res["excluded"]]
        self.assertEqual(excluded_ids, ["Fixture-B"])
        self.assertIn("Insufficient RAM", res["excluded"][0]["reasons"][0])

    def test_state_trace_invariants(self):
        """
        Verify the invariant linking intermediate trace records to final output:
        1. Length of trace matches length of input manifest.
        2. A model is eligible iff both eval_ram and eval_context are True.
        3. Excluded list exactly matches trace items with eligible == False.
        """
        res = self.selector.select(available_ram_gb=6, requested_context=1024)
        trace = res["trace"]
        self.assertEqual(len(trace), len(self.fixtures))

        for step in trace:
            invariant_met = step["eligible"] == (step["eval_ram"] and step["eval_context"])
            self.assertTrue(invariant_met)
            if not step["eligible"]:
                self.assertGreater(len(step["reasons"]), 0)

    def test_context_exclusion(self):
        """Test exclusion when RAM is sufficient but context is insufficient."""
        res = self.selector.select(available_ram_gb=10, requested_context=3000)
        # Fixture A has max_context 2048 < 3000 -> Excluded
        # Fixture B has required_ram 8 <= 10 and max_context 4096 >= 3000 -> Eligible
        eligible_ids = [m["id"] for m in res["eligible"]]
        self.assertEqual(eligible_ids, ["Fixture-B"])

        excluded_ids = [m["model_id"] for m in res["excluded"]]
        self.assertEqual(excluded_ids, ["Fixture-A"])
        self.assertIn("Insufficient context", res["excluded"][0]["reasons"][0])

    def test_deliberate_wrong_result_fails(self):
        """Ensure incorrect eligibility assertion fails."""
        res = self.selector.select(available_ram_gb=6, requested_context=1024)
        self.assertNotIn("Fixture-B", [m["id"] for m in res["eligible"]])


if __name__ == "__main__":
    unittest.main()
