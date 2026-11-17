"""
Unit tests and regression verification for Gemma synthetic model manifest selection (R04-T057).

Tests:
1. Exact worked example regression test: Fixture A (RAM 4/context 2048), Fixture B (RAM 8/context 4096);
   budget RAM 6 and requested context 1024 admits ONLY A.
2. Resource capacity variations (both admitted, both excluded).
3. Context constraint filtering (excluding A due to insufficient context).
4. Boundary condition evaluations.
5. Parameter validation (negative/zero RAM budget, invalid context).
6. Worked input-to-output explanation output validation.
7. Unestablished behaviors and lesson concept mapping coverage.
"""

import unittest

from example import (
    FIXTURE_A,
    FIXTURE_B,
    STANDARD_TEACHING_MANIFEST,
    ModelEntry,
    ModelManifestSelector,
    explain_mapping,
    explain_worked_example,
    identify_unestablished_behaviors,
    select_eligible_models,
)


class TestGemmaModelManifestSelection(unittest.TestCase):
    def setUp(self):
        self.selector = ModelManifestSelector()
        self.manifest = STANDARD_TEACHING_MANIFEST

    def test_worked_example_regression(self):
        """
        Regression test for exact contract:
        Fixture A (RAM 4 / context 2048)
        Fixture B (RAM 8 / context 4096)
        Budget RAM 6, requested context 1024 -> Admits only A.
        """
        result = self.selector.select(
            manifest=self.manifest,
            ram_budget_gb=6.0,
            requested_context=1024,
        )

        # Assert only A is admitted
        self.assertEqual(result.admitted_ids, ["fixture-a"])
        self.assertEqual(len(result.admitted_models), 1)
        self.assertEqual(result.admitted_models[0].name, "Synthetic Gemma Teaching Variant A")

        # Assert B is excluded
        self.assertEqual(result.excluded_ids, ["fixture-b"])
        self.assertEqual(len(result.excluded_models), 1)
        exclusion_b = result.excluded_models[0]
        self.assertEqual(exclusion_b.model_id, "fixture-b")

        # Verify exclusion reason explicitly reports RAM mismatch
        reasons_text = " ".join(exclusion_b.reasons)
        self.assertIn("Insufficient RAM", reasons_text)
        self.assertIn("8.0", reasons_text)
        self.assertIn("6.0", reasons_text)

    def test_both_admitted_when_budget_sufficient(self):
        """When RAM budget is 16 GB and requested context is 2048, both A and B are admitted."""
        result = self.selector.select(
            manifest=self.manifest,
            ram_budget_gb=16.0,
            requested_context=2048,
        )
        self.assertEqual(set(result.admitted_ids), {"fixture-a", "fixture-b"})
        self.assertEqual(len(result.excluded_models), 0)

    def test_both_excluded_when_ram_budget_too_low(self):
        """When RAM budget is 2 GB, both A and B fail due to insufficient RAM."""
        result = self.selector.select(
            manifest=self.manifest,
            ram_budget_gb=2.0,
            requested_context=1024,
        )
        self.assertEqual(result.admitted_ids, [])
        self.assertEqual(set(result.excluded_ids), {"fixture-a", "fixture-b"})
        for exc in result.excluded_models:
            self.assertTrue(any("Insufficient RAM" in r for r in exc.reasons))

    def test_context_constraint_excludes_fixture_a(self):
        """When requested context is 4096 and RAM budget is 16 GB, only B is admitted."""
        result = self.selector.select(
            manifest=self.manifest,
            ram_budget_gb=16.0,
            requested_context=4096,
        )
        self.assertEqual(result.admitted_ids, ["fixture-b"])
        self.assertEqual(result.excluded_ids, ["fixture-a"])
        exc_a = result.excluded_models[0]
        self.assertTrue(any("Insufficient context capacity" in r for r in exc_a.reasons))

    def test_simultaneous_ram_and_context_failure(self):
        """A model violating both RAM and context capacity reports both failure reasons."""
        custom_model = ModelEntry(
            model_id="heavy-small-context",
            name="Heavy Small Context Model",
            required_ram_gb=12.0,
            max_context_length=512,
        )
        result = self.selector.select(
            manifest=[custom_model],
            ram_budget_gb=8.0,
            requested_context=2048,
        )
        self.assertEqual(result.admitted_ids, [])
        self.assertEqual(len(result.excluded_models), 1)
        reasons = result.excluded_models[0].reasons
        self.assertEqual(len(reasons), 2)
        self.assertTrue(any("Insufficient RAM" in r for r in reasons))
        self.assertTrue(any("Insufficient context capacity" in r for r in reasons))

    def test_exact_boundary_admission(self):
        """Model with required RAM exactly equal to budget and context equal to request is admitted."""
        result = self.selector.select(
            manifest=self.manifest,
            ram_budget_gb=4.0,  # Exact RAM for A
            requested_context=2048,  # Exact context for A
        )
        self.assertEqual(result.admitted_ids, ["fixture-a"])
        self.assertEqual(result.excluded_ids, ["fixture-b"])

    def test_invalid_arguments_raise_value_errors(self):
        """Non-positive RAM budget or invalid requested context raise ValueError."""
        with self.assertRaises(ValueError):
            self.selector.select(self.manifest, ram_budget_gb=-1.0, requested_context=1024)

        with self.assertRaises(ValueError):
            self.selector.select(self.manifest, ram_budget_gb=0.0, requested_context=1024)

        with self.assertRaises(ValueError):
            self.selector.select(self.manifest, ram_budget_gb=6.0, requested_context=0)

        with self.assertRaises(ValueError):
            self.selector.select(self.manifest, ram_budget_gb=6.0, requested_context=-500)

    def test_dict_format_manifest_items(self):
        """Manifest items provided as raw dictionaries are properly evaluated."""
        raw_manifest = [
            {"model_id": "raw-a", "name": "Raw Model A", "required_ram_gb": 4, "max_context_length": 2048},
            {"model_id": "raw-b", "name": "Raw Model B", "required_ram_gb": 8, "max_context_length": 4096},
        ]
        result = select_eligible_models(raw_manifest, ram_budget_gb=6.0, requested_context=1024)
        self.assertEqual(result.admitted_ids, ["raw-a"])
        self.assertEqual(result.excluded_ids, ["raw-b"])

    def test_worked_explanation_output(self):
        """Verify explain_worked_example output contains all four key explanation sections."""
        text = explain_worked_example()
        self.assertIn("1. INPUT SPECIFICATION", text)
        self.assertIn("2. STEP-BY-STEP EVALUATION", text)
        self.assertIn("3. DETERMINISTIC OUTPUT REPORT", text)
        self.assertIn("4. CONCLUSION & REGRESSION GUARANTEE", text)
        self.assertIn("fixture-a", text)
        self.assertIn("fixture-b", text)

    def test_unestablished_behaviors_documented(self):
        """Verify explicit declarations that synthetic fixtures make no real-hardware claims."""
        unestablished = identify_unestablished_behaviors()
        self.assertGreaterEqual(len(unestablished), 4)
        combined = " ".join(unestablished).lower()
        self.assertIn("swap", combined)
        self.assertIn("gemma 2", combined)
        self.assertIn("vram", combined)

    def test_concept_mapping_integrity(self):
        """Verify conceptual mapping aligns with Module02/03.GemmaFamily.md."""
        mappings = explain_mapping()
        self.assertGreaterEqual(len(mappings), 4)
        for m in mappings:
            self.assertIn("selector_component", m)
            self.assertIn("lesson_concept", m)
            self.assertIn("pedagogical_purpose", m)


if __name__ == "__main__":
    unittest.main()
