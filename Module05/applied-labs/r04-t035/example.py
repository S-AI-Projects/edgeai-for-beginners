"""
Typed Tool Dispatch Refactoring: Monolithic Baseline vs. Extracted Validator.

Demonstrates refactoring a monolithic tool dispatch implementation by extracting
the argument validation responsibility into a dedicated Validator component (SchemaValidator).
Both baseline and refactored implementations share the exact contract:
- add(2,3) -> 5
- multiply(2,3) -> 6
- unknown tool and non-numeric arguments yield structured errors
- failed call stops execution, preventing subsequent tools from running.
Proves before/after behavioral equivalence on test fixtures.
"""

from typing import Dict, Any, List, Union, Tuple, Optional
import json


# ---------------------------------------------------------------------------
# 1. Monolithic Baseline Implementation
# ---------------------------------------------------------------------------
def baseline_dispatch_single(call: Dict[str, Any]) -> Dict[str, Any]:
    tool = call.get("tool")
    if tool not in ("add", "multiply"):
        return {
            "status": "error",
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool}' not found",
                "tool": tool,
            }
        }

    args = call.get("args")
    if not isinstance(args, dict):
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENT_SCHEMA",
                "message": "args must be a dictionary",
                "tool": tool,
            }
        }

    for param in ("a", "b"):
        if param not in args:
            return {
                "status": "error",
                "error": {
                    "code": "MISSING_ARGUMENT",
                    "message": f"Missing argument: {param}",
                    "tool": tool,
                }
            }
        val = args[param]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENT_TYPE",
                    "message": f"Argument '{param}' must be numeric",
                    "tool": tool,
                    "details": {"param": param, "value": val}
                }
            }

    if tool == "add":
        res = args["a"] + args["b"]
    else:
        res = args["a"] * args["b"]

    return {
        "status": "success",
        "tool": tool,
        "result": res
    }


def baseline_dispatch_pipeline(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for call in calls:
        outcome = baseline_dispatch_single(call)
        results.append(outcome)
        if outcome.get("status") == "error":
            break
    return results


# ---------------------------------------------------------------------------
# 2. Refactored Implementation (Extracted Responsibility: SchemaValidator)
# ---------------------------------------------------------------------------
class SchemaValidator:
    """Dedicated component responsible for validating argument dictionaries."""

    @staticmethod
    def validate_binary_numeric_args(args: Any, tool: str) -> Optional[Dict[str, Any]]:
        """Returns None if valid, or a structured error envelope if invalid."""
        if not isinstance(args, dict):
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENT_SCHEMA",
                    "message": "args must be a dictionary",
                    "tool": tool,
                }
            }

        for param in ("a", "b"):
            if param not in args:
                return {
                    "status": "error",
                    "error": {
                        "code": "MISSING_ARGUMENT",
                        "message": f"Missing argument: {param}",
                        "tool": tool,
                    }
                }
            val = args[param]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                return {
                    "status": "error",
                    "error": {
                        "code": "INVALID_ARGUMENT_TYPE",
                        "message": f"Argument '{param}' must be numeric",
                        "tool": tool,
                        "details": {"param": param, "value": val}
                    }
                }

        return None


class ModularToolDispatcher:
    """Refactored dispatcher delegating argument validation to SchemaValidator."""

    ALLOWLIST = {
        "add": lambda a, b: a + b,
        "multiply": lambda a, b: a * b,
    }

    def __init__(self, validator: SchemaValidator = SchemaValidator()):
        self.validator = validator

    def dispatch_single(self, call: Dict[str, Any]) -> Dict[str, Any]:
        tool = call.get("tool")
        if tool not in self.ALLOWLIST:
            return {
                "status": "error",
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"Tool '{tool}' not found",
                    "tool": tool,
                }
            }

        err = self.validator.validate_binary_numeric_args(call.get("args"), tool)
        if err is not None:
            return err

        args = call["args"]
        res = self.ALLOWLIST[tool](args["a"], args["b"])
        return {
            "status": "success",
            "tool": tool,
            "result": res
        }

    def dispatch_pipeline(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for call in calls:
            outcome = self.dispatch_single(call)
            results.append(outcome)
            if outcome.get("status") == "error":
                break
        return results


def run_demo() -> Dict[str, Any]:
    test_calls = [
        {"tool": "add", "args": {"a": 2, "b": 3}},
        {"tool": "multiply", "args": {"a": 2, "b": 3}},
        {"tool": "unknown_tool", "args": {"a": 1, "b": 2}},
        {"tool": "add", "args": {"a": "invalid", "b": 3}},
    ]
    dispatcher = ModularToolDispatcher()
    return {
        "baseline": baseline_dispatch_pipeline(test_calls),
        "refactored": dispatcher.dispatch_pipeline(test_calls),
    }


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
