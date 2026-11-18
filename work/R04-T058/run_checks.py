#!/usr/bin/env python3
"""
Verification check runner for R04-T058.
Validates Local Environment Preflight Check: Intermediate State Recording and Invariant Testing:
1. Canonical complete fixture passes (status PASS, 0 issues, all intermediate steps pass).
2. Missing executable produces separate actionable diagnostic (category MISSING_EXECUTABLE).
3. Absent config field produces separate actionable diagnostic (category ABSENT_CONFIG_FIELD).
4. Secret credentials strictly redacted (***REDACTED***) with zero leaks.
5. Intermediate states deterministically recorded after each step.
6. Formal invariants linking intermediate states to final report verified.
7. Deliberate failure verification (must exit non-zero).
8. Unittest discovery execution in a fresh process.
9. Writes evidence.json and test_output.txt to work/R04-T058/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Module03", "applied-labs", "r04-t058")
)
sys.path.insert(0, MODULE_DIR)

from example import (
    DEFAULT_REQUIRED_CONFIG_FIELDS,
    DEFAULT_REQUIRED_EXECUTABLES,
    DEFAULT_SECRET_KEYS,
    REDACTION_MASK,
    InvariantValidationResult,
    LocalEnvironmentPreflight,
    PreflightReport,
    demonstrate_intermediate_states_and_invariants,
    explain_mapping,
    identify_unestablished_behaviors,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []
    checker = LocalEnvironmentPreflight()

    # Check 1: Complete Valid Fixture Passes
    valid_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
            "api_token": "sk-secret-live-token-12345",
        },
    }
    report_1 = checker.check(valid_fixture)
    inv_1 = checker.verify_invariants(report_1)

    pass_1 = (
        report_1.passed
        and report_1.status == "PASS"
        and len(report_1.issues) == 0
        and len(report_1.intermediate_states) == 3
        and all(s.passed for s in report_1.intermediate_states)
        and inv_1.all_valid
    )
    status_1 = "PASSED" if pass_1 else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "complete_valid_fixture_passes",
        "inputs": {
            "executables": valid_fixture["executables"],
            "config": {
                "endpoint": valid_fixture["config"]["endpoint"],
                "port": valid_fixture["config"]["port"],
                "model_name": valid_fixture["config"]["model_name"],
                "api_token": "[REDACTED_IN_LOG]",
            },
        },
        "expected": {
            "status": "PASS",
            "passed": True,
            "issues_count": 0,
            "intermediate_states_count": 3,
            "all_steps_passed": True,
            "invariants_all_valid": True,
        },
        "actual": {
            "status": report_1.status,
            "passed": report_1.passed,
            "issues_count": len(report_1.issues),
            "intermediate_states_count": len(report_1.intermediate_states),
            "all_steps_passed": all(s.passed for s in report_1.intermediate_states),
            "invariants_all_valid": inv_1.all_valid,
        },
        "status": status_1,
    })

    # Check 2: Missing Executable Separate Actionable Failure
    missing_exe_fixture = {
        "executables": {"ollama": False, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
        },
    }
    report_2 = checker.check(missing_exe_fixture)
    inv_2 = checker.verify_invariants(report_2)

    pass_2 = (
        (not report_2.passed)
        and report_2.status == "FAIL"
        and report_2.missing_executables == ["ollama"]
        and report_2.absent_config_fields == []
        and len(report_2.issues) == 1
        and report_2.issues[0].category == "MISSING_EXECUTABLE"
        and "ollama" in report_2.issues[0].action.lower()
        and (not report_2.intermediate_states[0].passed)
        and report_2.intermediate_states[1].passed
        and inv_2.all_valid
    )
    status_2 = "PASSED" if pass_2 else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "missing_executable_gives_separate_actionable_failure",
        "inputs": missing_exe_fixture,
        "expected": {
            "status": "FAIL",
            "missing_executables": ["ollama"],
            "absent_config_fields": [],
            "category": "MISSING_EXECUTABLE",
            "step1_passed": False,
            "step2_passed": True,
            "invariants_all_valid": True,
        },
        "actual": {
            "status": report_2.status,
            "missing_executables": report_2.missing_executables,
            "absent_config_fields": report_2.absent_config_fields,
            "category": report_2.issues[0].category if report_2.issues else None,
            "step1_passed": report_2.intermediate_states[0].passed,
            "step2_passed": report_2.intermediate_states[1].passed,
            "invariants_all_valid": inv_2.all_valid,
        },
        "status": status_2,
    })

    # Check 3: Absent Config Field Separate Actionable Failure
    absent_config_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            # "model_name" absent!
        },
    }
    report_3 = checker.check(absent_config_fixture)
    inv_3 = checker.verify_invariants(report_3)

    pass_3 = (
        (not report_3.passed)
        and report_3.status == "FAIL"
        and report_3.absent_config_fields == ["model_name"]
        and report_3.missing_executables == []
        and len(report_3.issues) == 1
        and report_3.issues[0].category == "ABSENT_CONFIG_FIELD"
        and "model_name" in report_3.issues[0].action.lower()
        and report_3.intermediate_states[0].passed
        and (not report_3.intermediate_states[1].passed)
        and inv_3.all_valid
    )
    status_3 = "PASSED" if pass_3 else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "absent_config_field_gives_separate_actionable_failure",
        "inputs": absent_config_fixture,
        "expected": {
            "status": "FAIL",
            "missing_executables": [],
            "absent_config_fields": ["model_name"],
            "category": "ABSENT_CONFIG_FIELD",
            "step1_passed": True,
            "step2_passed": False,
            "invariants_all_valid": True,
        },
        "actual": {
            "status": report_3.status,
            "missing_executables": report_3.missing_executables,
            "absent_config_fields": report_3.absent_config_fields,
            "category": report_3.issues[0].category if report_3.issues else None,
            "step1_passed": report_3.intermediate_states[0].passed,
            "step2_passed": report_3.intermediate_states[1].passed,
            "invariants_all_valid": inv_3.all_valid,
        },
        "status": status_3,
    })

    # Check 4: Strict Credential Redaction
    secret_val = "live-production-secret-token-abcdef999"
    secret_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
            "api_token": secret_val,
            "auth_password": "super-secret-password-xyz",
        },
    }
    report_4 = checker.check(secret_fixture)
    summary_4 = report_4.summary()
    dict_json_4 = json.dumps(report_4.to_dict())

    pass_4 = (
        report_4.config_evaluated["api_token"] == REDACTION_MASK
        and report_4.config_evaluated["auth_password"] == REDACTION_MASK
        and (secret_val not in summary_4)
        and (secret_val not in str(report_4))
        and (secret_val not in dict_json_4)
        and ("super-secret-password-xyz" not in dict_json_4)
    )
    status_4 = "PASSED" if pass_4 else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "secret_values_never_printed_or_serialized",
        "inputs": {"keys_tested": ["api_token", "auth_password"]},
        "expected": {
            "api_token_evaluated": REDACTION_MASK,
            "auth_password_evaluated": REDACTION_MASK,
            "cleartext_in_summary": False,
            "cleartext_in_json": False,
        },
        "actual": {
            "api_token_evaluated": report_4.config_evaluated["api_token"],
            "auth_password_evaluated": report_4.config_evaluated["auth_password"],
            "cleartext_in_summary": secret_val in summary_4,
            "cleartext_in_json": secret_val in dict_json_4,
        },
        "status": status_4,
    })

    # Check 5: Intermediate State Recording and Invariant Validation
    states = report_1.intermediate_states
    pass_5 = (
        len(states) == 3
        and states[0].step_name == "check_executables"
        and states[1].step_name == "check_config_fields"
        and states[2].step_name == "sanitize_and_redact_secrets"
        and [s.step_index for s in states] == [1, 2, 3]
        and inv_1.all_valid
        and len(inv_1.checks) == 5
        and all(c.passed for c in inv_1.checks)
    )
    status_5 = "PASSED" if pass_5 else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "intermediate_states_and_invariants_verified",
        "expected": {
            "states_count": 3,
            "step_names": ["check_executables", "check_config_fields", "sanitize_and_redact_secrets"],
            "invariants_count": 5,
            "all_invariants_passed": True,
        },
        "actual": {
            "states_count": len(states),
            "step_names": [s.step_name for s in states],
            "invariants_count": len(inv_1.checks),
            "all_invariants_passed": inv_1.all_valid,
        },
        "status": status_5,
    })

    # Check 6: Unestablished Behaviors and Concept Mapping
    unestablished = identify_unestablished_behaviors()
    mapping = explain_mapping()
    pass_6 = (len(unestablished) >= 5) and (len(mapping) >= 5)
    status_6 = "PASSED" if pass_6 else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "unestablished_behaviors_and_concept_mapping",
        "expected": "At least 5 unestablished behaviors and 5 lesson concept mappings",
        "actual": {"unestablished_count": len(unestablished), "mapping_count": len(mapping)},
        "status": status_6,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import LocalEnvironmentPreflight
checker = LocalEnvironmentPreflight()
# Incomplete fixture missing 'ollama' and 'model_name'
faulty_fixture = {
    "executables": {"ollama": False, "docker": True},
    "config": {"endpoint": "http://localhost:11434", "port": 11434},
}
report = checker.check(faulty_fixture)
# Deliberate failure assertion: assert that faulty fixture passed
assert report.passed, "Intentional failure check: faulty fixture must not report passed"
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=MODULE_DIR,
        capture_output=True,
        text=True,
    )
    passed = (proc.returncode != 0) and ("AssertionError" in proc.stderr)
    return {
        "description": "Verify deliberate wrong result causes non-zero exit code",
        "exit_code": proc.returncode,
        "stderr_snippet": proc.stderr.strip().splitlines()[-1] if proc.stderr else "",
        "deliberate_failure_verified": passed,
    }


def run_unit_tests() -> Dict[str, Any]:
    """Execute unittest discover in a fresh process and capture results."""
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "Module03/applied-labs/r04-t058",
        "-p",
        "test_*.py",
    ]
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> None:
    work_dir = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(work_dir, exist_ok=True)

    print("Running contract checks...")
    checks = run_contract_checks()
    print(f"Executed {len(checks)} contract checks successfully.")

    print("Verifying deliberate failure behavior...")
    deliberate_fail = test_deliberate_failure()
    assert deliberate_fail["deliberate_failure_verified"], "Deliberate failure did not exit non-zero!"
    print(f"Deliberate failure correctly exited with non-zero code ({deliberate_fail['exit_code']}).")

    print("Running unittest discovery in fresh process...")
    unittest_res = run_unit_tests()
    if unittest_res["exit_code"] != 0:
        print(f"Unittest failed with exit code {unittest_res['exit_code']}:\n{unittest_res['stderr']}")
        sys.exit(unittest_res["exit_code"])
    print("Unittests completed successfully.")

    # Save test_output.txt
    test_output_path = os.path.join(work_dir, "test_output.txt")
    with open(test_output_path, "w", encoding="utf-8") as f:
        f.write(unittest_res["stderr"])

    # Prepare evidence.json
    evidence = {
        "task_id": "R04-T058",
        "issue": 58,
        "module": "Module03/02.DeployingSLMinLocalEnv.md",
        "python_version": sys.version,
        "platform": platform.platform(),
        "tool_versions": {
            "python": sys.version.split()[0],
            "unittest": "standard_library",
            "os": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "test_cases": checks,
        "deliberate_failure_demonstration": deliberate_fail,
        "unittest_execution": {
            "command": unittest_res["command"],
            "exit_code": unittest_res["exit_code"],
            "raw_output": unittest_res["stderr"].strip(),
        },
        "all_checks_passed": True,
    }

    evidence_path = os.path.join(work_dir, "evidence.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print(f"Evidence successfully written to:\n - {evidence_path}\n - {test_output_path}")


if __name__ == "__main__":
    main()
