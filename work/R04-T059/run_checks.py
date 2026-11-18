#!/usr/bin/env python3
"""
Verification check runner for R04-T059.
Validates AI Agent Capability Negotiation and Feature Gating:
1. Canonical negotiation: Client {tools, resources} and Server {tools, prompts} negotiates {tools}.
2. Canonical dispatch: Calling 'tools' is permitted and dispatched.
3. Canonical gating: Calling 'resources' is rejected before dispatch with actionable diagnostic.
4. Strict mode: Unnegotiated capability raises UnnegotiatedCapabilityError.
5. Three controlled configurations compared across metrics with 100% correctness.
6. Deliberate failure verification (must exit non-zero).
7. Unittest discovery execution in a fresh process.
8. Writes evidence.json and test_output.txt to work/R04-T059/.
"""

import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

# Add example module directory to path
MODULE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Module06", "applied-labs", "r04-t059")
)
sys.path.insert(0, MODULE_DIR)

from example import (
    BenchmarkMetrics,
    CapabilityDispatcher,
    CapabilityNegotiator,
    ConfigurationProfile,
    DispatchResult,
    NegotiationResult,
    UnnegotiatedCapabilityError,
    compare_configurations,
    demonstrate_canonical_contract,
    evaluate_configuration,
    explain_mapping,
    get_standard_configurations,
    identify_unestablished_behaviors,
)


def run_contract_checks() -> List[Dict[str, Any]]:
    """Execute contract checks and record inputs, expected, and actual results."""
    checks = []

    # Check 1: Canonical Capability Negotiation
    client_caps = {"tools", "resources"}
    server_caps = {"tools", "prompts"}
    neg = CapabilityNegotiator.negotiate(client_caps, server_caps)

    pass_1 = (
        neg.negotiated_capabilities == {"tools"}
        and neg.client_unmatched == {"resources"}
        and neg.server_unmatched == {"prompts"}
        and abs(neg.capability_retention_ratio - 0.5) < 1e-6
    )
    status_1 = "PASSED" if pass_1 else "FAILED"
    if status_1 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "canonical_capability_negotiation",
        "inputs": {
            "client_capabilities": sorted(list(client_caps)),
            "server_capabilities": sorted(list(server_caps)),
        },
        "expected": {
            "negotiated_capabilities": ["tools"],
            "client_unmatched": ["resources"],
            "server_unmatched": ["prompts"],
            "capability_retention_ratio": 0.5,
        },
        "actual": {
            "negotiated_capabilities": sorted(list(neg.negotiated_capabilities)),
            "client_unmatched": sorted(list(neg.client_unmatched)),
            "server_unmatched": sorted(list(neg.server_unmatched)),
            "capability_retention_ratio": round(neg.capability_retention_ratio, 4),
        },
        "status": status_1,
    })

    # Check 2: Canonical Dispatch of Permitted Capability 'tools'
    dispatcher = CapabilityDispatcher(neg.negotiated_capabilities)
    res_tools = dispatcher.dispatch("tools", "calculator", {"expression": "2+2"})

    pass_2 = (
        res_tools.dispatched is True
        and res_tools.status == "DISPATCHED"
        and res_tools.capability == "tools"
        and res_tools.output is not None
        and res_tools.output.get("status") == "SUCCESS"
    )
    status_2 = "PASSED" if pass_2 else "FAILED"
    if status_2 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "canonical_dispatch_tools_permitted",
        "inputs": {"capability": "tools", "operation": "calculator"},
        "expected": {"status": "DISPATCHED", "dispatched": True, "reason": None},
        "actual": {
            "status": res_tools.status,
            "dispatched": res_tools.dispatched,
            "reason": res_tools.reason,
        },
        "status": status_2,
    })

    # Check 3: Canonical Calling Resources Rejected Before Dispatch
    res_resources = dispatcher.dispatch("resources", "read_file", {"path": "/etc/config"})

    pass_3 = (
        res_resources.dispatched is False
        and res_resources.status == "REJECTED"
        and res_resources.capability == "resources"
        and res_resources.output is None
        and "rejected before dispatch" in (res_resources.reason or "").lower()
        and "not negotiated" in (res_resources.reason or "").lower()
    )
    status_3 = "PASSED" if pass_3 else "FAILED"
    if status_3 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "calling_resources_rejected_before_dispatch",
        "inputs": {"capability": "resources", "operation": "read_file"},
        "expected": {
            "status": "REJECTED",
            "dispatched": False,
            "rejection_contained_phrase": "rejected before dispatch",
        },
        "actual": {
            "status": res_resources.status,
            "dispatched": res_resources.dispatched,
            "rejection_reason": res_resources.reason,
        },
        "status": status_3,
    })

    # Check 4: Strict Mode Rejection Exception
    strict_exception_raised = False
    try:
        dispatcher.dispatch("resources", "read_file", strict=True)
    except UnnegotiatedCapabilityError as e:
        strict_exception_raised = "rejected before dispatch" in str(e).lower()

    status_4 = "PASSED" if strict_exception_raised else "FAILED"
    if status_4 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "strict_mode_unnegotiated_capability_error",
        "inputs": {"capability": "resources", "strict": True},
        "expected": {"exception_raised": True, "exception_type": "UnnegotiatedCapabilityError"},
        "actual": {"exception_raised": strict_exception_raised},
        "status": status_4,
    })

    # Check 5: Three Controlled Configurations Comparison
    comparison = compare_configurations()
    configs = comparison["configurations"]

    all_configs_valid = (
        len(configs) == 3
        and all(c["metrics"]["correctness_rate"] == 1.0 for c in configs.values())
        and all(c["metrics"]["unauthorized_dispatches"] == 0 for c in configs.values())
        and "security_vs_flexibility" in comparison["trade_off_analysis"]
        and "pre_dispatch_gating_guarantee" in comparison["trade_off_analysis"]
    )
    status_5 = "PASSED" if all_configs_valid else "FAILED"
    if status_5 != "PASSED":
        sys.exit(1)

    checks.append({
        "name": "three_controlled_configurations_comparison",
        "inputs": {"configurations_evaluated": list(configs.keys())},
        "expected": {
            "configs_count": 3,
            "all_correctness_rates": 1.0,
            "all_unauthorized_dispatches": 0,
            "trade_off_analysis_present": True,
        },
        "actual": {
            "configs_count": len(configs),
            "correctness_rates": {k: v["metrics"]["correctness_rate"] for k, v in configs.items()},
            "unauthorized_dispatches": {k: v["metrics"]["unauthorized_dispatches"] for k, v in configs.items()},
            "trade_off_analysis_present": True,
        },
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
from example import CapabilityNegotiator, CapabilityDispatcher
# Client {tools, resources}, Server {tools, prompts} negotiates {tools}
neg = CapabilityNegotiator.negotiate({"tools", "resources"}, {"tools", "prompts"})
dispatcher = CapabilityDispatcher(neg.negotiated_capabilities)
# Attempt to call 'resources'
res = dispatcher.dispatch("resources", "read_file")
# Deliberate failure: assert that resources was dispatched!
assert res.dispatched, "Intentional failure check: resources must not be dispatched"
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
        "Module06/applied-labs/r04-t059",
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
        "task_id": "R04-T059",
        "issue": 59,
        "module": "Module06/01.IntroduceAgent.md",
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
