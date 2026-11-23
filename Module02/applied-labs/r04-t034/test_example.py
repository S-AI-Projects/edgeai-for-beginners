"""
Unit tests for Offline Service Adapter and Model-Manifest Selection.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import OfflineModelCatalogAdapter, ManifestSelector, run_demo


class TestOfflineServiceAdapter(unittest.TestCase):

    def setUp(self):
        self.fixtures = [
            {"id": "Fixture-A", "required_ram_gb": 4, "max_context": 2048},
            {"id": "Fixture-B", "required_ram_gb": 8, "max_context": 4096},
        ]
        self.adapter = OfflineModelCatalogAdapter(self.fixtures)
        self.selector = ManifestSelector(self.adapter)

    def test_ram6_context1024_admits_only_a(self):
        """Budget RAM 6 and requested context 1024 admits only Fixture A."""
        res = self.selector.select_models(available_ram_gb=6, requested_context=1024)
        eligible_ids = [m["id"] for m in res["eligible"]]
        self.assertEqual(eligible_ids, ["Fixture-A"])

        excluded_ids = [m["model_id"] for m in res["excluded"]]
        self.assertEqual(excluded_ids, ["Fixture-B"])
        self.assertIn("exceeds available", res["excluded"][0]["reasons"][0])

    def test_adapter_protocol_determinism(self):
        """Verify the offline adapter returns deterministic fixtures without mutations."""
        manifest_1 = self.adapter.fetch_manifest()
        manifest_2 = self.adapter.fetch_manifest()
        self.assertEqual(manifest_1, manifest_2)
        self.assertEqual(len(manifest_1), 2)

    def test_boundary_exact_match(self):
        """Verify exact boundary match: RAM 4 and context 2048 admits A."""
        res = self.selector.select_models(available_ram_gb=4, requested_context=2048)
        self.assertEqual([m["id"] for m in res["eligible"]], ["Fixture-A"])

    def test_deliberate_wrong_result_fails(self):
        """Deliberate wrong expectation must fail assertion."""
        res = self.selector.select_models(available_ram_gb=6, requested_context=1024)
        self.assertNotEqual([m["id"] for m in res["eligible"]], ["Fixture-B"])


if __name__ == "__main__":
    unittest.main()
