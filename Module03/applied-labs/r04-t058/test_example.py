"""
Unit tests for Local Environment Preflight Check: Intermediate State & Invariant Testing (R04-T058).

Tests:
1. Complete fixture passes.
2. Missing executable gives separate actionable failure.
3. Absent configuration field gives separate actionable failure.
4. Secret values are never printed or serialized in cleartext (strict redaction).
5. Intermediate states are recorded after each step with sequential indices and audit details.
6. Invariant: Status equivalence (final status equals conjunction of intermediate step statuses).
7. Invariant: Issue partition & union (final issues equal concatenation of step issues).
8. Invariant: Categorical consistency (missing executables and absent fields match step details).
9. Invariant: Strict redaction preservation (no cleartext secrets in step states or report).
10. Invariant: Chronological monotonicity (sequential step indices and non-decreasing issue count).
11. Invariant verification engine failure detection on tampered or corrupted reports.
12. Boundary conditions (invalid port ranges, empty string values).
13. Unestablished real-service behaviors and concept mapping integrity.
14. End-to-end demonstration workflow and invariant verification.
"""

import json
import unittest

from example import (
    DEFAULT_REQUIRED_CONFIG_FIELDS,
    DEFAULT_REQUIRED_EXECUTABLES,
    DEFAULT_SECRET_KEYS,
    REDACTION_MASK,
    InvariantValidationResult,
    LocalEnvironmentPreflight,
    PreflightIssue,
    PreflightReport,
    StepIntermediateState,
    demonstrate_intermediate_states_and_invariants,
    explain_mapping,
    identify_unestablished_behaviors,
    sanitize_config,
)


class TestLocalEnvironmentPreflightIntermediateStates(unittest.TestCase):
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

        # Verify all intermediate steps passed
        self.assertEqual(len(report.intermediate_states), 3)
        for state in report.intermediate_states:
            self.assertTrue(state.passed)
            self.assertEqual(state.status, "PASS")

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

        # Verify step 1 caught the failure while step 2 passed
        step1 = report.intermediate_states[0]
        step2 = report.intermediate_states[1]
        self.assertFalse(step1.passed)
        self.assertEqual(step1.status, "FAIL")
        self.assertEqual(step1.details["missing_executables"], ["ollama"])
        self.assertTrue(step2.passed)
        self.assertEqual(step2.status, "PASS")

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

        # Verify step 1 passed while step 2 caught the failure
        step1 = report.intermediate_states[0]
        step2 = report.intermediate_states[1]
        self.assertTrue(step1.passed)
        self.assertEqual(step1.status, "PASS")
        self.assertFalse(step2.passed)
        self.assertEqual(step2.status, "FAIL")
        self.assertEqual(step2.details["absent_config_fields"], ["model_name"])

    def test_secret_values_never_printed_or_serialized(self):
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
                "admin_password": "super-secret-password-xyz",
            },
        }
        report = self.checker.check(fixture)

        # 1. Direct config inspection
        self.assertEqual(report.config_evaluated["api_token"], REDACTION_MASK)
        self.assertEqual(report.config_evaluated["admin_password"], REDACTION_MASK)

        # 2. String conversion / Summary inspection
        summary_str = report.summary()
        self.assertNotIn(secret_value, summary_str)
        self.assertNotIn("super-secret-password-xyz", summary_str)

        str_repr = str(report)
        self.assertNotIn(secret_value, str_repr)
        self.assertNotIn("super-secret-password-xyz", str_repr)

        # 3. Serialized dictionary inspection
        report_dict = report.to_dict()
        dict_json = json.dumps(report_dict)
        self.assertNotIn(secret_value, dict_json)
        self.assertNotIn("super-secret-password-xyz", dict_json)

        # 4. Step 3 intermediate state inspection
        step3 = report.intermediate_states[2]
        self.assertTrue(step3.passed)
        self.assertIn("api_token", step3.details["secret_keys_redacted"])
        self.assertIn("admin_password", step3.details["secret_keys_redacted"])

    def test_intermediate_states_recorded_after_each_step(self):
        """Verify that intermediate states are deterministically recorded after each step."""
        report = self.checker.check(self.complete_valid_fixture)
        states = report.intermediate_states

        self.assertEqual(len(states), 3)

        # Step 1: Executable check
        self.assertEqual(states[0].step_index, 1)
        self.assertEqual(states[0].step_name, "check_executables")
        self.assertIn("executables_checked", states[0].details)

        # Step 2: Config check
        self.assertEqual(states[1].step_index, 2)
        self.assertEqual(states[1].step_name, "check_config_fields")
        self.assertIn("required_config_fields", states[1].details)

        # Step 3: Redaction check
        self.assertEqual(states[2].step_index, 3)
        self.assertEqual(states[2].step_name, "sanitize_and_redact_secrets")
        self.assertIn("secret_keys_redacted", states[2].details)

    def test_invariant_status_equivalence(self):
        """Verify invariant: final report status equals conjunction of all intermediate step statuses."""
        # Case A: All steps pass -> final report PASS
        rep_pass = self.checker.check(self.complete_valid_fixture)
        inv_pass = self.checker.verify_invariants(rep_pass)
        check1 = next(c for c in inv_pass.checks if c.name == "status_equivalence")
        self.assertTrue(check1.passed)

        # Case B: Step 1 fails -> final report FAIL
        fail_exe_fixture = {
            "executables": {"ollama": False, "docker": True},
            "config": {"endpoint": "http://localhost:11434", "port": 11434, "model_name": "phi4:mini"},
        }
        rep_fail = self.checker.check(fail_exe_fixture)
        inv_fail = self.checker.verify_invariants(rep_fail)
        check1_fail = next(c for c in inv_fail.checks if c.name == "status_equivalence")
        self.assertTrue(check1_fail.passed)
        self.assertEqual(rep_fail.status, "FAIL")

    def test_invariant_issue_partition_and_union(self):
        """Verify invariant: final issues list equals ordered concatenation of all step issues."""
        multi_issue_fixture = {
            "executables": {"ollama": False, "docker": False},  # 2 missing executables
            "config": {
                # missing endpoint and model_name
                "port": "invalid-port",  # 1 invalid port
            },
        }
        report = self.checker.check(multi_issue_fixture)
        inv = self.checker.verify_invariants(report)
        check2 = next(c for c in inv.checks if c.name == "issue_partition_and_union")
        self.assertTrue(check2.passed)

        step1_issues = report.intermediate_states[0].issues
        step2_issues = report.intermediate_states[1].issues
        step3_issues = report.intermediate_states[2].issues
        self.assertEqual(report.issues, step1_issues + step2_issues + step3_issues)

    def test_invariant_categorical_consistency(self):
        """Verify invariant: categorical failure lists match intermediate state details."""
        fixture = {
            "executables": {"ollama": False, "docker": True},
            "config": {"endpoint": "http://localhost:11434", "port": 11434},  # model_name missing
        }
        report = self.checker.check(fixture)
        inv = self.checker.verify_invariants(report)
        check3 = next(c for c in inv.checks if c.name == "categorical_consistency")
        self.assertTrue(check3.passed)

        self.assertEqual(report.missing_executables, ["ollama"])
        self.assertEqual(report.absent_config_fields, ["model_name"])

    def test_invariant_strict_redaction_preservation(self):
        """Verify invariant: sensitive keys are redacted in Step 3 and final config with zero leaks."""
        report = self.checker.check(self.complete_valid_fixture)
        inv = self.checker.verify_invariants(report)
        check4 = next(c for c in inv.checks if c.name == "strict_redaction_preservation")
        self.assertTrue(check4.passed)

    def test_invariant_chronological_monotonicity(self):
        """Verify invariant: step indices are sequential and issue count is non-decreasing."""
        report = self.checker.check(self.complete_valid_fixture)
        inv = self.checker.verify_invariants(report)
        check5 = next(c for c in inv.checks if c.name == "chronological_monotonicity")
        self.assertTrue(check5.passed)

    def test_invariant_verification_catches_tampered_state(self):
        """Verify invariant engine catches corrupted or inconsistent state (negative testing)."""
        report = self.checker.check(self.complete_valid_fixture)

        # Tamper with status to simulate broken invariant 1
        tampered_report = PreflightReport(
            status="FAIL",  # Inconsistent with step states which all passed!
            passed=False,
            lesson_source=report.lesson_source,
            executables_checked=report.executables_checked,
            config_evaluated=report.config_evaluated,
            issues=report.issues,
            intermediate_states=report.intermediate_states,
        )
        inv_tampered = self.checker.verify_invariants(tampered_report)
        self.assertFalse(inv_tampered.all_valid)
        check1 = next(c for c in inv_tampered.checks if c.name == "status_equivalence")
        self.assertFalse(check1.passed)

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
        """Verify explicit declarations that validator does not claim live service or hardware actions."""
        unestablished = identify_unestablished_behaviors()
        self.assertGreaterEqual(len(unestablished), 5)
        combined = " ".join(unestablished).lower()
        self.assertIn("network", combined)
        self.assertIn("package managers", combined)
        self.assertIn("gpu", combined)
        self.assertIn("daemon", combined)
        self.assertIn("model weights", combined)

    def test_concept_mapping_integrity(self):
        """Verify conceptual mapping aligns with Module03/02.DeployingSLMinLocalEnv.md."""
        mappings = explain_mapping()
        self.assertGreaterEqual(len(mappings), 5)
        for item in mappings:
            self.assertIn("preflight_component", item)
            self.assertIn("lesson_concept", item)
            self.assertIn("pedagogical_purpose", item)

    def test_demonstrate_workflow(self):
        """Verify end-to-end demonstration workflow runs and all scenario invariants hold."""
        demo = demonstrate_intermediate_states_and_invariants(self.checker)
        self.assertTrue(demo["all_invariants_confirmed"])
        self.assertEqual(demo["scenario_valid"]["status"], "PASS")
        self.assertEqual(demo["scenario_missing_executable"]["status"], "FAIL")
        self.assertEqual(demo["scenario_absent_config"]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
