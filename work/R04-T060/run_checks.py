#!/usr/bin/env python3
"""
Verification check runner for R04-T060.
Validates Microsoft Phi Model Family Synthetic Manifest Selection & Applied Questions:
1. Canonical contract: Budget RAM 6 GB and requested context 1024 admits only Fixture A.
2. Explicit actionable reason reported for excluded Fixture B (insufficient RAM 8.0 GB vs 6.0 GB).
3. Applied Question 1 (Predict an output) verified.
4. Applied Question 2 (Diagnose a failure) verified.
5. Applied Question 3 (Choose a boundary policy) verified.
6. Unestablished behaviors and concept mapping integrity.
7. Deliberate failure verification (must exit non-zero).
8. Unittest discovery execution in fresh process.
9. Writes evidence.json and test_output.txt to work/R04-T060/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Module02", "applied-labs", "r04-t060")
)
sys.path.insert(0, MODULE_DIR)

from example import (
    FIXTURE_A,
    FIXTURE_B,
    STANDARD_TEACHING_MANIFEST,
    AppliedQuestion,
    ExclusionReport,
    ModelEntry,
    PhiModelManifestSelector,
    SelectionResult,
    check_choose_boundary_policy,
    check_diagnose_failure,
    check_predict_output,
    explain_mapping,
    get_applied_questions,
    identify_unestablished_behaviors,
    verify_all_applied_questions,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []
    selector = PhiModelManifestSelector()

    # Check 1: Canonical Manifest Selection (Budget RAM 6 GB, Context 1024 admits only Fixture A)
    res_1 = selector.select(STANDARD_TEACHING_MANIFEST, ram_budget_gb=6.0, requested_context=1024)
    admitted_only_a = (res_1.admitted_ids == ["fixture-a"])
    excluded_only_b = (res_1.excluded_ids == ["fixture-b"])
    pass_1 = admitted_only_a and excluded_only_b
    status_1 = "PASSED" if pass_1 else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "canonical_manifest_selection_admits_only_a",
        "inputs": {
            "manifest": [FIXTURE_A.to_dict(), FIXTURE_B.to_dict()],
            "ram_budget_gb": 6.0,
            "requested_context": 1024,
        },
        "expected": {
            "admitted_ids": ["fixture-a"],
            "excluded_ids": ["fixture-b"],
        },
        "actual": {
            "admitted_ids": res_1.admitted_ids,
            "excluded_ids": res_1.excluded_ids,
        },
        "status": status_1,
    })

    # Check 2: Explicit Actionable Failure Reason for Fixture B
    exc_b = res_1.excluded_models[0]
    reason_str = " ".join(exc_b.reasons)
    pass_2 = ("Insufficient RAM" in reason_str) and ("8.0 GB" in reason_str) and ("6.0 GB" in reason_str)
    status_2 = "PASSED" if pass_2 else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "fixture_b_actionable_failure_reported",
        "inputs": {"model_id": "fixture-b", "required_ram": 8.0, "budget_ram": 6.0},
        "expected": "Insufficient RAM: model requires 8.0 GB, but host budget is 6.0 GB.",
        "actual": exc_b.reasons,
        "status": status_2,
    })

    # Check 3: Applied Question 1 (Predict an output)
    pass_3 = check_predict_output()
    status_3 = "PASSED" if pass_3 else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    questions = get_applied_questions()
    q1 = next(q for q in questions if q.question_id == "Q1_PREDICT_OUTPUT")
    checks.append({
        "name": "applied_question_1_predict_output",
        "question_id": q1.question_id,
        "prompt": q1.prompt,
        "expected_answer": q1.factual_answer,
        "check_passed": pass_3,
        "status": status_3,
    })

    # Check 4: Applied Question 2 (Diagnose a failure)
    pass_4 = check_diagnose_failure()
    status_4 = "PASSED" if pass_4 else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    q2 = next(q for q in questions if q.question_id == "Q2_DIAGNOSE_FAILURE")
    checks.append({
        "name": "applied_question_2_diagnose_failure",
        "question_id": q2.question_id,
        "prompt": q2.prompt,
        "expected_answer": q2.factual_answer,
        "check_passed": pass_4,
        "status": status_4,
    })

    # Check 5: Applied Question 3 (Choose a boundary policy)
    pass_5 = check_choose_boundary_policy()
    status_5 = "PASSED" if pass_5 else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    q3 = next(q for q in questions if q.question_id == "Q3_CHOOSE_BOUNDARY_POLICY")
    checks.append({
        "name": "applied_question_3_choose_boundary_policy",
        "question_id": q3.question_id,
        "prompt": q3.prompt,
        "expected_answer": q3.factual_answer,
        "check_passed": pass_5,
        "status": status_5,
    })

    # Check 6: Unestablished Behaviors & Concept Mapping
    unest = identify_unestablished_behaviors()
    mapping = explain_mapping()
    pass_6 = (len(unest) >= 5) and (len(mapping) >= 5)
    status_6 = "PASSED" if pass_6 else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "unestablished_behaviors_and_concept_mapping",
        "expected": "At least 5 unestablished behaviors and 5 lesson concept mappings",
        "actual": {"unestablished_count": len(unest), "mapping_count": len(mapping)},
        "status": status_6,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import PhiModelManifestSelector, STANDARD_TEACHING_MANIFEST
selector = PhiModelManifestSelector()
res = selector.select(STANDARD_TEACHING_MANIFEST, ram_budget_gb=6.0, requested_context=1024)
# Deliberate failure: assert that fixture-b was admitted under budget RAM 6.0 GB!
assert "fixture-b" in res.admitted_ids, "Intentional failure check: fixture-b must not be admitted"
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
        "Module02/applied-labs/r04-t060",
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
        "task_id": "R04-T060",
        "issue": 60,
        "module": "Module02/01.PhiFamily.md",
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
