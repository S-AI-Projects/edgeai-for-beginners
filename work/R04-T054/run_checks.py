#!/usr/bin/env python3
"""
Verification check runner for R04-T054.
Validates model-manifest selection contract, offline adapter decoupling,
runs unittest discovery, tests deliberate failure handling, and generates evidence in work/R04-T054/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Module02", "applied-labs", "r04-t054"))
sys.path.insert(0, MODULE_DIR)

from example import (
    DEFAULT_SYNTHETIC_MANIFEST,
    ModelManifestSelector,
    SyntheticManifestAdapter,
    explain_mapping,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []

    adapter = SyntheticManifestAdapter()
    selector = ModelManifestSelector(manifest_provider=adapter)

    # Check 1: Primary Contract Fixture (RAM 6GB, context 1024 admits only A)
    res_1 = selector.select(available_ram_gb=6.0, requested_context=1024)
    expected_admitted_1 = ["fixture-a"]
    expected_excluded_1 = ["fixture-b"]

    status_1 = "PASSED" if (
        res_1["admitted_ids"] == expected_admitted_1
        and res_1["excluded_ids"] == expected_excluded_1
        and any("Insufficient RAM" in r for r in res_1["excluded"][0]["reasons"])
    ) else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "primary_contract_admission",
        "inputs": {"available_ram_gb": 6.0, "requested_context": 1024},
        "expected": {"admitted_ids": expected_admitted_1, "excluded_ids": expected_excluded_1},
        "actual": {"admitted_ids": res_1["admitted_ids"], "excluded_ids": res_1["excluded_ids"]},
        "status": status_1,
    })

    # Check 2: Exact RAM boundary (RAM 4GB, context 1024 admits A)
    res_2 = selector.select(available_ram_gb=4.0, requested_context=1024)
    status_2 = "PASSED" if "fixture-a" in res_2["admitted_ids"] else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "exact_ram_boundary",
        "inputs": {"available_ram_gb": 4.0, "requested_context": 1024},
        "expected": {"admitted_contains": "fixture-a"},
        "actual": {"admitted_ids": res_2["admitted_ids"]},
        "status": status_2,
    })

    # Check 3: Context overflow excludes A (RAM 6GB, context 2049)
    res_3 = selector.select(available_ram_gb=6.0, requested_context=2049)
    status_3 = "PASSED" if (
        "fixture-a" in res_3["excluded_ids"]
        and any("context" in r.lower() for exc in res_3["excluded"] if exc["id"] == "fixture-a" for r in exc["reasons"])
    ) else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "context_overflow_exclusion",
        "inputs": {"available_ram_gb": 6.0, "requested_context": 2049},
        "expected": {"excluded_contains": "fixture-a"},
        "actual": {"excluded_ids": res_3["excluded_ids"]},
        "status": status_3,
    })

    # Check 4: Adapter decoupling and defensive copying
    copy_1 = adapter()
    copy_1.clear()
    copy_2 = adapter()
    status_4 = "PASSED" if len(copy_2) == 2 else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "adapter_defensive_copying",
        "expected": {"manifest_length_preserved": 2},
        "actual": {"manifest_length": len(copy_2)},
        "status": status_4,
    })

    # Check 5: Invalid inputs rejection
    rejections = []
    try:
        selector.select(available_ram_gb=-1.0, requested_context=1024)
        rejections.append("negative_ram_not_rejected")
    except ValueError:
        rejections.append("negative_ram_rejected")

    try:
        selector.select(available_ram_gb=6.0, requested_context=0)
        rejections.append("zero_context_not_rejected")
    except ValueError:
        rejections.append("zero_context_rejected")

    status_5 = "PASSED" if all("not_rejected" not in r for r in rejections) else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "invalid_parameters_rejection",
        "expected": ["negative_ram_rejected", "zero_context_rejected"],
        "actual": rejections,
        "status": status_5,
    })

    # Check 6: Unestablished real-service behaviors documented
    unestablished = ModelManifestSelector.identify_unestablished_behaviors()
    mapping = explain_mapping()
    status_6 = "PASSED" if (len(unestablished) >= 4 and len(mapping) >= 5) else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "unestablished_behaviors_and_mapping",
        "expected": "At least 4 unestablished behaviors and 5 concept mappings",
        "actual": {
            "unestablished_count": len(unestablished),
            "mapping_count": len(mapping),
        },
        "status": status_6,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import ModelManifestSelector
selector = ModelManifestSelector()
# Deliberate failure: assert incorrect admitted ID
res = selector.select(available_ram_gb=6.0, requested_context=1024)
assert res["admitted_ids"] == ["fixture-b"], "Intentional failure check"
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
        "Module02/applied-labs/r04-t054",
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
        "task_id": "R04-T054",
        "issue": 54,
        "module": "Module02/05.mumodel.md",
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
