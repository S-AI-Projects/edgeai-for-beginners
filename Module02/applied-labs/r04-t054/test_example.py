#!/usr/bin/env python3
"""
Unit tests for Model-Manifest Selection - Offline Service Adapter (R04-T054)
Module 02: Microsoft Mu Model Fundamentals (05.mumodel.md)
"""

import unittest
from example import (
    DEFAULT_SYNTHETIC_MANIFEST,
    ModelManifestSelector,
    SyntheticManifestAdapter,
    explain_mapping,
)


class TestModelManifestSelection(unittest.TestCase):
    """Test suite verifying contract compliance of ModelManifestSelector and offline adapter."""

    def setUp(self) -> None:
        """Initialize selector with default synthetic adapter."""
        self.adapter = SyntheticManifestAdapter()
        self.selector = ModelManifestSelector(manifest_provider=self.adapter)

    # -----------------------------------------------------------------
    # Primary Contract Requirement
    # -----------------------------------------------------------------
    def test_budget_ram6_context1024_admits_only_fixture_a(self) -> None:
        """Fixture A needs RAM4/context2048, B RAM8/context4096; budget RAM6/context1024 admits only A."""
        result = self.selector.select(available_ram_gb=6.0, requested_context=1024)

        self.assertEqual(result["admitted_ids"], ["fixture-a"])
        self.assertEqual(result["excluded_ids"], ["fixture-b"])
        self.assertEqual(len(result["admitted"]), 1)
        self.assertEqual(len(result["excluded"]), 1)

        # Check Fixture A admitted properties
        admitted_model = result["admitted"][0]
        self.assertEqual(admitted_model["min_ram_gb"], 4)
        self.assertEqual(admitted_model["max_context"], 2048)

        # Check Fixture B exclusion explanation
        excluded_b = result["excluded"][0]
        self.assertEqual(excluded_b["id"], "fixture-b")
        self.assertTrue(any("Insufficient RAM" in r for r in excluded_b["reasons"]))
        self.assertIn("8", str(excluded_b["reasons"]))

        # Check teaching note
        self.assertIn("invented teaching fixtures", result["teaching_note"])

    # -----------------------------------------------------------------
    # Boundary Conditions
    # -----------------------------------------------------------------
    def test_exact_ram_boundary(self) -> None:
        """Budget exactly equal to model requirement (4GB) admits Fixture A."""
        result = self.selector.select(available_ram_gb=4.0, requested_context=1024)
        self.assertIn("fixture-a", result["admitted_ids"])

    def test_exact_context_boundary(self) -> None:
        """Requested context matching model maximum context (2048) admits Fixture A."""
        result = self.selector.select(available_ram_gb=6.0, requested_context=2048)
        self.assertIn("fixture-a", result["admitted_ids"])

    def test_context_overflow_excludes_model(self) -> None:
        """Requested context exceeding model maximum (2049) excludes Fixture A."""
        result = self.selector.select(available_ram_gb=6.0, requested_context=2049)
        self.assertNotIn("fixture-a", result["admitted_ids"])
        self.assertIn("fixture-a", result["excluded_ids"])

        excluded_a = [e for e in result["excluded"] if e["id"] == "fixture-a"][0]
        self.assertTrue(any("Insufficient context capacity" in r for r in excluded_a["reasons"]))

    def test_ample_resources_admits_both(self) -> None:
        """Large RAM budget and small context requirement admits both fixtures."""
        result = self.selector.select(available_ram_gb=16.0, requested_context=512)
        self.assertEqual(sorted(result["admitted_ids"]), ["fixture-a", "fixture-b"])
        self.assertEqual(result["excluded_ids"], [])

    def test_insufficient_resources_excludes_all(self) -> None:
        """RAM budget lower than any model requirement excludes all entries."""
        result = self.selector.select(available_ram_gb=2.0, requested_context=512)
        self.assertEqual(result["admitted_ids"], [])
        self.assertEqual(sorted(result["excluded_ids"]), ["fixture-a", "fixture-b"])

    # -----------------------------------------------------------------
    # Callable Interface and Adapter Decoupling
    # -----------------------------------------------------------------
    def test_adapter_callable_interface(self) -> None:
        """Adapter satisfies callable interface and returns defensive copy."""
        manifest_copy = self.adapter()
        self.assertEqual(len(manifest_copy), 2)

        # Mutate returned copy
        manifest_copy.clear()

        # Internal state of adapter remains unaffected
        fresh_copy = self.adapter()
        self.assertEqual(len(fresh_copy), 2)

    def test_custom_callable_adapter_injection(self) -> None:
        """Selector accepts arbitrary custom callable providing model manifest."""
        custom_fixture = [
            {"id": "custom-1", "name": "Custom", "min_ram_gb": 2, "max_context": 512}
        ]
        custom_selector = ModelManifestSelector(manifest_provider=lambda: custom_fixture)
        result = custom_selector.select(available_ram_gb=3.0, requested_context=256)
        self.assertEqual(result["admitted_ids"], ["custom-1"])

    # -----------------------------------------------------------------
    # Error Handling & Edge Cases
    # -----------------------------------------------------------------
    def test_invalid_parameters_raise_value_error(self) -> None:
        """Nonpositive RAM or context must raise ValueError."""
        with self.assertRaises(ValueError):
            self.selector.select(available_ram_gb=0.0, requested_context=1024)
        with self.assertRaises(ValueError):
            self.selector.select(available_ram_gb=-4.0, requested_context=1024)
        with self.assertRaises(ValueError):
            self.selector.select(available_ram_gb=6.0, requested_context=0)
        with self.assertRaises(ValueError):
            self.selector.select(available_ram_gb=6.0, requested_context=-100)

    def test_malformed_manifest_entry_rejected(self) -> None:
        """Manifest entry missing min_ram_gb or max_context raises ValueError."""
        malformed = [{"id": "bad-entry", "name": "Missing Fields"}]
        selector = ModelManifestSelector(manifest_provider=lambda: malformed)
        with self.assertRaises(ValueError):
            selector.select(available_ram_gb=6.0, requested_context=1024)

    # -----------------------------------------------------------------
    # Unestablished Real-Service Behaviors & Mapping
    # -----------------------------------------------------------------
    def test_unestablished_behaviors_documented(self) -> None:
        """Unestablished behaviors are explicitly enumerated."""
        behaviors = ModelManifestSelector.identify_unestablished_behaviors()
        self.assertGreaterEqual(len(behaviors), 4)
        self.assertTrue(any("Network Transport" in b for b in behaviors))
        self.assertTrue(any("Dynamic Host Telemetry" in b for b in behaviors))

    def test_concept_mapping_coverage(self) -> None:
        """Explain mapping covers core architectural concepts."""
        mapping = explain_mapping()
        for key in ["available_ram_gb", "requested_context", "min_ram_gb", "max_context", "admitted", "excluded"]:
            self.assertIn(key, mapping)


if __name__ == "__main__":
    unittest.main()
