# R04-T017 - Typed Tool Dispatch: Worked Example with Checks

Companion applied lab to [Module06/02.FunctionCalling.md](../../02.FunctionCalling.md) ("Section02 : Function Calling in Small Language Models (SLMs) - How Function Calling Works").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
SLM function calling pipelines parse structured tool invocation requests from generated JSON. Reliable agent deployment requires strict dispatch contracts:
1. **Tool Allowlist**: Only registered tools (`add`, `multiply`) can be invoked.
2. **Numeric Validation**: Arguments `a` and `b` must be numeric (`int` or `float`). Strings and booleans are rejected with structured errors (`INVALID_ARGUMENTS`).
3. **Execution Isolation**: A failed call halts processing immediately and never executes another tool.
4. **Worked Example Regression**: The exact published input/output session is maintained as a regression test to prevent contract drift.

### Scope and Limitations
* **Local Contract Fixture**: Models JSON parsing, type validation, and dispatch locally. Not a full Model Context Protocol (MCP) server or network client.
* **Prerequisites**: Python 3 standard library only.

---

## 2. Published Worked Example Session

```text
1. Input:  {"tool": "add", "parameters": {"a": 2, "b": 3}}
   Output: {"status": "success", "tool": "add", "result": 5}

2. Input:  {"tool": "multiply", "parameters": {"a": 2, "b": 3}}
   Output: {"status": "success", "tool": "multiply", "result": 6}

3. Input:  {"tool": "add", "parameters": {"a": "2", "b": 3}}
   Output: {"status": "error", "error": {"code": "INVALID_ARGUMENTS", "message": "Parameters 'a' and 'b' must be numeric, got a=str, b=int."}}

4. Input:  {"tool": "power", "parameters": {"a": 2, "b": 3}}
   Output: {"status": "error", "error": {"code": "UNKNOWN_TOOL", "message": "Tool 'power' is not in allowed tools: ['add', 'multiply']"}}
```

---

## 3. Run and Verify

```bash
python3 Module06/applied-labs/r04-t017/example.py
python3 -m unittest discover -s Module06/applied-labs/r04-t017 -p "test_*.py"
```
Ran 8 tests in ~0.001s, OK.
