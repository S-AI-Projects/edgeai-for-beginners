"""
Typed Tool Dispatch with Allowlist and Argument Validation.

Dispatches local JSON calls for add(a, b) and multiply(a, b) through an
explicit allowlist and numeric argument validation.
Rejects unknown tools and non-numeric arguments with structured errors.
A failed call halts execution immediately and cannot execute subsequent tools.
"""

from typing import Dict, Any, List, Union, Tuple
import json


class ToolDispatchError(Exception):
    """Base exception for tool dispatch errors returning structured details."""
    def __init__(self, code: str, message: str, tool_name: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.tool_name = tool_name
        self.details = details or {}

    def to_envelope(self) -> Dict[str, Any]:
        return {
            "status": "error",
            "error": {
                "code": self.code,
                "message": self.message,
                "tool": self.tool_name,
                "details": self.details,
            }
        }


def add_op(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b


def multiply_op(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a * b


TOOL_ALLOWLIST = {
    "add": add_op,
    "multiply": multiply_op,
}


def dispatch_single_call(call: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and executes a single tool call dictionary.

    Schema:
    {
        "tool": str,
        "args": {
            "a": int | float,
            "b": int | float
        }
    }
    """
    tool_name = call.get("tool")
    if not isinstance(tool_name, str) or tool_name not in TOOL_ALLOWLIST:
        return {
            "status": "error",
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' is not in allowlist {list(TOOL_ALLOWLIST.keys())}",
                "tool": tool_name,
                "details": {}
            }
        }

    raw_args = call.get("args")
    if not isinstance(raw_args, dict):
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENT_SCHEMA",
                "message": "Arguments must be provided as a dictionary",
                "tool": tool_name,
                "details": {"args": raw_args}
            }
        }

    for param in ("a", "b"):
        if param not in raw_args:
            return {
                "status": "error",
                "error": {
                    "code": "MISSING_ARGUMENT",
                    "message": f"Missing required parameter '{param}'",
                    "tool": tool_name,
                    "details": {"missing_parameter": param}
                }
            }

        val = raw_args[param]
        # Boolean is a subclass of int in Python, so explicitly disallow bools as numeric operands
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENT_TYPE",
                    "message": f"Parameter '{param}' must be a numeric type (int or float), got {type(val).__name__}",
                    "tool": tool_name,
                    "details": {
                        "parameter": param,
                        "expected": "int | float",
                        "received_type": type(val).__name__,
                        "received_value": val,
                    }
                }
            }

    handler = TOOL_ALLOWLIST[tool_name]
    res = handler(raw_args["a"], raw_args["b"])
    return {
        "status": "success",
        "tool": tool_name,
        "result": res
    }


def dispatch_tool_pipeline(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Dispatches a sequence of tool calls.
    Invariant: A failed call halts further execution immediately.
    """
    results: List[Dict[str, Any]] = []
    for call in calls:
        outcome = dispatch_single_call(call)
        results.append(outcome)
        if outcome.get("status") == "error":
            # Halts immediately; subsequent calls cannot execute
            break
    return results


def run_demo() -> Dict[str, Any]:
    suite = [
        {"tool": "add", "args": {"a": 2, "b": 3}},
        {"tool": "multiply", "args": {"a": 2, "b": 3}},
        {"tool": "unknown_tool", "args": {"a": 1, "b": 2}},
        {"tool": "add", "args": {"a": "2", "b": 3}},
    ]
    return {
        "pipeline_results": [dispatch_single_call(c) for c in suite]
    }


if __name__ == "__main__":
    demo = run_demo()
    print(json.dumps(demo, indent=2))
