"""
Unit tests for Local Environment Preflight Check (R04-T056).

Tests:
1. Complete fixture passes.
2. Missing executable gives separate actionable failure.
3. Absent configuration field gives separate actionable failure.
4. Secret values are never printed or serialized in cleartext (strict redaction).
5. Documented invalid/missing-data case with failure diagnosis and clean recovery on valid input.
6. Boundary conditions (empty strings, invalid port ranges).
7. Non-intrusive offline behavior and lesson concept mapping.
"""

import json
import unittest

from example import (
    DEFAULT_REQUIRED_CONFIG_FIELDS,
    DEFAULT_REQUIRED_EXECUTABLES,
    DEFAULT_SECRET_KEYS,
    REDACTION_MASK,
    LocalEnvironmentPreflight,
    PreflightReport,
    demonstrate_failure_and_recovery,
    explain_mapping,
    sanitize_config,
)


class TestLocalEnvironmentPreflight(unittest.TestCase):
    def setUp(self):
        self.checker = LocalEnvironmentPreflight()
        self.complete_valid_fixture = {
            "executables": {
                "ollama": True,
                "docker": True,
            },
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                "model_name": "phi4:mini",
                "api_token": "super-confidential-secret-key-98765",
            },
        }

    def test_complete_fixture_passes(self):
        """Verify that a complete fixture satisfies all preflight checks and passes."""
        report = self.checker.check(self.complete_valid_fixture)
        self.assertTrue(report.passed)
        self.assertEqual(report.status, "PASS")
        self.assertEqual(len(report.issues), 0)
        self.assertEqual(report.missing_executables, [])
        self.assertEqual(report.absent_config_fields, [])
        self.assertEqual(report.invalid_config_fields, [])

    def test_missing_executable_gives_separate_actionable_failure(self):
        """Verify missing executable fails with category MISSING_EXECUTABLE and actionable fix."""
        fixture = {
            "executables": {
                "ollama": False,  # Missing
                "docker": True,
            },
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                "model_name": "phi4:mini",
            },
        }
        report = self.checker.check(fixture)
        self.assertFalse(report.passed)
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(report.missing_executables, ["ollama"])
        self.assertEqual(report.absent_config_fields, [])

        # Verify actionable diagnostic
        issues = [i for i in report.issues if i.category == "MISSING_EXECUTABLE"]
        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue.target, "ollama")
        self.assertIn("missing", issue.message.lower())
        self.assertIn("install 'ollama'", issue.action.lower())

    def test_absent_config_field_gives_separate_actionable_failure(self):
        """Verify absent config field fails with category ABSENT_CONFIG_FIELD and actionable fix."""
        fixture = {
            "executables": {
                "ollama": True,
                "docker": True,
            },
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                # "model_name" is absent!
            },
        }
        report = self.checker.check(fixture)
        self.assertFalse(report.passed)
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(report.absent_config_fields, ["model_name"])
        self.assertEqual(report.missing_executables, [])

        # Verify actionable diagnostic
        issues = [i for i in report.issues if i.category == "ABSENT_CONFIG_FIELD"]
        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue.target, "model_name")
        self.assertIn("absent", issue.message.lower())
        self.assertIn("specify 'model_name'", issue.action.lower())

    def test_secret_values_are_never_printed_or_serialized(self):
        """
        Verify that secret tokens, keys, and passwords are never exposed in cleartext.
        They must be replaced with ***REDACTED*** in reports, dicts, summaries, and strings.
        """
        secret_value = "top-secret-bearer-token-abc123xyz"
        fixture = {
            "executables": {"ollama": True, "docker": True},
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                "model_name": "phi4:mini",
                "api_token": secret_value,
                "admin_secret_key": secret_value,
                "auth_token": secret_value,
            },
        }
        report = self.checker.check(fixture)

        # 1. Check evaluated config dictionary
        for secret_field in ["api_token", "admin_secret_key", "auth_token"]:
            self.assertEqual(report.config_evaluated[secret_field], REDACTION_MASK)

        # 2. Check serialized JSON
        serialized = json.dumps(report.to_dict())
        self.assertNotIn(secret_value, serialized)
        self.assertIn(REDACTION_MASK, serialized)

        # 3. Check summary string and __str__
        summary_str = report.summary()
        self.assertNotIn(secret_value, summary_str)
        self.assertNotIn(secret_value, str(report))

    def test_failure_and_recovery_flow(self):
        """
        Exercise a documented invalid/missing-data case, explain the error,
        and demonstrate recovery on the next valid input.
        """
        result = demonstrate_failure_and_recovery(self.checker)

        # Initial attempt must fail
        self.assertFalse(result["initial_attempt"]["passed"])
        self.assertEqual(result["initial_attempt"]["status"], "FAIL")
        self.assertIn("ollama", result["initial_attempt"]["missing_executables"])
        self.assertIn("model_name", result["initial_attempt"]["absent_config_fields"])

        # Recovery patch must supply missing elements
        self.assertIn("executables", result["recovery_patch_applied"])
        self.assertIn("config", result["recovery_patch_applied"])

        # Recovered attempt must pass
        self.assertTrue(result["recovered_attempt"]["passed"])
        self.assertEqual(result["recovered_attempt"]["status"], "PASS")
        self.assertEqual(len(result["recovered_attempt"]["issues"]), 0)

        # Overall recovery workflow succeeded
        self.assertTrue(result["recovery_successful"])

    def test_invalid_config_values_boundary_checks(self):
        """Verify invalid port values and empty strings are rejected with actionable guidance."""
        # Non-numeric port
        invalid_port_fixture = {
            "executables": {"ollama": True, "docker": True},
            "config": {
                "endpoint": "http://localhost:11434",
                "port": "not-a-port",
                "model_name": "phi4:mini",
            },
        }
        report = self.checker.check(invalid_port_fixture)
        self.assertFalse(report.passed)
        self.assertIn("port", report.invalid_config_fields)

        # Out-of-range port
        out_of_range_fixture = {
            "executables": {"ollama": True, "docker": True},
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 999999,
                "model_name": "phi4:mini",
            },
        }
        report2 = self.checker.check(out_of_range_fixture)
        self.assertFalse(report2.passed)
        self.assertIn("port", report2.invalid_config_fields)

        # Empty string model_name
        empty_model_fixture = {
            "executables": {"ollama": True, "docker": True},
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                "model_name": "   ",
            },
        }
        report3 = self.checker.check(empty_model_fixture)
        self.assertFalse(report3.passed)
        self.assertIn("model_name", report3.invalid_config_fields)

    def test_unestablished_behaviors_documented(self):
        """Verify explicit declarations that mock does not contact real daemons or install packages."""
        unestablished = LocalEnvironmentPreflight.identify_unestablished_behaviors()
        self.assertGreaterEqual(len(unestablished), 4)
        combined = " ".join(unestablished).lower()
        self.assertIn("network", combined)
        self.assertIn("package managers", combined)
        self.assertIn("gpu", combined)

    def test_concept_mapping_integrity(self):
        """Verify conceptual mapping aligns with Module03/02.DeployingSLMinLocalEnv.md."""
        mappings = explain_mapping()
        self.assertGreaterEqual(len(mappings), 4)
        for item in mappings:
            self.assertIn("preflight_component", item)
            self.assertIn("lesson_concept", item)
            self.assertIn("pedagogical_purpose", item)

    def test_custom_secret_keys_and_case_insensitivity(self):
        """Verify custom secret keys and case-insensitive redaction."""
        custom_checker = LocalEnvironmentPreflight(secret_keys={"custom_token", "vault_key"})
        fixture = {
            "executables": ["ollama", "docker"],
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                "model_name": "phi4:mini",
                "CUSTOM_TOKEN": "hidden-secret-value",
                "vault_key": "another-secret-value",
            },
        }
        report = custom_checker.check(fixture)
        self.assertTrue(report.passed)
        self.assertEqual(report.config_evaluated["CUSTOM_TOKEN"], REDACTION_MASK)
        self.assertEqual(report.config_evaluated["vault_key"], REDACTION_MASK)
        self.assertNotIn("hidden-secret-value", str(report))
        self.assertNotIn("another-secret-value", str(report))

    def test_list_and_set_executable_fixtures(self):
        """Verify executables supplied as lists or sets are evaluated properly."""
        fixture_list = {
            "executables": ["ollama"],  # docker missing
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                "model_name": "phi4:mini",
            },
        }
        report = self.checker.check(fixture_list)
        self.assertFalse(report.passed)
        self.assertEqual(report.missing_executables, ["docker"])


if __name__ == "__main__":
    unittest.main()
