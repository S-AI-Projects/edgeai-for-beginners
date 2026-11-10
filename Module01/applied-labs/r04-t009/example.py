#!/usr/bin/env python3
"""
Installation Preflight Report - Evaluation Experiment (R04-T009)
Module 01: Practical Implementation Guide

Concept:
In EdgeAI development, environment preflight routines ensure that target edge
nodes meet toolchain and configuration prerequisites before initiating pipeline
stages. Preflight checks must execute read-only without side effects, separate
tooling errors from config errors, and strictly redact secret tokens.

Focus:
Evaluation experiment comparing three small controlled tier configurations
(Minimal, Standard, Enterprise) measuring verification complexity, failure
isolation, and redaction coverage.
"""

from typing import List, Dict, Any, Tuple
import time

SENSITIVE_KEYWORDS = {"key", "secret", "token", "password", "credential"}


def redact_sensitive_value(key: str, val: Any) -> str:
    """Masks secret values if the key indicates credential data."""
    if any(s in key.lower() for s in SENSITIVE_KEYWORDS):
        return "[REDACTED]"
    return str(val)


class EnvironmentPreflightChecker:
    """
    Read-only environment preflight validator checking executables and configuration parameters.
    """

    def __init__(self, required_executables: List[str], required_config: List[str]):
        self.required_executables = list(required_executables)
        self.required_config = list(required_config)

    def check(
        self, available_executables: Dict[str, bool], config_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes read-only check of provided environment state against requirements.
        """
        executable_failures = []
        config_failures = []
        sanitized_config = {}

        # 1. Executable checks
        for exe in self.required_executables:
            if not available_executables.get(exe, False):
                executable_failures.append(f"MISSING_EXECUTABLE: '{exe}' was not found on system PATH.")

        # 2. Config parameter checks & secret masking
        for key in self.required_config:
            if key not in config_dict:
                config_failures.append(f"ABSENT_CONFIG: Key '{key}' missing from configuration.")
            else:
                sanitized_config[key] = redact_sensitive_value(key, config_dict[key])

        all_failures = executable_failures + config_failures
        passed = len(all_failures) == 0

        return {
            "passed": passed,
            "executable_failures": executable_failures,
            "config_failures": config_failures,
            "all_failures": all_failures,
            "sanitized_config": sanitized_config,
            "checks_performed": len(self.required_executables) + len(self.required_config),
        }


def run_evaluation_experiment() -> Dict[str, Any]:
    """
    Compares three small controlled configurations across quantitative metrics:
    - Minimal (2 tools, 2 configs)
    - Standard (4 tools, 4 configs)
    - Enterprise (6 tools, 6 configs)
    """
    profiles = {
        "tier_minimal": {
            "execs": ["python3", "git"],
            "config": ["model_dir", "api_key"],
        },
        "tier_standard": {
            "execs": ["python3", "git", "curl", "cmake"],
            "config": ["model_dir", "api_key", "endpoint", "log_level"],
        },
        "tier_enterprise": {
            "execs": ["python3", "git", "curl", "cmake", "docker", "foundry"],
            "config": ["model_dir", "api_key", "endpoint", "log_level", "cache_limit_gb", "telemetry_token"],
        },
    }

    # Simulated environment: all present except 'docker' and 'telemetry_token'
    sim_execs = {
        "python3": True, "git": True, "curl": True, "cmake": True, "foundry": True, "docker": False
    }
    sim_config = {
        "model_dir": "/opt/edge/models",
        "api_key": "raw_secret_key_123",
        "endpoint": "http://127.0.0.1:8080",
        "log_level": "INFO",
        "cache_limit_gb": 16,
    }

    experiment_results = {}

    for name, p in profiles.items():
        checker = EnvironmentPreflightChecker(p["execs"], p["config"])
        t0 = time.perf_counter()
        result = checker.check(sim_execs, sim_config)
        elapsed_us = (time.perf_counter() - t0) * 1_000_000

        experiment_results[name] = {
            "checks_count": result["checks_performed"],
            "passed": result["passed"],
            "executable_failure_count": len(result["executable_failures"]),
            "config_failure_count": len(result["config_failures"]),
            "duration_microseconds": round(elapsed_us, 2),
            "secrets_redacted": any("[REDACTED]" in str(v) for v in result["sanitized_config"].values()),
        }

    return experiment_results


def run_demo() -> None:
    print("=== Module 01: Preflight Evaluation Experiment Demo ===")
    results = run_evaluation_experiment()
    print("Tier Comparison Experiment Results:")
    for tier, data in results.items():
        print(f"  {tier}: Checks={data['checks_count']}, Passed={data['passed']}, Failures=(exe:{data['executable_failure_count']}, cfg:{data['config_failure_count']})")


if __name__ == "__main__":
    run_demo()
