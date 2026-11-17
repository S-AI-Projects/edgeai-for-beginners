#!/usr/bin/env python3
"""
Verification check runner for R04-T057.
Validates Gemma Synthetic Model Manifest Selection:
1. Canonical contract: Fixture A (RAM4/context2048), B (RAM8/context4096), budget RAM6 and context1024 admits only A.
2. Explicit reason reported for excluded entries.
3. Worked input-to-output explanation published.
4. Regression verification.
5. Deliberate failure verification (must exit non-zero).
6. Unittest discovery execution in fresh process.
7. Writes evidence.json and test_output.txt to work/R04-T057/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Module02", "applied-labs", "r04-t057")
)
sys.path.insert(0, MODULE_DIR)

from example import (
    FIXTURE_A,
    FIXTURE_B,
    STANDARD_TEACHING_MANIFEST,
    ModelManifestSelector,
    explain_mapping,
    explain_worked_example,
    identify_unestablished_behaviors,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []
    selector = ModelManifestSelector()

    # Check 1: Canonical Contract: Fixture A (RAM4/context2048), B (RAM8/context4096);
    # budget RAM6 and requested context1024 admits only A.
    manifest = [FIXTURE_A, FIXTURE_B]
    res_1 = selector.select(manifest, ram_budget_gb=6.0, requested_context=1024)

    admitted_only_a = (res_1.admitted_ids == ["fixture-a"])
    excluded_only_b = (res_1.excluded_ids == ["fixture-b"])
    status_1 = "PASSED" if (admitted_only_a and excluded_only_b) else "FAILED"
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

    # Check 2: Explicit failure explanation for excluded model B
    exc_b = res_1.excluded_models[0]
    reason_text = " ".join(exc_b.reasons)
    has_ram_reason = ("Insufficient RAM" in reason_text) and ("8.0" in reason_text) and ("6.0" in reason_text)
    status_2 = "PASSED" if has_ram_reason else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "explicit_failure_reasons_reported",
        "expected": "Insufficient RAM reason specifying model requirement 8.0 GB vs budget 6.0 GB",
        "actual": exc_b.reasons,
        "status": status_2,
    })

    # Check 3: Worked input-to-output explanation published
    explanation = explain_worked_example(manifest, ram_budget_gb=6.0, requested_context=1024)
    has_all_sections = all(
        s in explanation
        for s in [
            "1. INPUT SPECIFICATION",
            "2. STEP-BY-STEP EVALUATION",
            "3. DETERMINISTIC OUTPUT REPORT",
            "4. CONCLUSION & REGRESSION GUARANTEE",
        ]
    )
    status_3 = "PASSED" if has_all_sections else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "worked_input_to_output_explanation_published",
        "expected": "Complete 4-section worked explanation detailing input, steps, output, and regression guarantee",
        "actual": {"sections_present": has_all_sections, "character_length": len(explanation)},
        "status": status_3,
    })

    # Check 4: Exact lesson source recorded
    status_4 = "PASSED" if res_1.lesson_source == "Module02/03.GemmaFamily.md" else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "exact_lesson_source_recorded",
        "expected": "Module02/03.GemmaFamily.md",
        "actual": res_1.lesson_source,
        "status": status_4,
    })

    # Check 5: Unestablished real-service behaviors documented
    unestablished = identify_unestablished_behaviors()
    mapping = explain_mapping()
    status_5 = "PASSED" if (len(unestablished) >= 4 and len(mapping) >= 4) else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "unestablished_behaviors_and_concept_mapping",
        "expected": "At least 4 unestablished behaviors and 4 lesson concept mappings",
        "actual": {"unestablished_count": len(unestablished), "mapping_count": len(mapping)},
        "status": status_5,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import ModelManifestSelector, FIXTURE_A, FIXTURE_B
selector = ModelManifestSelector()
res = selector.select([FIXTURE_A, FIXTURE_B], ram_budget_gb=6.0, requested_context=1024)
# Deliberate failure: assert that fixture-b was admitted under budget RAM 6
assert "fixture-b" in res.admitted_ids, "Intentional failure check for fixture-b admission"
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
        "Module02/applied-labs/r04-t057",
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
        "task_id": "R04-T057",
        "issue": 57,
        "module": "Module02/03.GemmaFamily.md",
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
