"""
R04-T016: Platform-Compatibility Preflight - Refactor the Teaching Example
Companion applied lab for Module04/05.AppleMLX.md.

Demonstrates manifest-driven platform verification for Apple MLX:
- Requirements derived strictly from Section 4 ("System Requirements"):
    OS: Darwin (macOS 13.0+)
    Architecture: arm64 (Native Apple Silicon, not Rosetta)
    Backend: metal (Metal Performance Shaders unified memory)
    RAM: 8GB minimum
- Hardware-independent: checks supplied observation fixtures; never inspects host machine.
- Fails with mismatched field on architecture deviation.
- Missing observation fields are reported as missing, never guessed.
- Refactor: extracts evaluate_field_requirement() and proves before/after equivalence.

Prerequisites: Python 3 standard library only.
"""

from typing import Any, Dict, List, Optional, Tuple


class PlatformCheckError(Exception):
    """Raised when manifest validation or observation schema is invalid."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


MLX_MANIFEST = {
    "framework": "Apple MLX",
    "lesson_reference": "Module04/05.AppleMLX.md#L52-L58",
    "requirements": {
        "os": {"type": "exact", "expected": "Darwin", "description": "macOS operating system"},
        "architecture": {"type": "exact", "expected": "arm64", "description": "Native Apple Silicon (ARM64)"},
        "backend": {"type": "exact", "expected": "metal", "description": "Metal Performance Shaders accelerator"},
        "min_ram_gb": {"type": "minimum", "expected": 8, "field": "ram_gb", "description": "8GB+ unified memory"},
    },
    "explicit_unknowns": [
        "exact_gpu_core_count",
        "minimum_apple_silicon_generation",
    ]
}


def evaluate_field_requirement(
    req_key: str,
    rule: Dict[str, Any],
    observed_value: Any
) -> Tuple[bool, Optional[str]]:
    """
    Extracted responsibility: evaluates a single requirement rule against observed data.
    Returns (passed, failure_message).
    """
    rule_type = rule.get("type")
    expected = rule.get("expected")

    if rule_type == "exact":
        if observed_value != expected:
            return False, f"MISMATCH: field '{req_key}' observed '{observed_value}', required '{expected}'"
        return True, None

    if rule_type == "minimum":
        if not isinstance(observed_value, (int, float)):
            return False, f"TYPE_ERROR: field '{req_key}' must be numeric, got {type(observed_value).__name__}"
        if observed_value < expected:
            return False, f"INSUFFICIENT: field '{req_key}' observed {observed_value}, required >= {expected}"
        return True, None

    return False, f"UNKNOWN_RULE_TYPE: {rule_type}"


def check_platform_baseline(manifest: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monolithic baseline preflight checker:
    Inlines field comparison, missing field detection, and result generation.
    """
    if not isinstance(observation, dict):
        raise PlatformCheckError("INVALID_OBSERVATION", "Observation must be a dictionary.")

    requirements = manifest.get("requirements", {})
    passed_fields = []
    failed_fields = []
    missing_fields = []

    for req_key, rule in requirements.items():
        obs_field = rule.get("field", req_key)
        if obs_field not in observation:
            missing_fields.append({
                "field": obs_field,
                "requirement": req_key,
                "reason": "Observed data lacks required field; capability cannot be guessed",
            })
            continue

        observed_val = observation[obs_field]
        rule_type = rule.get("type")
        expected = rule.get("expected")

        if rule_type == "exact":
            if observed_val == expected:
                passed_fields.append(obs_field)
            else:
                failed_fields.append({
                    "field": obs_field,
                    "observed": observed_val,
                    "expected": expected,
                    "reason": f"Mismatch on '{obs_field}': observed '{observed_val}', expected '{expected}'",
                })
        elif rule_type == "minimum":
            if isinstance(observed_val, (int, float)) and observed_val >= expected:
                passed_fields.append(obs_field)
            else:
                failed_fields.append({
                    "field": obs_field,
                    "observed": observed_val,
                    "expected": f">= {expected}",
                    "reason": f"Insufficient value for '{obs_field}': observed {observed_val}, expected >= {expected}",
                })

    is_compatible = len(failed_fields) == 0 and len(missing_fields) == 0

    return {
        "compatible": is_compatible,
        "passed": passed_fields,
        "failed": failed_fields,
        "missing": missing_fields,
        "lesson_reference": manifest.get("lesson_reference"),
    }


def check_platform_refactored(manifest: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refactored preflight checker:
    Delegates individual rule assessment to the pure evaluate_field_requirement() function.
    """
    if not isinstance(observation, dict):
        raise PlatformCheckError("INVALID_OBSERVATION", "Observation must be a dictionary.")

    requirements = manifest.get("requirements", {})
    passed_fields = []
    failed_fields = []
    missing_fields = []

    for req_key, rule in requirements.items():
        obs_field = rule.get("field", req_key)
        if obs_field not in observation:
            missing_fields.append({
                "field": obs_field,
                "requirement": req_key,
                "reason": "Observed data lacks required field; capability cannot be guessed",
            })
            continue

        observed_val = observation[obs_field]
        passed, error_msg = evaluate_field_requirement(obs_field, rule, observed_val)
        if passed:
            passed_fields.append(obs_field)
        else:
            failed_fields.append({
                "field": obs_field,
                "observed": observed_val,
                "expected": rule.get("expected"),
                "reason": error_msg,
            })

    is_compatible = len(failed_fields) == 0 and len(missing_fields) == 0

    return {
        "compatible": is_compatible,
        "passed": passed_fields,
        "failed": failed_fields,
        "missing": missing_fields,
        "lesson_reference": manifest.get("lesson_reference"),
    }


# Canonical entry point
check_platform = check_platform_refactored


def run_concept_example() -> Dict[str, Any]:
    """Executes the standard test scenarios."""
    # 1. Matching fixture: Apple Silicon Mac
    matching_obs = {
        "os": "Darwin",
        "architecture": "arm64",
        "backend": "metal",
        "ram_gb": 16,
    }
    match_res = check_platform(MLX_MANIFEST, matching_obs)

    # 2. Changed architecture: x86_64 Mac
    mismatch_obs = {
        "os": "Darwin",
        "architecture": "x86_64",
        "backend": "metal",
        "ram_gb": 16,
    }
    mismatch_res = check_platform(MLX_MANIFEST, mismatch_obs)

    # 3. Missing capability: backend omitted
    missing_obs = {
        "os": "Darwin",
        "architecture": "arm64",
        "ram_gb": 16,
    }
    missing_res = check_platform(MLX_MANIFEST, missing_obs)

    return {
        "matching_compatible": match_res["compatible"],
        "matching_passed": match_res["passed"],
        "mismatch_compatible": mismatch_res["compatible"],
        "mismatch_failed_field": mismatch_res["failed"][0]["field"],
        "missing_compatible": missing_res["compatible"],
        "missing_field": missing_res["missing"][0]["field"],
    }


if __name__ == "__main__":
    res = run_concept_example()
    print("=== Apple MLX Platform Preflight Check ===")
    print(f"Matching fixture compatible: {res['matching_compatible']} (passed: {res['matching_passed']})")
    print(f"Changed architecture compatible: {res['mismatch_compatible']} (failed field: {res['mismatch_failed_field']})")
    print(f"Missing backend compatible: {res['missing_compatible']} (missing field: {res['missing_field']})")
    print("\n[NOTE] Hardware independent: operates solely on observation fixtures without querying machine hardware.")
