#!/usr/bin/env python3
"""
Verification check runner for R04-T056.
Validates Local Environment Preflight Check:
1. Complete fixture passes.
2. Missing executable gives separate actionable failure.
3. Absent config field gives separate actionable failure.
4. Secret values are never printed or serialized (strict redaction).
5. Documented invalid/missing-data failure diagnosis and recovery on next valid input.
6. Deliberate failure verification (must exit non-zero).
7. Unittest discovery execution in fresh process.
8. Writes evidence.json and test_output.txt to work/R04-T056/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Module03", "applied-labs", "r04-t056")
)
sys.path.insert(0, MODULE_DIR)

from example import (
    DEFAULT_SECRET_KEYS,
    REDACTION_MASK,
    LocalEnvironmentPreflight,
    demonstrate_failure_and_recovery,
    explain_mapping,
    identify_unestablished_behaviors,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []
    checker = LocalEnvironmentPreflight()

    complete_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
            "api_token": "secret-token-super-private-999",
        },
    }

    missing_exe_fixture = {
        "executables": {"ollama": False, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
        },
    }

    absent_config_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            # "model_name" absent
        },
    }

    # Check 1: Complete fixture passes
    res_1 = checker.check(complete_fixture)
    status_1 = "PASSED" if (res_1.passed and res_1.status == "PASS" and not res_1.issues) else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "complete_fixture_passes",
        "inputs": complete_fixture,
        "expected": {"status": "PASS", "passed": True, "issues_count": 0},
        "actual": {"status": res_1.status, "passed": res_1.passed, "issues_count": len(res_1.issues)},
        "status": status_1,
    })

    # Check 2: Missing executable gives separate actionable failure
    res_2 = checker.check(missing_exe_fixture)
    has_exe_issue = any(i.category == "MISSING_EXECUTABLE" and i.target == "ollama" for i in res_2.issues)
    has_no_config_issue = len(res_2.absent_config_fields) == 0
    status_2 = "PASSED" if (not res_2.passed and res_2.status == "FAIL" and has_exe_issue and has_no_config_issue) else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "missing_executable_actionable_failure",
        "inputs": missing_exe_fixture,
        "expected": {
            "status": "FAIL",
            "passed": False,
            "missing_executables": ["ollama"],
            "absent_config_fields": [],
        },
        "actual": {
            "status": res_2.status,
            "passed": res_2.passed,
            "missing_executables": res_2.missing_executables,
            "absent_config_fields": res_2.absent_config_fields,
        },
        "status": status_2,
    })

    # Check 3: Absent config field gives separate actionable failure
    res_3 = checker.check(absent_config_fixture)
    has_cfg_issue = any(i.category == "ABSENT_CONFIG_FIELD" and i.target == "model_name" for i in res_3.issues)
    has_no_exe_issue = len(res_3.missing_executables) == 0
    status_3 = "PASSED" if (not res_3.passed and res_3.status == "FAIL" and has_cfg_issue and has_no_exe_issue) else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "absent_config_field_actionable_failure",
        "inputs": absent_config_fixture,
        "expected": {
            "status": "FAIL",
            "passed": False,
            "absent_config_fields": ["model_name"],
            "missing_executables": [],
        },
        "actual": {
            "status": res_3.status,
            "passed": res_3.passed,
            "absent_config_fields": res_3.absent_config_fields,
            "missing_executables": res_3.missing_executables,
        },
        "status": status_3,
    })

    # Check 4: Secret values are never printed or serialized in cleartext
    raw_secret = "secret-token-super-private-999"
    redacted_val = res_1.config_evaluated.get("api_token")
    serialized = json.dumps(res_1.to_dict())
    summary_str = res_1.summary()
    secret_leaked = (raw_secret in serialized) or (raw_secret in summary_str)
    status_4 = "PASSED" if (redacted_val == REDACTION_MASK and not secret_leaked) else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "secrets_never_printed_redacted_diagnostics",
        "expected": {"api_token": REDACTION_MASK, "raw_secret_exposed": False},
        "actual": {"api_token": redacted_val, "raw_secret_exposed": secret_leaked},
        "status": status_4,
    })

    # Check 5: Documented invalid case, failure explanation, and recovery on valid input
    flow = demonstrate_failure_and_recovery(checker)
    status_5 = "PASSED" if (
        not flow["initial_attempt"]["passed"]
        and flow["recovered_attempt"]["passed"]
        and flow["recovery_successful"]
    ) else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "failure_diagnosis_and_recovery_flow",
        "expected": {
            "initial_passed": False,
            "recovered_passed": True,
            "recovery_successful": True,
        },
        "actual": {
            "initial_passed": flow["initial_attempt"]["passed"],
            "recovered_passed": flow["recovered_attempt"]["passed"],
            "recovery_successful": flow["recovery_successful"],
        },
        "status": status_5,
    })

    # Check 6: Exact lesson requirement recorded
    status_6 = "PASSED" if res_1.lesson_source == "Module03/02.DeployingSLMinLocalEnv.md" else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "exact_lesson_source_recorded",
        "expected": "Module03/02.DeployingSLMinLocalEnv.md",
        "actual": res_1.lesson_source,
        "status": status_6,
    })

    # Check 7: Unestablished real-service behaviors documented
    unestablished = identify_unestablished_behaviors()
    mapping = explain_mapping()
    status_7 = "PASSED" if (len(unestablished) >= 4 and len(mapping) >= 4) else "FAILED"
    if status_7 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "unestablished_behaviors_and_concept_mapping",
        "expected": "At least 4 unestablished behaviors and 4 lesson concept mappings",
        "actual": {"unestablished_count": len(unestablished), "mapping_count": len(mapping)},
        "status": status_7,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import LocalEnvironmentPreflight
checker = LocalEnvironmentPreflight()
# Deliberately missing executable
report = checker.check({"executables": {"ollama": False}, "config": {}})
# Deliberate wrong assertion: asserting preflight passed
assert report.status == "PASS", "Intentional failure check for preflight pass"
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
        "Module03/applied-labs/r04-t056",
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
        "task_id": "R04-T056",
        "issue": 56,
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
