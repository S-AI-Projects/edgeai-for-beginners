#!/usr/bin/env python3
"""
Verification check runner for R04-T053.
Validates symmetric signed-int8 quantizer contract, compares two approaches,
runs unittest discovery, tests deliberate failure handling, and generates evidence in work/R04-T053/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Module02", "applied-labs", "r04-t053"))
sys.path.insert(0, MODULE_DIR)

from example import (
    SymmetricInt8Quantizer,
    compare_approaches,
    explain_mapping,
    reference_dequantize,
    reference_pipeline,
    reference_quantize,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []

    # Check 1: Values [-1, 0, 1], scale=0.1 yield [-10, 0, 10] and reconstruct exactly
    quantizer = SymmetricInt8Quantizer(scale=0.1)
    inputs_1 = [-1.0, 0.0, 1.0]
    actual_q_1 = quantizer.quantize_sequence(inputs_1)
    actual_recon_1 = quantizer.dequantize_sequence(actual_q_1)
    expected_q_1 = [-10, 0, 10]
    expected_recon_1 = [-1.0, 0.0, 1.0]

    status_1 = "PASSED" if (actual_q_1 == expected_q_1 and actual_recon_1 == expected_recon_1) else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "exact_reconstruction_contract",
        "inputs": inputs_1,
        "scale": 0.1,
        "expected": {"quantized": expected_q_1, "reconstructed": expected_recon_1},
        "actual": {"quantized": actual_q_1, "reconstructed": actual_recon_1},
        "status": status_1,
    })

    # Check 2: Value 20 clips to 127
    actual_clip_20 = quantizer.quantize(20.0)
    actual_recon_20 = quantizer.dequantize(actual_clip_20)
    status_2 = "PASSED" if (actual_clip_20 == 127 and actual_recon_20 == 12.7) else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "upper_clipping_bound_20",
        "input": 20.0,
        "scale": 0.1,
        "expected": {"quantized": 127, "reconstructed": 12.7},
        "actual": {"quantized": actual_clip_20, "reconstructed": actual_recon_20},
        "status": status_2,
    })

    # Check 3: Value -20 clips to -127
    actual_clip_neg20 = quantizer.quantize(-20.0)
    actual_recon_neg20 = quantizer.dequantize(actual_clip_neg20)
    status_3 = "PASSED" if (actual_clip_neg20 == -127 and actual_recon_neg20 == -12.7) else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "lower_clipping_bound_neg20",
        "input": -20.0,
        "scale": 0.1,
        "expected": {"quantized": -127, "reconstructed": -12.7},
        "actual": {"quantized": actual_clip_neg20, "reconstructed": actual_recon_neg20},
        "status": status_3,
    })

    # Check 4: Nonpositive scale rejection
    rejected_scales = []
    try:
        SymmetricInt8Quantizer(scale=0.0)
        rejected_scales.append("zero_not_rejected")
    except ValueError:
        rejected_scales.append("zero_rejected")

    try:
        SymmetricInt8Quantizer(scale=-0.1)
        rejected_scales.append("negative_not_rejected")
    except ValueError:
        rejected_scales.append("negative_rejected")

    status_4 = "PASSED" if all("not_rejected" not in r for r in rejected_scales) else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "nonpositive_scale_rejection",
        "expected": ["zero_rejected", "negative_rejected"],
        "actual": rejected_scales,
        "status": status_4,
    })

    # Check 5: Compare two approaches (direct vs reference)
    comparison_inputs = [-20.0, -12.7, -1.0, 0.0, 1.0, 12.7, 20.0]
    comp_res = compare_approaches(comparison_inputs, scale=0.1)
    status_5 = "PASSED" if comp_res["all_match"] else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "compare_two_approaches_equivalence",
        "inputs": comparison_inputs,
        "scale": 0.1,
        "expected": {"identical_quantization": True, "identical_reconstruction": True, "all_match": True},
        "actual": {
            "identical_quantization": comp_res["identical_quantization"],
            "identical_reconstruction": comp_res["identical_reconstruction"],
            "all_match": comp_res["all_match"],
        },
        "status": status_5,
    })

    # Check 6: Concept mapping
    mapping = explain_mapping()
    status_6 = "PASSED" if len(mapping) >= 5 else "FAILED"
    if status_6 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "concept_mapping_completeness",
        "expected": "At least 5 core BitNET quantization concepts mapped",
        "actual": mapping,
        "status": status_6,
    })

    return checks


def test_deliberate_failure() -> Dict[str, Any]:
    """Verify that an intentional faulty assertion produces a non-zero exit code."""
    code = """
import sys
from example import SymmetricInt8Quantizer
q = SymmetricInt8Quantizer(scale=0.1)
# Deliberate failure: assert incorrect quantized value for 20
assert q.quantize(20.0) == 999, "Intentional failure check"
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
        "Module02/applied-labs/r04-t053",
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
        "task_id": "R04-T053",
        "issue": 53,
        "module": "Module02/04.BitNETFamily.md",
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
