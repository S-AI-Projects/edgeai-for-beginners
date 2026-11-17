"""
Unit tests for R04-T016 Apple MLX Platform Preflight.
Tests normal matching fixture, changed architecture, missing fields, before/after equivalence, and deliberate flaw detection.
"""

import unittest
from unittest.mock import patch

from example import (
    MLX_MANIFEST,
    PlatformCheckError,
    check_platform_baseline,
    check_platform_refactored,
    evaluate_field_requirement,
    run_concept_example,
)


class TestPlatformPreflightNormal(unittest.TestCase):
    def setUp(self):
        self.matching_fixture = {
            "os": "Darwin",
            "architecture": "arm64",
            "backend": "metal",
            "ram_gb": 16,
        }

    def test_matching_fixture_passes(self):
        """A fixture matching required OS/architecture/backend passes."""
        res = check_platform_refactored(MLX_MANIFEST, self.matching_fixture)
        self.assertTrue(res["compatible"])
        self.assertEqual(len(res["failed"]), 0)
        self.assertEqual(len(res["missing"]), 0)
        self.assertIn("os", res["passed"])
        self.assertIn("architecture", res["passed"])
        self.assertIn("backend", res["passed"])
        self.assertIn("ram_gb", res["passed"])

    def test_changed_architecture_fails_with_mismatched_field(self):
        """A changed architecture fails with the mismatched field 'architecture'."""
        changed_obs = dict(self.matching_fixture, architecture="x86_64")
        res = check_platform_refactored(MLX_MANIFEST, changed_obs)
        self.assertFalse(res["compatible"])
        self.assertEqual(len(res["failed"]), 1)
        self.assertEqual(res["failed"][0]["field"], "architecture")
        self.assertEqual(res["failed"][0]["observed"], "x86_64")
        self.assertIn("mismatch", res["failed"][0]["reason"].lower())

    def test_missing_capability_is_reported_rather_than_guessed(self):
        """A missing capability (backend omitted) is reported in missing, not guessed."""
        missing_obs = {
            "os": "Darwin",
            "architecture": "arm64",
            "ram_gb": 16,
        }
        res = check_platform_refactored(MLX_MANIFEST, missing_obs)
        self.assertFalse(res["compatible"])
        self.assertEqual(len(res["missing"]), 1)
        self.assertEqual(res["missing"][0]["field"], "backend")
        self.assertIn("cannot be guessed", res["missing"][0]["reason"])

    def test_run_concept_example_summary(self):
        summary = run_concept_example()
        self.assertTrue(summary["matching_compatible"])
        self.assertFalse(summary["mismatch_compatible"])
        self.assertEqual(summary["mismatch_failed_field"], "architecture")
        self.assertFalse(summary["missing_compatible"])
        self.assertEqual(summary["missing_field"], "backend")


class TestBoundaryAndValidation(unittest.TestCase):
    def test_insufficient_ram_fails(self):
        obs = {
            "os": "Darwin",
            "architecture": "arm64",
            "backend": "metal",
            "ram_gb": 4,  # required >= 8
        }
        res = check_platform_refactored(MLX_MANIFEST, obs)
        self.assertFalse(res["compatible"])
        self.assertEqual(res["failed"][0]["field"], "ram_gb")

    def test_exact_minimum_boundary_ram_passes(self):
        obs = {
            "os": "Darwin",
            "architecture": "arm64",
            "backend": "metal",
            "ram_gb": 8,  # exactly boundary
        }
        res = check_platform_refactored(MLX_MANIFEST, obs)
        self.assertTrue(res["compatible"])

    def test_hardware_independence(self):
        """Ensure check does not query host platform or os modules."""
        with patch("platform.system", side_effect=AssertionError("Should not call platform.system")):
            with patch("os.uname", side_effect=AssertionError("Should not call os.uname")):
                obs = {
                    "os": "Darwin",
                    "architecture": "arm64",
                    "backend": "metal",
                    "ram_gb": 8,
                }
                res = check_platform_refactored(MLX_MANIFEST, obs)
                self.assertTrue(res["compatible"])


class TestRefactorEquivalence(unittest.TestCase):
    def test_baseline_and_refactored_equivalence(self):
        """Baseline and refactored checkers yield identical results across test cases."""
        test_observations = [
            {"os": "Darwin", "architecture": "arm64", "backend": "metal", "ram_gb": 16},
            {"os": "Darwin", "architecture": "x86_64", "backend": "metal", "ram_gb": 16},
            {"os": "Linux", "architecture": "arm64", "backend": "metal", "ram_gb": 16},
            {"os": "Darwin", "architecture": "arm64", "backend": "cuda", "ram_gb": 16},
            {"os": "Darwin", "architecture": "arm64", "ram_gb": 16},  # missing backend
            {"os": "Darwin", "architecture": "arm64", "backend": "metal", "ram_gb": 4},
        ]
        for obs in test_observations:
            baseline = check_platform_baseline(MLX_MANIFEST, obs)
            refactored = check_platform_refactored(MLX_MANIFEST, obs)
            self.assertEqual(baseline["compatible"], refactored["compatible"])
            self.assertEqual(baseline["passed"], refactored["passed"])
            self.assertEqual(len(baseline["failed"]), len(refactored["failed"]))
            self.assertEqual(len(baseline["missing"]), len(refactored["missing"]))


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_checker_ignoring_architecture_fails(self):
        """A flawed checker that forgets to check architecture must fail test."""
        def flawed_checker(manifest, obs):
            # Deliberate bug: omits architecture check
            return {"compatible": obs.get("os") == "Darwin"}

        res = flawed_checker(MLX_MANIFEST, {"os": "Darwin", "architecture": "x86_64"})
        # Should be False (incompatible), but flawed returns True
        with self.assertRaises(AssertionError):
            self.assertFalse(res["compatible"])

    def test_flawed_checker_guessing_missing_field_fails(self):
        """A flawed checker that defaults missing backend to 'metal' must be caught."""
        def flawed_checker_defaults(obs):
            # Deliberate bug: guesses missing field
            backend = obs.get("backend", "metal")
            return backend

        guessed = flawed_checker_defaults({"os": "Darwin"})
        # Expecting the checker to report missing, guessing fails verification
        with self.assertRaises(AssertionError):
            self.assertIsNone(guessed)


if __name__ == "__main__":
    unittest.main()
