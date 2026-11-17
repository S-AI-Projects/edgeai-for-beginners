"""
R04-T014: Typed Tool Dispatch - Invariant and State Trace
Companion applied lab for Module06/02.FunctionCalling.md.

Demonstrates local typed JSON tool dispatch with step-by-step state tracing:
- Allowed tools: 'add' and 'multiply'.
- Arguments 'a' and 'b' must be numbers (integers or floats, not strings or booleans).
- add(2, 3) -> 5; multiply(2, 3) -> 6.
- Unknown tool and invalid argument types return structured errors.
- Strict isolation: a failed call cannot execute another tool.
- Records intermediate state trace after each step to verify state-to-output invariants.

Prerequisites: Python 3 standard library only.
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union


class ToolDispatchError(Exception):
    """Raised when JSON parsing, allowlist verification, or parameter validation fails."""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.details = details or {}


def tool_add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b


def tool_multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a * b


TOOL_REGISTRY = {
    "add": tool_add,
    "multiply": tool_multiply,
}


class DispatchTracer:
    """Manages execution state tracing for tool dispatch operations."""
    def __init__(self):
        self.trace: List[Dict[str, Any]] = []

    def record_step(self, step_name: str, status: str, context: Dict[str, Any]):
        self.trace.append({
            "step": step_name,
            "status": status,
            "context": dict(context),
        })

    def get_steps(self) -> List[str]:
        return [item["step"] for item in self.trace]


def dispatch_tool_call(call_input: Union[str, Dict[str, Any]], tracer: Optional[DispatchTracer] = None) -> Dict[str, Any]:
    """
    Parses and dispatches a tool call with rigorous numeric validation and state tracing.
    """
    tr = tracer or DispatchTracer()

    # Step 1: Parse input
    tr.record_step("INPUT_RECEIVED", "STARTED", {"raw_input": call_input})
    if isinstance(call_input, str):
        try:
            payload = json.loads(call_input)
        except Exception as exc:
            tr.record_step("PARSE_JSON", "FAILED", {"error": str(exc)})
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_JSON",
                    "message": f"Malformed JSON input: {exc}",
                },
                "trace": tr.trace,
            }
    elif isinstance(call_input, dict):
        payload = call_input
    else:
        tr.record_step("PARSE_JSON", "FAILED", {"error": "Input must be dict or JSON string"})
        return {
            "status": "error",
            "error": {
                "code": "INVALID_INPUT",
                "message": f"Input must be dict or JSON string, got {type(call_input).__name__}",
            },
            "trace": tr.trace,
        }

    tr.record_step("PARSE_JSON", "SUCCESS", {"payload": payload})

    # Step 2: Validate structure & tool allowlist
    tool_name = payload.get("tool") or payload.get("function")
    tr.record_step("ALLOWLIST_CHECK", "STARTED", {"tool_name": tool_name})

    if not isinstance(tool_name, str) or tool_name not in TOOL_REGISTRY:
        tr.record_step("ALLOWLIST_CHECK", "FAILED", {"tool_name": tool_name, "allowed": list(TOOL_REGISTRY.keys())})
        return {
            "status": "error",
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' is not in allowed tools: {list(TOOL_REGISTRY.keys())}",
            },
            "trace": tr.trace,
        }
    tr.record_step("ALLOWLIST_CHECK", "SUCCESS", {"tool_name": tool_name})

    # Step 3: Validate arguments
    args = payload.get("parameters") or payload.get("arguments") or {}
    tr.record_step("ARGUMENT_VALIDATION", "STARTED", {"args": args})

    if not isinstance(args, dict):
        tr.record_step("ARGUMENT_VALIDATION", "FAILED", {"error": "Arguments must be a dictionary"})
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "Arguments must be a key-value dictionary.",
            },
            "trace": tr.trace,
        }

    if "a" not in args or "b" not in args:
        tr.record_step("ARGUMENT_VALIDATION", "FAILED", {"error": "Missing required argument 'a' or 'b'"})
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "Both arguments 'a' and 'b' are required.",
            },
            "trace": tr.trace,
        }

    a = args["a"]
    b = args["b"]

    # Reject booleans (since in Python bool is a subclass of int) and strings
    if type(a) not in (int, float) or type(b) not in (int, float) or isinstance(a, bool) or isinstance(b, bool):
        tr.record_step("ARGUMENT_VALIDATION", "FAILED", {"a": a, "type_a": type(a).__name__, "b": b, "type_b": type(b).__name__})
        return {
            "status": "error",
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": f"Arguments 'a' and 'b' must be numbers, got a={type(a).__name__}, b={type(b).__name__}.",
            },
            "trace": tr.trace,
        }

    tr.record_step("ARGUMENT_VALIDATION", "SUCCESS", {"a": a, "b": b})

    # Step 4: Dispatch execution
    tr.record_step("DISPATCH_EXECUTION", "STARTED", {"tool": tool_name, "a": a, "b": b})
    fn = TOOL_REGISTRY[tool_name]
    output = fn(a, b)
    tr.record_step("DISPATCH_EXECUTION", "SUCCESS", {"result": output})

    return {
        "status": "success",
        "tool": tool_name,
        "result": output,
        "trace": tr.trace,
    }


def run_concept_example() -> Dict[str, Any]:
    """Runs the canonical fixture scenarios."""
    # 1. add(2, 3) -> 5
    tracer_add = DispatchTracer()
    add_res = dispatch_tool_call({"tool": "add", "parameters": {"a": 2, "b": 3}}, tracer_add)

    # 2. multiply(2, 3) -> 6
    tracer_mul = DispatchTracer()
    mul_res = dispatch_tool_call({"tool": "multiply", "parameters": {"a": 2, "b": 3}}, tracer_mul)

    # 3. String argument 'a' failure
    tracer_str_a = DispatchTracer()
    str_a_res = dispatch_tool_call({"tool": "add", "parameters": {"a": "2", "b": 3}}, tracer_str_a)

    # 4. Unknown tool failure
    tracer_unk = DispatchTracer()
    unk_res = dispatch_tool_call({"tool": "power", "parameters": {"a": 2, "b": 3}}, tracer_unk)

    return {
        "add_result": add_res["result"],
        "add_status": add_res["status"],
        "mul_result": mul_res["result"],
        "mul_status": mul_res["status"],
        "str_a_code": str_a_res["error"]["code"],
        "unk_tool_code": unk_res["error"]["code"],
        "add_trace_steps": tracer_add.get_steps(),
        "str_a_trace_steps": tracer_str_a.get_steps(),
    }


if __name__ == "__main__":
    result = run_concept_example()
    print("=== Typed Tool Dispatch Example ===")
    print(f"add(2, 3): status={result['add_status']}, result={result['add_result']}")
    print(f"multiply(2, 3): status={result['mul_status']}, result={result['mul_result']}")
    print(f"string 'a' error: code={result['str_a_code']}")
    print(f"unknown tool error: code={result['unk_tool_code']}")
    print(f"add trace steps: {result['add_trace_steps']}")
    print(f"string 'a' trace steps: {result['str_a_trace_steps']}")
    print("\n[NOTE] Local contract fixture: dispatch halts immediately on validation failure; no secondary execution.")
