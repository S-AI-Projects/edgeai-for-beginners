"""
Unit tests for Model-Manifest Selection Failure and Recovery.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import ResilientManifestSelector, ManifestValidationError, run_demo


class TestManifestFailureAndRecovery(unittest.TestCase):

    def setUp(self):
        self.selector = ResilientManifestSelector()
        self.valid_manifest = [
            {"id": "Fixture-A", "required_ram_gb": 4, "max_context": 2048},
            {"id": "Fixture-B", "required_ram_gb": 8, "max_context": 4096},
        ]

    def test_canonical_selection(self):
        """Fixture A admitted, Fixture B excluded under RAM 6 / Context 1024."""
        res = self.selector.select(self.valid_manifest, available_ram_gb=6, requested_context=1024)
        self.assertEqual([m["id"] for m in res["eligible"]], ["Fixture-A"])
        self.assertEqual([m["model_id"] for m in res["excluded"]], ["Fixture-B"])
        self.assertEqual(len(res["errors"]), 0)

    def test_missing_data_failure(self):
        """Missing field generates structured error envelope."""
        malformed = [{"id": "Bad-Entry", "required_ram_gb": 4}]
        res = self.selector.select(malformed, available_ram_gb=6, requested_context=1024)
        self.assertEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["error"], "MALFORMED_MANIFEST_ENTRY")
        self.assertIn("Missing required field: 'max_context'", res["errors"][0]["message"])
        self.assertEqual(len(res["eligible"]), 0)

    def test_recovery_on_subsequent_valid_input(self):
        """System recovers completely on subsequent valid input without state poisoning."""
        # 1. Trigger failure
        malformed = [{"id": "Corrupted", "max_context": 1024}]
        fail_res = self.selector.select(malformed, available_ram_gb=6, requested_context=1024)
        self.assertEqual(len(fail_res["errors"]), 1)

        # 2. Subsequent valid invocation succeeds
        recovery_res = self.selector.select(self.valid_manifest, available_ram_gb=6, requested_context=1024)
        self.assertEqual([m["id"] for m in recovery_res["eligible"]], ["Fixture-A"])
        self.assertEqual(len(recovery_res["errors"]), 0)

    def test_deliberate_wrong_result_fails(self):
        """Deliberate wrong assertion fails."""
        res = self.selector.select(self.valid_manifest, available_ram_gb=6, requested_context=1024)
        self.assertNotEqual([m["id"] for m in res["eligible"]], ["Fixture-B"])


if __name__ == "__main__":
    unittest.main()
