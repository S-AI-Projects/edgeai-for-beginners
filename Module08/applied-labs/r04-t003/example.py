#!/usr/bin/env python3
"""
Installation Preflight Report - Compare Two Approaches (R04-T003)
Module 08: Foundry Local Setup

Concept:
Before bootstrapping local SLM runtimes (e.g. Foundry Local), a read-only
preflight check verifies necessary tooling (e.g. foundry CLI, python3) and
local configuration variables. Secret credentials must be redacted in all
diagnostics, and failures must clearly distinguish missing binaries from
missing configuration keys.

Focus:
Compares the direct object-oriented validator with a declarative, table-based
reference calculation over identical inputs.
"""

from typing import List, Dict, Any, Set, Tuple

SENSITIVE_KEYWORDS = {"key", "secret", "token", "password", "credential"}


def redact_value(key: str, value: Any) -> str:
    """Masks secret values if the key name indicates sensitive content."""
    key_lower = key.lower()
    if any(secret in key_lower for secret in SENSITIVE_KEYWORDS):
        return "[REDACTED]"
    return str(value)


class InstallationPreflightChecker:
    """
    Direct procedural implementation of environment preflight checking.
    """

    def __init__(self, required_executables: List[str], required_config: List[str]):
        self.required_executables = list(required_executables)
        self.required_config = list(required_config)

    def run_preflight(
        self, available_executables: Dict[str, bool], config_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes read-only environment check without modifying filesystem or network.
        """
        executable_failures = []
        config_failures = []
        reported_config = {}

        # 1. Executable checks
        for exe in self.required_executables:
            if not available_executables.get(exe, False):
                executable_failures.append(f"MISSING_EXECUTABLE: '{exe}' was not found.")

        # 2. Configuration checks & sanitization
        for key in self.required_config:
            if key not in config_dict:
                config_failures.append(f"ABSENT_CONFIG: Key '{key}' is missing from configuration.")
            else:
                reported_config[key] = redact_value(key, config_dict[key])

        all_failures = executable_failures + config_failures
        passed = len(all_failures) == 0

        return {
            "passed": passed,
            "executable_failures": executable_failures,
            "config_failures": config_failures,
            "all_failures": all_failures,
            "diagnostics": reported_config,
        }


def reference_preflight_evaluator(
    required_executables: List[str],
    required_config: List[str],
    available_executables: Dict[str, bool],
    config_dict: Dict[str, Any],
) -> Tuple[bool, List[str], Dict[str, str]]:
    """
    Independent declarative reference implementation using pure set-difference
    and lookup table operations on identical inputs.
    """
    present_execs = {k for k, v in available_executables.items() if v}
    missing_execs = sorted(set(required_executables) - present_execs)
    missing_config = sorted(set(required_config) - set(config_dict.keys()))

    failures = [f"MISSING_EXECUTABLE: '{exe}' was not found." for exe in missing_execs]
    failures.extend([f"ABSENT_CONFIG: Key '{cfg}' is missing from configuration." for cfg in missing_config])

    sanitized = {
        k: redact_value(k, config_dict[k])
        for k in required_config
        if k in config_dict
    }

    return len(failures) == 0, failures, sanitized


def run_demo() -> None:
    print("=== Module 08: Foundry Local Preflight Verification Demo ===")
    req_execs = ["foundry", "python3"]
    req_config = ["model_dir", "api_key"]

    checker = InstallationPreflightChecker(req_execs, req_config)

    # 1. Complete Fixture
    complete_execs = {"foundry": True, "python3": True}
    complete_config = {"model_dir": "/var/models", "api_key": "secret-super-key-123"}
    res1 = checker.run_preflight(complete_execs, complete_config)
    print("\n1. Complete Fixture Result:")
    print(f"Passed: {res1['passed']}, Diagnostics: {res1['diagnostics']}")

    # 2. Missing Executable & Config
    incomplete_execs = {"python3": True}
    incomplete_config = {"api_key": "my-secret"}
    res2 = checker.run_preflight(incomplete_execs, incomplete_config)
    print("\n2. Incomplete Fixture Result:")
    print(f"Passed: {res2['passed']}, Failures: {res2['all_failures']}")


if __name__ == "__main__":
    run_demo()
