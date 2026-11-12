#!/usr/bin/env python3
"""
Verification check runner for R04-T051.
Validates the token budget preflight contract, runs unittest discovery,
tests deliberate failure handling, and generates evidence in work/R04-T051/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Module03", "applied-labs", "r04-t051"))
sys.path.insert(0, MODULE_DIR)

from example import TokenBudgetPreflight, explain_mapping


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute each contract requirement and record input, expected, and actual."""
    checks = []

    # Check 1: Overflow truncation
    checker_3 = TokenBudgetPreflight(budget=3)
    prompt_overflow = "one two three four"
    actual_1 = checker_3.check(prompt_overflow)
    expected_1 = {
        "retained_tokens": ["one", "two", "three"],
        "retained_count": 3,
        "removed_tokens": ["four"],
        "removed_count": 1,
        "truncated": True,
        "tokenizer_note": "Teaching approximation (whitespace tokenization), not the model's real tokenizer",
    }
    status_1 = "PASSED" if (
        actual_1["retained_tokens"] == expected_1["retained_tokens"]
        and actual_1["retained_count"] == expected_1["retained_count"]
        and actual_1["removed_tokens"] == expected_1["removed_tokens"]
        and actual_1["removed_count"] == expected_1["removed_count"]
        and actual_1["truncated"] == expected_1["truncated"]
        and actual_1["tokenizer_note"] == expected_1["tokenizer_note"]
    ) else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "overflow_truncation",
        "input": {"prompt": prompt_overflow, "budget": 3},
        "expected": expected_1,
        "actual": actual_1,
        "status": status_1,
    })

    # Check 2: Empty input
    prompt_empty = ""
    actual_2 = checker_3.check(prompt_empty)
    expected_2 = {
        "retained_tokens": [],
        "retained_count": 0,
        "removed_tokens": [],
        "removed_count": 0,
        "truncated": False,
    }
    status_2 = "PASSED" if (
        actual_2["retained_tokens"] == expected_2["retained_tokens"]
        and actual_2["retained_count"] == expected_2["retained_count"]
        and actual_2["removed_tokens"] == expected_2["removed_tokens"]
        and actual_2["removed_count"] == expected_2["removed_count"]
        and actual_2["truncated"] == expected_2["truncated"]
    ) else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "empty_input_retains_none",
        "input": {"prompt": prompt_empty, "budget": 3},
        "expected": expected_2,
        "actual": actual_2,
        "status": status_2,
    })

    # Check 3: Whitespace only
    prompt_whitespace = "   \t\n   "
    actual_3 = checker_3.check(prompt_whitespace)
    expected_3 = {
        "retained_tokens": [],
        "retained_count": 0,
        "removed_tokens": [],
        "removed_count": 0,
        "truncated": False,
    }
    status_3 = "PASSED" if (
        actual_3["retained_tokens"] == expected_3["retained_tokens"]
        and actual_3["retained_count"] == expected_3["retained_count"]
        and actual_3["truncated"] == expected_3["truncated"]
    ) else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "whitespace_only_retains_none",
        "input": {"prompt": prompt_whitespace, "budget": 3},
        "expected": expected_3,
        "actual": actual_3,
        "status": status_3,
    })

    # Check 4: Negative budget rejection
    actual_4 = "None"
    try:
        TokenBudgetPreflight(budget=-1)
        status_4 = "FAILED"
    except ValueError as e:
        actual_4 = f"ValueError: {e}"
        status_4 = "PASSED" if "cannot be negative" in str(e) else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "reject_negative_budget",
        "input": {"budget": -1},
        "expected": "ValueError: Token budget cannot be negative: -1",
        "actual": actual_4,
        "status": status_4,
    })

    # Check 5: Exact capacity match
    prompt_exact = "one two three"
    actual_5 = checker_3.check(prompt_exact)
    expected_5 = {
        "retained_tokens": ["one", "two", "three"],
        "retained_count": 3,
        "removed_tokens": [],
        "removed_count": 0,
        "truncated": False,
    }
    status_5 = "PASSED" if (
        actual_5["retained_tokens"] == expected_5["retained_tokens"]
        and actual_5["retained_count"] == expected_5["retained_count"]
        and actual_5["removed_count"] == expected_5["removed_count"]
        and actual_5["truncated"] == expected_5["truncated"]
    ) else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "exact_capacity_boundary",
        "input": {"prompt": prompt_exact, "budget": 3},
        "expected": expected_5,
        "actual": actual_5,
        "status": status_5,
    })

    # Check 6: Teaching approximation label
    prompt_label = "test"
    actual_6 = checker_3.check(prompt_label)
    note = actual_6["tokenizer_note"]
    status_6 = "PASSED" if (
        "teaching approximation" in note.lower()
        and "not the model's real tokenizer" in note.lower()
    ) else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "teaching_approximation_label",
        "input": {"prompt": prompt_label, "budget": 3},
        "expected": "Teaching approximation (whitespace tokenization), not the model's real tokenizer",
        "actual": note,
        "status": status_6,
    })

    # Check 7: Concept mapping completeness
    mapping = explain_mapping()
    all_keys_mapped = all(k in mapping for k in actual_1.keys())
    status_7 = "PASSED" if all_keys_mapped else "FAILED"
    if status_7 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "concept_mapping_coverage",
        "input": list(actual_1.keys()),
        "expected": "All report keys mapped to containerized cloud concepts",
        "actual": mapping,
        "status": status_7,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Demonstrate that an intentional faulty assertion produces a non-zero exit."""
    code = """
import sys
from example import TokenBudgetPreflight
checker = TokenBudgetPreflight(budget=3)
res = checker.check("one two three four")
# Deliberate failure: assert false result
assert res["retained_tokens"] == ["intentional_mismatch"], "Deliberate wrong result check"
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
        "Module03/applied-labs/r04-t051",
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
        "task_id": "R04-T051",
        "issue": 6,
        "module": "Module03/03.DeployingSLMinCloud.md",
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
