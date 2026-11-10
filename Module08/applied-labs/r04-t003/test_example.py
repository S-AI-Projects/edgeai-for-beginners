"""
Unit Tests for Foundry Local Preflight (R04-T003)
Module 08: Foundry Local Setup
"""

import unittest

try:
    from .example import (
        InstallationPreflightChecker,
        reference_preflight_evaluator,
        redact_value,
    )
except ImportError:
    from example import (
        InstallationPreflightChecker,
        reference_preflight_evaluator,
        redact_value,
    )


class TestInstallationPreflight(unittest.TestCase):
    def setUp(self):
        self.req_executables = ["foundry", "python3"]
        self.req_config = ["model_dir", "api_key", "endpoint"]
        self.checker = InstallationPreflightChecker(
            self.req_executables, self.req_config
        )

    def test_complete_fixture_passes(self):
        """A complete fixture passes all preflight checks."""
        available_execs = {"foundry": True, "python3": True, "git": True}
        config_data = {
            "model_dir": "/opt/foundry/models",
            "api_key": "sk-super-secret-1234",
            "endpoint": "http://127.0.0.1:5272",
        }

        result = self.checker.run_preflight(available_execs, config_data)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["all_failures"]), 0)

    def test_missing_executable_gives_actionable_failure(self):
        """Missing executable produces specific actionable failure message."""
        available_execs = {"python3": True}  # 'foundry' is missing
        config_data = {
            "model_dir": "/opt/foundry/models",
            "api_key": "secret",
            "endpoint": "http://localhost:5272",
        }

        result = self.checker.run_preflight(available_execs, config_data)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["executable_failures"]), 1)
        self.assertIn("MISSING_EXECUTABLE: 'foundry'", result["executable_failures"][0])
        self.assertEqual(len(result["config_failures"]), 0)

    def test_absent_config_field_gives_actionable_failure(self):
        """Absent config field produces specific actionable failure message."""
        available_execs = {"foundry": True, "python3": True}
        config_data = {
            "model_dir": "/opt/foundry/models",
            # 'api_key' and 'endpoint' are missing
        }

        result = self.checker.run_preflight(available_execs, config_data)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["config_failures"]), 2)
        self.assertTrue(any("api_key" in err for err in result["config_failures"]))
        self.assertTrue(any("endpoint" in err for err in result["config_failures"]))
        self.assertEqual(len(result["executable_failures"]), 0)

    def test_secrets_are_redacted_never_printed(self):
        """Secret values are replaced with [REDACTED] and raw secrets do not appear."""
        raw_secret = "super_confidential_token_xyz_999"
        available_execs = {"foundry": True, "python3": True}
        config_data = {
            "model_dir": "/opt/models",
            "api_key": raw_secret,
            "endpoint": "http://localhost:5272",
        }

        result = self.checker.run_preflight(available_execs, config_data)
        diagnostics_str = str(result["diagnostics"])
        self.assertNotIn(raw_secret, diagnostics_str)
        self.assertEqual(result["diagnostics"]["api_key"], "[REDACTED]")

    def test_compare_two_approaches_equivalence(self):
        """Compare direct procedural check with independent declarative reference approach."""
        test_execs = {"python3": True}  # missing 'foundry'
        test_config = {
            "model_dir": "/tmp/models",
            "api_key": "my-key-999",
            # missing 'endpoint'
        }

        # 1. Direct approach
        direct_res = self.checker.run_preflight(test_execs, test_config)

        # 2. Reference approach
        ref_passed, ref_failures, ref_diagnostics = reference_preflight_evaluator(
            self.req_executables, self.req_config, test_execs, test_config
        )

        # Equivalence checks
        self.assertEqual(direct_res["passed"], ref_passed)
        self.assertEqual(set(direct_res["all_failures"]), set(ref_failures))
        self.assertEqual(direct_res["diagnostics"], ref_diagnostics)


if __name__ == "__main__":
    unittest.main()
