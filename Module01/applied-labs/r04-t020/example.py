"""
R04-T020: Installation Preflight Report - Scenario Assessment
Companion applied lab for Module01/03.PracticalImplementationGuide.md.

Demonstrates a read-only environment preflight report:
- Checks explicitly listed executables (e.g. 'python3', 'git') and config fields.
- Does not install packages or contact external network services.
- Complete fixture passes.
- Missing executable and absent config fields give separate actionable failures.
- Secret values (e.g. api_token, api_key) are masked and never printed in plaintext.
- Supplies three applied questions: predict output, diagnose failure, choose boundary policy.

Prerequisites: Python 3 standard library only.
"""

import json
from typing import Any, Dict, List, Optional, Set


SECRET_FIELD_SUBSTRINGS = {"secret", "token", "key", "password", "auth"}


def mask_secret(value: Any) -> str:
    """Masks secret values to prevent credential leakage in logs and reports."""
    if not value:
        return "[EMPTY]"
    return "***"


def is_secret_field(field_name: str) -> bool:
    name_lower = field_name.lower()
    return any(sub in name_lower for sub in SECRET_FIELD_SUBSTRINGS)


class PreflightChecker:
    """
    Read-only preflight checker evaluating environment fixtures against requirements.
    """
    def __init__(
        self,
        required_executables: List[str],
        required_config_fields: List[str]
    ):
        self.required_executables = required_executables
        self.required_config_fields = required_config_fields

    def check(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates environment observation against required executables and configs.
        Safe: masks any secret config values in report output.
        """
        if not isinstance(observation, dict):
            return {
                "status": "FAILED",
                "error": "Observation must be a dictionary.",
                "passed": False,
            }

        available_executables = set(observation.get("executables", []))
        config_data = observation.get("config", {})

        missing_executables = []
        for exe in self.required_executables:
            if exe not in available_executables:
                missing_executables.append({
                    "executable": exe,
                    "code": "EXECUTABLE_NOT_FOUND",
                    "action": f"Install '{exe}' and ensure it is available in PATH.",
                })

        missing_configs = []
        reported_config = {}

        # Safely sanitize all present config fields
        for k, v in config_data.items():
            reported_config[k] = mask_secret(v) if is_secret_field(k) else v

        # Check required fields
        for field in self.required_config_fields:
            if field not in config_data:
                missing_configs.append({
                    "field": field,
                    "code": "CONFIG_FIELD_MISSING",
                    "action": f"Set configuration parameter '{field}' in local environment config.",
                })

        passed = (len(missing_executables) == 0 and len(missing_configs) == 0)

        return {
            "status": "PASSED" if passed else "FAILED",
            "passed": passed,
            "missing_executables": missing_executables,
            "missing_configs": missing_configs,
            "sanitized_config": reported_config,
            "checked_executables": list(available_executables),
        }


# Canonical preflight specification
CANONICAL_REQUIRED_EXECS = ["python3", "git"]
CANONICAL_REQUIRED_CONFIGS = ["cache_dir", "api_token"]


APPLIED_QUESTIONS = [
    {
        "id": "Q1_PREDICT_OUTPUT",
        "type": "predict_output",
        "question": "What is the preflight status and sanitized api_token output for a complete fixture?",
        "answer": {
            "status": "PASSED",
            "api_token": "***"
        },
        "rationale": "All required executables and config keys exist, and secret-containing fields are replaced with '***'."
    },
    {
        "id": "Q2_DIAGNOSE_FAILURE",
        "type": "diagnose_failure",
        "question": "When 'git' is omitted from available executables, what error code and action are reported?",
        "answer": {
            "code": "EXECUTABLE_NOT_FOUND",
            "executable": "git"
        },
        "rationale": "Missing executables trigger EXECUTABLE_NOT_FOUND with an actionable installation recommendation."
    },
    {
        "id": "Q3_BOUNDARY_POLICY",
        "type": "choose_boundary_policy",
        "question": "What policy should be adopted when an optional config field is absent vs mandatory field?",
        "answer": {
            "policy": "STRICT_SCHEMA_ENFORCEMENT",
            "rationale": "Mandatory fields fail immediately with CONFIG_FIELD_MISSING without guessing defaults; optional fields pass."
        },
        "rationale": "Explicit failures prevent silent runtime misconfigurations in edge environments."
    }
]


def run_concept_example() -> Dict[str, Any]:
    """Runs the canonical scenarios and answers."""
    checker = PreflightChecker(CANONICAL_REQUIRED_EXECS, CANONICAL_REQUIRED_CONFIGS)

    # 1. Complete fixture
    complete_obs = {
        "executables": ["python3", "git"],
        "config": {
            "cache_dir": "/var/models/cache",
            "api_token": "super_secret_token_12345",
        }
    }
    complete_res = checker.check(complete_obs)

    # 2. Missing executable fixture
    missing_exe_obs = {
        "executables": ["python3"],
        "config": {
            "cache_dir": "/var/models/cache",
            "api_token": "token_val",
        }
    }
    missing_exe_res = checker.check(missing_exe_obs)

    # 3. Missing config fixture
    missing_cfg_obs = {
        "executables": ["python3", "git"],
        "config": {
            "cache_dir": "/var/models/cache",
        }
    }
    missing_cfg_res = checker.check(missing_cfg_obs)

    # Verify secrets are never in plaintext
    serialized = json.dumps(complete_res)
    secrets_leaked = "super_secret_token_12345" in serialized

    return {
        "complete_passed": complete_res["passed"],
        "complete_status": complete_res["status"],
        "token_masked": complete_res["sanitized_config"]["api_token"] == "***",
        "secrets_leaked": secrets_leaked,
        "missing_exe_code": missing_exe_res["missing_executables"][0]["code"],
        "missing_cfg_code": missing_cfg_res["missing_configs"][0]["code"],
        "applied_questions": APPLIED_QUESTIONS,
    }


if __name__ == "__main__":
    res = run_concept_example()
    print("=== Installation Preflight Report ===")
    print(f"Complete fixture passed: {res['complete_passed']} (status={res['complete_status']})")
    print(f"Secret token masked: {res['token_masked']} (secrets leaked: {res['secrets_leaked']})")
    print(f"Missing executable code: {res['missing_exe_code']}")
    print(f"Missing config code: {res['missing_cfg_code']}")
    print("\n--- Applied Questions Assessment ---")
    for q in res["applied_questions"]:
        print(f"[{q['id']}] {q['question']}")
        print(f"  Answer: {q['answer']}")
        print(f"  Rationale: {q['rationale']}")

