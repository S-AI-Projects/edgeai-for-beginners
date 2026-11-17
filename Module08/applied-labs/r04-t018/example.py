"""
R04-T018: Typed Tool Dispatch - Failure and Recovery Example
Companion applied lab for Module08/06.ModelsAsTools.md.

Demonstrates typed tool dispatch with documented failure and recovery:
- Allowed tools: 'add' and 'multiply'.
- Arguments 'a' and 'b' must be numbers.
- add(2, 3) -> 5; multiply(2, 3) -> 6.
- Unknown tool and invalid argument types return structured errors.
- Strict isolation: a failed call cannot execute another tool.
- Exercises a documented invalid/missing-data case, explains the failure,
  and demonstrates seamless recovery on the next valid input.

Prerequisites: Python 3 standard library only.
"""

import json
from typing import Any, Dict, List, Optional, Union


def tool_add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b


def tool_multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a * b


ALLOWED_TOOLS = {
    "add": tool_add,
    "multiply": tool_multiply,
}


class ToolDispatcher:
    """
    Stateless, robust tool dispatcher enforcing schema validation and recovery.
    """
    def __init__(self):
        self.call_history: List[Dict[str, Any]] = []

    def dispatch(self, call_input: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses input, verifies allowlist, validates types, and dispatches.
        Logs every attempt to history.
        """
        if isinstance(call_input, str):
            try:
                payload = json.loads(call_input)
            except Exception as exc:
                res = {
                    "status": "error",
                    "error": {
                        "code": "INVALID_JSON",
                        "message": f"Malformed JSON: {exc}",
                    }
                }
                self.call_history.append(res)
                return res
        elif isinstance(call_input, dict):
            payload = call_input
        else:
            res = {
                "status": "error",
                "error": {
                    "code": "INVALID_INPUT",
                    "message": f"Expected dict or JSON string, got {type(call_input).__name__}",
                }
            }
            self.call_history.append(res)
            return res

        tool_name = payload.get("tool") or payload.get("function")
        if not isinstance(tool_name, str) or tool_name not in ALLOWED_TOOLS:
            res = {
                "status": "error",
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"Tool '{tool_name}' is not in allowed tools: {list(ALLOWED_TOOLS.keys())}",
                }
            }
            self.call_history.append(res)
            return res

        args = payload.get("parameters") or payload.get("arguments") or {}
        if not isinstance(args, dict):
            res = {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": "Parameters must be a key-value dictionary.",
                }
            }
            self.call_history.append(res)
            return res

        if "a" not in args or "b" not in args:
            missing = [k for k in ("a", "b") if k not in args]
            res = {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": f"Missing required parameter(s): {missing}.",
                }
            }
            self.call_history.append(res)
            return res

        a = args["a"]
        b = args["b"]

        if type(a) not in (int, float) or type(b) not in (int, float) or isinstance(a, bool) or isinstance(b, bool):
            res = {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": f"Parameters 'a' and 'b' must be numeric, got a={type(a).__name__}, b={type(b).__name__}.",
                }
            }
            self.call_history.append(res)
            return res

        # Execution
        fn = ALLOWED_TOOLS[tool_name]
        output = fn(a, b)

        res = {
            "status": "success",
            "tool": tool_name,
            "result": output,
        }
        self.call_history.append(res)
        return res


def run_failure_and_recovery_session() -> Dict[str, Any]:
    """
    Demonstrates:
    1. Initial valid call: add(2, 3) -> 5
    2. Documented failure: missing data and string 'a' -> INVALID_ARGUMENTS
    3. Seamless recovery on next valid input: multiply(2, 3) -> 6
    """
    dispatcher = ToolDispatcher()

    # Step 1: Valid call
    step1 = dispatcher.dispatch({"tool": "add", "parameters": {"a": 2, "b": 3}})

    # Step 2: Documented failure (string 'a')
    step2 = dispatcher.dispatch({"tool": "add", "parameters": {"a": "2", "b": 3}})

    # Step 3: Documented failure (missing 'b')
    step3 = dispatcher.dispatch({"tool": "multiply", "parameters": {"a": 5}})

    # Step 4: Recovery on next valid input
    step4 = dispatcher.dispatch({"tool": "multiply", "parameters": {"a": 2, "b": 3}})

    return {
        "step1_success": step1["status"] == "success" and step1["result"] == 5,
        "step2_error_code": step2["error"]["code"],
        "step3_error_code": step3["error"]["code"],
        "step4_recovered": step4["status"] == "success" and step4["result"] == 6,
        "history_count": len(dispatcher.call_history),
    }


if __name__ == "__main__":
    res = run_failure_and_recovery_session()
    print("=== Typed Tool Dispatch: Failure and Recovery ===")
    print(f"Step 1 (Initial valid call add(2,3)): success={res['step1_success']}")
    print(f"Step 2 (String argument failure): error_code={res['step2_error_code']}")
    print(f"Step 3 (Missing parameter failure): error_code={res['step3_error_code']}")
    print(f"Step 4 (Immediate recovery call multiply(2,3)): recovered={res['step4_recovered']}")
    print(f"Total dispatched operations tracked: {res['history_count']}")
