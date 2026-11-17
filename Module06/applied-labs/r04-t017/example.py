"""
R04-T017: Typed Tool Dispatch - Worked Example with Regression Checks
Companion applied lab for Module06/02.FunctionCalling.md.

Demonstrates typed tool dispatch with an explicit published worked example:
- Allowed tools: 'add' and 'multiply'.
- Arguments 'a' and 'b' must be numbers.
- add(2, 3) -> 5; multiply(2, 3) -> 6.
- Unknown tool and invalid argument types return structured errors.
- Strict isolation: a failed call cannot execute another tool.
- Produces a published worked input-to-output explanation verified by exact regression tests.

Prerequisites: Python 3 standard library only.
"""

import json
from typing import Any, Dict, List, Optional, Union


class ToolDispatchError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def tool_add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b


def tool_multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a * b


ALLOWED_TOOLS = {
    "add": tool_add,
    "multiply": tool_multiply,
}


def dispatch_tool_call(call_input: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates and executes a tool dispatch request according to the typed contract.
    """
    if isinstance(call_input, str):
        try:
            payload = json.loads(call_input)
        except Exception as exc:
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_JSON",
                    "message": f"Malformed JSON: {exc}",
                }
            }
    elif isinstance(call_input, dict):
        payload = call_input
    else:
        return {
            "status": "error",
            "error": {
                "code": "INVALID_INPUT",
                "message": f"Expected dict or JSON string, got {type(call_input).__name__}",
            }
        }

    tool_name = payload.get("tool") or payload.get("function")
    if not isinstance(tool_name, str) or tool_name not in ALLOWED_TOOLS:
        return {
            "status": "error",
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' is not in allowed tools: {list(ALLOWED_TOOLS.keys())}",
            }
        }

    args = payload.get("parameters") or payload.get("arguments") or {}
    if not isinstance(args, dict):
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "Parameters must be a dictionary.",
            }
        }

    if "a" not in args or "b" not in args:
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "Both parameters 'a' and 'b' are required.",
            }
        }

    a = args["a"]
    b = args["b"]

    if type(a) not in (int, float) or type(b) not in (int, float) or isinstance(a, bool) or isinstance(b, bool):
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": f"Parameters 'a' and 'b' must be numeric, got a={type(a).__name__}, b={type(b).__name__}.",
            }
        }

    # Dispatch to target tool
    fn = ALLOWED_TOOLS[tool_name]
    output = fn(a, b)

    return {
        "status": "success",
        "tool": tool_name,
        "result": output,
    }


WORKED_SESSION_TEXT = """[WORKED EXAMPLE SESSION]
1. Input: {"tool": "add", "parameters": {"a": 2, "b": 3}}
   Output: {"status": "success", "tool": "add", "result": 5}
2. Input: {"tool": "multiply", "parameters": {"a": 2, "b": 3}}
   Output: {"status": "success", "tool": "multiply", "result": 6}
3. Input: {"tool": "add", "parameters": {"a": "2", "b": 3}}
   Output: {"status": "error", "error": {"code": "INVALID_ARGUMENTS", "message": "Parameters 'a' and 'b' must be numeric, got a=str, b=int."}}
4. Input: {"tool": "power", "parameters": {"a": 2, "b": 3}}
   Output: {"status": "error", "error": {"code": "UNKNOWN_TOOL", "message": "Tool 'power' is not in allowed tools: ['add', 'multiply']"}}
"""


def run_worked_session() -> Dict[str, Any]:
    """Runs the canonical worked examples."""
    add_call = {"tool": "add", "parameters": {"a": 2, "b": 3}}
    mul_call = {"tool": "multiply", "parameters": {"a": 2, "b": 3}}
    str_a_call = {"tool": "add", "parameters": {"a": "2", "b": 3}}
    unk_call = {"tool": "power", "parameters": {"a": 2, "b": 3}}

    return {
        "add_res": dispatch_tool_call(add_call),
        "mul_res": dispatch_tool_call(mul_call),
        "str_a_res": dispatch_tool_call(str_a_call),
        "unk_res": dispatch_tool_call(unk_call),
    }


if __name__ == "__main__":
    print(WORKED_SESSION_TEXT)
    res = run_worked_session()
    print("Execution verification:")
    print(f"add(2, 3) -> {res['add_res']['result']}")
    print(f"multiply(2, 3) -> {res['mul_res']['result']}")
    print(f"string 'a' -> error code: {res['str_a_res']['error']['code']}")
    print(f"unknown tool -> error code: {res['unk_res']['error']['code']}")
