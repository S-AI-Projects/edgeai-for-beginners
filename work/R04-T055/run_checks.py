#!/usr/bin/env python3
"""
Verification check runner for R04-T055.
Validates Qualcomm QNN platform preflight check, refactoring equivalence,
runs unittest discovery, tests deliberate failure handling, and generates evidence in work/R04-T055/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Module04", "applied-labs", "r04-t055"))
sys.path.insert(0, MODULE_DIR)

from example import (
    QNN_LESSON_REQUIREMENTS,
    BaselineQNNPlatformChecker,
    PlatformRuleValidator,
    RefactoredQNNPlatformChecker,
    explain_mapping,
    prove_equivalence,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []

    matching_fixture = {
        "os": "Linux",
        "architecture": "aarch64",
        "backend": "htp",
        "capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
    }
    changed_arch_fixture = {
        "os": "Linux",
        "architecture": "x86_64",
        "backend": "htp",
        "capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
    }
    missing_caps_fixture = {
        "os": "Linux",
        "architecture": "aarch64",
        "backend": "htp",
        "capabilities": ["QNN_SDK"],
    }

    checker = RefactoredQNNPlatformChecker()

    # Check 1: Matching fixture passes
    res_1 = checker.check(matching_fixture)
    status_1 = "PASSED" if (res_1["compatible"] and res_1["status"] == "PASS" and not res_1["mismatches"]) else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "matching_fixture_passes",
        "inputs": matching_fixture,
        "expected": {"compatible": True, "status": "PASS", "mismatches": [], "missing_capabilities": []},
        "actual": {"compatible": res_1["compatible"], "status": res_1["status"], "mismatches": res_1["mismatches"], "missing_capabilities": res_1["missing_capabilities"]},
        "status": status_1,
    })

    # Check 2: Changed architecture fails with exact mismatched field
    res_2 = checker.check(changed_arch_fixture)
    expected_mismatch = [{"field": "architecture", "expected": "aarch64", "actual": "x86_64"}]
    status_2 = "PASSED" if (not res_2["compatible"] and res_2["mismatches"] == expected_mismatch) else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "changed_architecture_fails_mismatch_reported",
        "inputs": changed_arch_fixture,
        "expected": {"compatible": False, "status": "FAIL", "mismatches": expected_mismatch},
        "actual": {"compatible": res_2["compatible"], "status": res_2["status"], "mismatches": res_2["mismatches"]},
        "status": status_2,
    })

    # Check 3: Missing capability is reported rather than guessed
    res_3 = checker.check(missing_caps_fixture)
    expected_missing = ["Hexagon_NPU", "HTP_Backend"]
    status_3 = "PASSED" if (
        not res_3["compatible"]
        and sorted(res_3["missing_capabilities"]) == sorted(expected_missing)
    ) else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "missing_capabilities_reported",
        "inputs": missing_caps_fixture,
        "expected": {"compatible": False, "missing_capabilities": expected_missing},
        "actual": {"compatible": res_3["compatible"], "missing_capabilities": res_3["missing_capabilities"]},
        "status": status_3,
    })

    # Check 4: Refactoring equivalence between Baseline and Refactored
    proof = prove_equivalence([matching_fixture, changed_arch_fixture, missing_caps_fixture])
    status_4 = "PASSED" if proof["all_equivalent"] else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "refactoring_equivalence_baseline_vs_refactored",
        "expected": {"all_equivalent": True},
        "actual": {"all_equivalent": proof["all_equivalent"], "total_fixtures": proof["total_fixtures"]},
        "status": status_4,
    })

    # Check 5: Exact lesson requirement recorded
    status_5 = "PASSED" if res_1["lesson_source"] == "Module04/07.QualcommQNN.md" else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "exact_lesson_requirement_recorded",
        "expected": "Module04/07.QualcommQNN.md",
        "actual": res_1["lesson_source"],
        "status": status_5,
    })

    # Check 6: Unestablished real-service behaviors documented
    unestablished = RefactoredQNNPlatformChecker.identify_unestablished_behaviors()
    mapping = explain_mapping()
    status_6 = "PASSED" if (len(unestablished) >= 4 and len(mapping) >= 5) else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "unestablished_behaviors_documented",
        "expected": "At least 4 unestablished behaviors and 5 concept mappings",
        "actual": {"unestablished_count": len(unestablished), "mapping_count": len(mapping)},
        "status": status_6,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import RefactoredQNNPlatformChecker
checker = RefactoredQNNPlatformChecker()
res = checker.check({
    "os": "Linux",
    "architecture": "x86_64",
    "backend": "htp",
    "capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
})
# Deliberate failure: assert that changed architecture passed
assert res["status"] == "PASS", "Intentional failure check"
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
        "Module04/applied-labs/r04-t055",
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
        "task_id": "R04-T055",
        "issue": 55,
        "module": "Module04/07.QualcommQNN.md",
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
