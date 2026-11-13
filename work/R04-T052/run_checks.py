#!/usr/bin/env python3
"""
Verification check runner for R04-T052.
Validates bounded conversation memory contract, runs unittest discovery,
tests deliberate failure handling, and generates evidence in work/R04-T052/.
"""

import copy
import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Module06", "applied-labs", "r04-t052"))
sys.path.insert(0, MODULE_DIR)

from example import BoundedConversationMemory, explain_mapping


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []

    # Check 1: Adding A, B, C, D retains B, C, D in arrival order
    mem = BoundedConversationMemory(capacity=3)
    inputs = ["A", "B", "C", "D"]
    for item in inputs:
        mem.add_record(item)
    actual_records = mem.get_records()
    expected_records = ["B", "C", "D"]
    status_1 = "PASSED" if actual_records == expected_records else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "overflow_retention_a_b_c_d",
        "inputs": inputs,
        "capacity": 3,
        "expected": expected_records,
        "actual": actual_records,
        "status": status_1,
    })

    # Check 2: Mutating returned list does not alter stored memory
    exposed = mem.get_records()
    exposed.append("MUTATED_EXTRA")
    exposed.pop(0)
    exposed.clear()
    stored_after_tamper = mem.get_records()
    status_2 = "PASSED" if stored_after_tamper == ["B", "C", "D"] else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "defensive_copy_immutability",
        "action": "Expose list, append, pop, and clear",
        "expected": ["B", "C", "D"],
        "actual": stored_after_tamper,
        "status": status_2,
    })

    # Check 3: Smallest valid cases (empty memory, single record, capacity 1)
    fresh_mem = BoundedConversationMemory(capacity=3)
    actual_empty = fresh_mem.get_records()
    fresh_mem.add_record("A")
    actual_single = fresh_mem.get_records()
    mem_cap1 = BoundedConversationMemory(capacity=1)
    mem_cap1.add_record("FIRST")
    mem_cap1.add_record("SECOND")
    actual_cap1 = mem_cap1.get_records()

    status_3 = "PASSED" if (
        actual_empty == []
        and actual_single == ["A"]
        and actual_cap1 == ["SECOND"]
    ) else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "smallest_valid_cases",
        "expected": {"empty": [], "single": ["A"], "capacity_1": ["SECOND"]},
        "actual": {"empty": actual_empty, "single": actual_single, "capacity_1": actual_cap1},
        "status": status_3,
    })

    # Check 4: Boundary case (exact capacity vs overflow)
    exact_mem = BoundedConversationMemory(capacity=3)
    exact_mem.add_record("A")
    exact_mem.add_record("B")
    res_c = exact_mem.add_record("C")
    res_d = exact_mem.add_record("D")
    status_4 = "PASSED" if (
        res_c["evicted"] is None
        and res_c["truncated"] is False
        and res_d["evicted"] == "A"
        and res_d["truncated"] is True
    ) else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "boundary_decision_eviction",
        "expected": {"at_boundary_evicted": None, "overflow_evicted": "A"},
        "actual": {"at_boundary_evicted": res_c["evicted"], "overflow_evicted": res_d["evicted"]},
        "status": status_4,
    })

    # Check 5: Invalid cases rejection
    invalid_rejections = []
    try:
        BoundedConversationMemory(capacity=0)
        invalid_rejections.append("capacity_0_not_rejected")
    except ValueError:
        invalid_rejections.append("capacity_0_rejected")

    try:
        mem.add_record(None)
        invalid_rejections.append("none_not_rejected")
    except ValueError:
        invalid_rejections.append("none_rejected")

    try:
        mem.add_record("   ")
        invalid_rejections.append("empty_whitespace_not_rejected")
    except ValueError:
        invalid_rejections.append("empty_whitespace_rejected")

    status_5 = "PASSED" if all("not_rejected" not in r for r in invalid_rejections) else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "invalid_cases_rejection",
        "expected": ["capacity_0_rejected", "none_rejected", "empty_whitespace_rejected"],
        "actual": invalid_rejections,
        "status": status_5,
    })

    # Check 6: Boundary decision explanation and concept mapping
    decision = mem.get_boundary_decision()
    mapping = explain_mapping()
    has_policy = decision.get("policy") == "FIFO_SLIDING_WINDOW"
    has_mapping = len(mapping) >= 5
    status_6 = "PASSED" if (has_policy and has_mapping) else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "boundary_decision_and_mapping",
        "expected": {"policy": "FIFO_SLIDING_WINDOW", "has_concept_mapping": True},
        "actual": {"policy": decision.get("policy"), "has_concept_mapping": has_mapping},
        "status": status_6,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import BoundedConversationMemory
mem = BoundedConversationMemory(capacity=3)
mem.add_record("A")
mem.add_record("B")
mem.add_record("C")
mem.add_record("D")
# Deliberate failure: assert incorrect retained records
assert mem.get_records() == ["WRONG", "PREDICTION"], "Intentional failure check"
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
        "Module06/applied-labs/r04-t052",
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
        "task_id": "R04-T052",
        "issue": 52,
        "module": "Module06/03.IntroduceMCP.md",
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
