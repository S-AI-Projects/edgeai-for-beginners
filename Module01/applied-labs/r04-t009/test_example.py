"""
Unit Tests for Environment Preflight Evaluation Experiment (R04-T009)
Module 01: Practical Implementation Guide
"""

import unittest

try:
    from .example import (
        EnvironmentPreflightChecker,
        run_evaluation_experiment,
        redact_sensitive_value,
    )
except ImportError:
    from example import (
        EnvironmentPreflightChecker,
        run_evaluation_experiment,
        redact_sensitive_value,
    )


class TestEnvironmentPreflightEvaluator(unittest.TestCase):
    def setUp(self):
        self.execs = ["python3", "git"]
        self.config_keys = ["model_dir", "api_key"]
        self.checker = EnvironmentPreflightChecker(self.execs, self.config_keys)

    def test_complete_fixture_passes(self):
        """A complete fixture passes all preflight checks."""
        available = {"python3": True, "git": True}
        cfg = {"model_dir": "/models", "api_key": "secret_abc"}
        res = self.checker.check(available, cfg)

        self.assertTrue(res["passed"])
        self.assertEqual(len(res["all_failures"]), 0)

    def test_missing_executable_gives_actionable_failure(self):
        """Missing executable produces a separate actionable failure message."""
        available = {"python3": True, "git": False}
        cfg = {"model_dir": "/models", "api_key": "secret"}
        res = self.checker.check(available, cfg)

        self.assertFalse(res["passed"])
        self.assertEqual(len(res["executable_failures"]), 1)
        self.assertIn("MISSING_EXECUTABLE: 'git'", res["executable_failures"][0])
        self.assertEqual(len(res["config_failures"]), 0)

    def test_absent_config_gives_actionable_failure(self):
        """Absent config produces a separate actionable failure message."""
        available = {"python3": True, "git": True}
        cfg = {"model_dir": "/models"}  # missing api_key
        res = self.checker.check(available, cfg)

        self.assertFalse(res["passed"])
        self.assertEqual(len(res["config_failures"]), 1)
        self.assertIn("ABSENT_CONFIG: Key 'api_key'", res["config_failures"][0])
        self.assertEqual(len(res["executable_failures"]), 0)

    def test_secret_values_never_printed(self):
        """Secret values are redacted and never printed raw."""
        raw_secret = "super_classified_token_xyz"
        available = {"python3": True, "git": True}
        cfg = {"model_dir": "/models", "api_key": raw_secret}
        res = self.checker.check(available, cfg)

        self.assertNotIn(raw_secret, str(res))
        self.assertEqual(res["sanitized_config"]["api_key"], "[REDACTED]")

    def test_evaluation_experiment_three_tiers(self):
        """Verify experiment runs three tiers and measures correctness and metrics."""
        results = run_evaluation_experiment()
        self.assertIn("tier_minimal", results)
        self.assertIn("tier_standard", results)
        self.assertIn("tier_enterprise", results)

        # Minimal (no missing items) passes
        self.assertTrue(results["tier_minimal"]["passed"])
        # Standard (no missing items) passes
        self.assertTrue(results["tier_standard"]["passed"])
        # Enterprise (docker and telemetry_token missing) isolates exactly 2 failures
        self.assertFalse(results["tier_enterprise"]["passed"])
        self.assertEqual(
            results["tier_enterprise"]["executable_failure_count"], 1
        )
        self.assertEqual(results["tier_enterprise"]["config_failure_count"], 1)

        # Check counts increase monotonically across tiers
        self.assertLess(
            results["tier_minimal"]["checks_count"],
            results["tier_standard"]["checks_count"],
        )
        self.assertLess(
            results["tier_standard"]["checks_count"],
            results["tier_enterprise"]["checks_count"],
        )


if __name__ == "__main__":
    unittest.main()
