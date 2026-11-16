#!/usr/bin/env python3
"""
Unit tests for Qualcomm QNN Platform-Compatibility Preflight (R04-T055)
Module 04: Qualcomm QNN Optimization Suite (07.QualcommQNN.md)
"""

import unittest
from example import (
    QNN_LESSON_REQUIREMENTS,
    BaselineQNNPlatformChecker,
    PlatformRuleValidator,
    RefactoredQNNPlatformChecker,
    explain_mapping,
    prove_equivalence,
)


class TestQNNPlatformChecker(unittest.TestCase):
    """Test suite verifying contract compliance and refactoring equivalence for QNN preflight check."""

    def setUp(self) -> None:
        """Initialize fixtures and checkers."""
        self.matching_fixture = {
            "os": "Linux",
            "architecture": "aarch64",
            "backend": "htp",
            "capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
        }
        self.changed_arch_fixture = {
            "os": "Linux",
            "architecture": "x86_64",
            "backend": "htp",
            "capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
        }
        self.missing_caps_fixture = {
            "os": "Linux",
            "architecture": "aarch64",
            "backend": "htp",
            "capabilities": ["QNN_SDK"],
        }
        self.baseline = BaselineQNNPlatformChecker()
        self.refactored = RefactoredQNNPlatformChecker()
        self.validator = PlatformRuleValidator()

    # -----------------------------------------------------------------
    # Primary Contract Requirements
    # -----------------------------------------------------------------
    def test_matching_fixture_passes(self) -> None:
        """A fixture matching required OS/architecture/backend passes without error."""
        result = self.refactored.check(self.matching_fixture)
        self.assertTrue(result["compatible"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["missing_capabilities"], [])
        self.assertEqual(result["lesson_source"], "Module04/07.QualcommQNN.md")

    def test_changed_architecture_fails_with_mismatched_field(self) -> None:
        """A changed architecture fails reporting the exact mismatched field."""
        result = self.refactored.check(self.changed_arch_fixture)
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(len(result["mismatches"]), 1)

        mismatch = result["mismatches"][0]
        self.assertEqual(mismatch["field"], "architecture")
        self.assertEqual(mismatch["expected"], "aarch64")
        self.assertEqual(mismatch["actual"], "x86_64")

    def test_missing_capability_reported_rather_than_guessed(self) -> None:
        """A missing capability is reported explicitly rather than guessed."""
        result = self.refactored.check(self.missing_caps_fixture)
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(sorted(result["missing_capabilities"]), ["HTP_Backend", "Hexagon_NPU"])
        self.assertEqual(result["mismatches"], [])

    def test_exact_lesson_requirement_recorded(self) -> None:
        """The preflight check records the exact lesson requirement used."""
        result = self.refactored.check(self.matching_fixture)
        reqs = result["requirements"]
        self.assertEqual(reqs["lesson_source"], "Module04/07.QualcommQNN.md")
        self.assertEqual(reqs["required_os"], "Linux")
        self.assertEqual(reqs["required_architecture"], "aarch64")
        self.assertEqual(reqs["required_backend"], "htp")
        self.assertIn("Hexagon_NPU", reqs["required_capabilities"])

    # -----------------------------------------------------------------
    # Focus: Refactoring Equivalence Proof
    # -----------------------------------------------------------------
    def test_before_after_refactoring_equivalence(self) -> None:
        """Prove that Baseline and Refactored implementations produce identical outputs."""
        fixtures = [
            self.matching_fixture,
            self.changed_arch_fixture,
            self.missing_caps_fixture,
            {"os": "Windows", "architecture": "arm64", "backend": "cpu", "capabilities": []},
            {},
        ]
        proof = prove_equivalence(fixtures)
        self.assertTrue(proof["all_equivalent"])
        for res in proof["results"]:
            self.assertTrue(res["matches"])

    # -----------------------------------------------------------------
    # Extracted Responsibility Unit Testing
    # -----------------------------------------------------------------
    def test_platform_rule_validator_attributes(self) -> None:
        """PlatformRuleValidator directly validates OS, architecture, and backend."""
        mismatches = self.validator.validate_attributes(
            QNN_LESSON_REQUIREMENTS,
            {"os": "Darwin", "architecture": "arm64", "backend": "gpu"},
        )
        mismatched_fields = [m["field"] for m in mismatches]
        self.assertIn("os", mismatched_fields)
        self.assertIn("architecture", mismatched_fields)
        self.assertIn("backend", mismatched_fields)

    def test_platform_rule_validator_capabilities(self) -> None:
        """PlatformRuleValidator identifies exact missing capabilities."""
        missing = self.validator.validate_capabilities(
            ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
            ["Hexagon_NPU"],
        )
        self.assertEqual(sorted(missing), ["HTP_Backend", "QNN_SDK"])

    # -----------------------------------------------------------------
    # Error Handling and Boundaries
    # -----------------------------------------------------------------
    def test_non_dictionary_probe_raises_value_error(self) -> None:
        """Passing non-dictionary probe data raises ValueError."""
        with self.assertRaises(ValueError):
            self.refactored.check("invalid_probe_string")  # type: ignore

    def test_empty_dictionary_probe_fails_gracefully(self) -> None:
        """An empty probe data dictionary reports all missing fields and capabilities."""
        result = self.refactored.check({})
        self.assertFalse(result["compatible"])
        self.assertEqual(len(result["mismatches"]), 3)
        self.assertEqual(len(result["missing_capabilities"]), 3)

    # -----------------------------------------------------------------
    # Unestablished Behaviors & Concept Mapping
    # -----------------------------------------------------------------
    def test_unestablished_behaviors_documented(self) -> None:
        """Unestablished real-service behaviors are documented."""
        behaviors = RefactoredQNNPlatformChecker.identify_unestablished_behaviors()
        self.assertGreaterEqual(len(behaviors), 4)
        self.assertTrue(any("Hexagon NPU" in b for b in behaviors))

    def test_concept_mapping_coverage(self) -> None:
        """Concept mapping covers all primary lesson fields."""
        mapping = explain_mapping()
        for key in ["required_os", "required_architecture", "required_backend", "required_capabilities", "extracted_responsibility"]:
            self.assertIn(key, mapping)


if __name__ == "__main__":
    unittest.main()
