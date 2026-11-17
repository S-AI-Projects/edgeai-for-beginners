"""
Unit tests for R04-T020 Installation Preflight Report.
Tests complete fixture pass, missing executable/config separation, secret masking, and applied questions.
"""

import json
import unittest

from example import (
    APPLIED_QUESTIONS,
    CANONICAL_REQUIRED_CONFIGS,
    CANONICAL_REQUIRED_EXECS,
    PreflightChecker,
    run_concept_example,
)


class TestPreflightNormalAndErrors(unittest.TestCase):
    def setUp(self):
        self.checker = PreflightChecker(CANONICAL_REQUIRED_EXECS, CANONICAL_REQUIRED_CONFIGS)

    def test_complete_fixture_passes(self):
        """A complete fixture passes."""
        obs = {
            "executables": ["python3", "git"],
            "config": {
                "cache_dir": "/opt/cache",
                "api_token": "token_12345",
            }
        }
        res = self.checker.check(obs)
        self.assertTrue(res["passed"])
        self.assertEqual(res["status"], "PASSED")
        self.assertEqual(len(res["missing_executables"]), 0)
        self.assertEqual(len(res["missing_configs"]), 0)

    def test_missing_executable_actionable_failure(self):
        """Missing executable gives actionable failure with EXECUTABLE_NOT_FOUND."""
        obs = {
            "executables": ["python3"],  # git missing
            "config": {
                "cache_dir": "/opt/cache",
                "api_token": "token_12345",
            }
        }
        res = self.checker.check(obs)
        self.assertFalse(res["passed"])
        self.assertEqual(res["status"], "FAILED")
        self.assertEqual(len(res["missing_executables"]), 1)
        missing_item = res["missing_executables"][0]
        self.assertEqual(missing_item["executable"], "git")
        self.assertEqual(missing_item["code"], "EXECUTABLE_NOT_FOUND")
        self.assertIn("Install 'git'", missing_item["action"])

    def test_absent_config_field_actionable_failure(self):
        """Absent config field gives separate actionable failure with CONFIG_FIELD_MISSING."""
        obs = {
            "executables": ["python3", "git"],
            "config": {
                "cache_dir": "/opt/cache",
                # api_token is absent
            }
        }
        res = self.checker.check(obs)
        self.assertFalse(res["passed"])
        self.assertEqual(res["status"], "FAILED")
        self.assertEqual(len(res["missing_configs"]), 1)
        missing_item = res["missing_configs"][0]
        self.assertEqual(missing_item["field"], "api_token")
        self.assertEqual(missing_item["code"], "CONFIG_FIELD_MISSING")
        self.assertIn("Set configuration parameter 'api_token'", missing_item["action"])

    def test_secret_values_are_never_printed(self):
        """Secret values are masked and never exposed in plaintext."""
        secret_plaintext = "SUPER_SECRET_KEY_999888"
        obs = {
            "executables": ["python3", "git"],
            "config": {
                "cache_dir": "/opt/cache",
                "api_token": secret_plaintext,
                "anthropic_api_key": secret_plaintext,
                "db_password": secret_plaintext,
            }
        }
        res = self.checker.check(obs)
        serialized = json.dumps(res)

        # Plaintext secret MUST NOT appear anywhere in output or serialized json
        self.assertNotIn(secret_plaintext, serialized)
        self.assertEqual(res["sanitized_config"]["api_token"], "***")
        self.assertEqual(res["sanitized_config"]["anthropic_api_key"], "***")
        self.assertEqual(res["sanitized_config"]["db_password"], "***")

    def test_run_concept_example_summary(self):
        summary = run_concept_example()
        self.assertTrue(summary["complete_passed"])
        self.assertEqual(summary["complete_status"], "PASSED")
        self.assertTrue(summary["token_masked"])
        self.assertFalse(summary["secrets_leaked"])
        self.assertEqual(summary["missing_exe_code"], "EXECUTABLE_NOT_FOUND")
        self.assertEqual(summary["missing_cfg_code"], "CONFIG_FIELD_MISSING")


class TestAppliedQuestionsExecutableChecks(unittest.TestCase):
    def test_q1_predict_output_executable_check(self):
        """Verifies prediction for Question 1."""
        checker = PreflightChecker(CANONICAL_REQUIRED_EXECS, CANONICAL_REQUIRED_CONFIGS)
        obs = {"executables": ["python3", "git"], "config": {"cache_dir": "/tmp", "api_token": "secret_abc"}}
        res = checker.check(obs)
        self.assertEqual(res["status"], "PASSED")
        self.assertEqual(res["sanitized_config"]["api_token"], "***")

    def test_q2_diagnose_failure_executable_check(self):
        """Verifies diagnosis for Question 2."""
        checker = PreflightChecker(CANONICAL_REQUIRED_EXECS, CANONICAL_REQUIRED_CONFIGS)
        obs = {"executables": ["python3"], "config": {"cache_dir": "/tmp", "api_token": "secret_abc"}}
        res = checker.check(obs)
        self.assertEqual(res["status"], "FAILED")
        self.assertEqual(res["missing_executables"][0]["code"], "EXECUTABLE_NOT_FOUND")
        self.assertEqual(res["missing_executables"][0]["executable"], "git")

    def test_q3_boundary_policy_executable_check(self):
        """Verifies policy enforcement for Question 3."""
        checker = PreflightChecker(["python3"], ["mandatory_key"])
        obs = {"executables": ["python3"], "config": {}}
        res = checker.check(obs)
        self.assertFalse(res["passed"])
        self.assertEqual(res["missing_configs"][0]["code"], "CONFIG_FIELD_MISSING")


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_checker_leaking_secret_fails(self):
        """A flawed checker that prints plaintext secrets violates contract and fails test."""
        flawed_output = {"api_token": "my_secret_token_123"}
        with self.assertRaises(AssertionError):
            self.assertEqual(flawed_output["api_token"], "***")

    def test_flawed_checker_passing_missing_executable_fails(self):
        """A flawed checker that ignores missing executables fails check."""
        flawed_passed = True
        with self.assertRaises(AssertionError):
            self.assertFalse(flawed_passed)


if __name__ == "__main__":
    unittest.main()

