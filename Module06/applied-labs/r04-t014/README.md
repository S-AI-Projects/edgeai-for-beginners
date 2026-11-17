# R04-T014 - Typed Tool Dispatch: Invariant and State Trace

Companion applied lab to [Module06/02.FunctionCalling.md](../../02.FunctionCalling.md) ("Section02 : Function Calling in Small Language Models (SLMs) - How Function Calling Works").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
In SLM function calling, the model outputs structured JSON containing tool identifiers and parameter arguments. The runtime must enforce:
1. **Explicit Allowlist**: Only designated tools (`add`, `multiply`) can be called.
2. **Strict Type Validation**: Arguments `a` and `b` must be real numbers (`int` or `float`), rejecting strings, booleans, and nulls.
3. **Fail-Safe Isolation**: If validation fails at any point, the dispatch pipeline halts immediately. A failed call can never invoke fallback or alternative tools.
4. **Step-by-Step State Tracing**: Intermediate states (`INPUT_RECEIVED`, `PARSE_JSON`, `ALLOWLIST_CHECK`, `ARGUMENT_VALIDATION`, `DISPATCH_EXECUTION`) are recorded to prove execution invariants.

### Scope and Limitations
* **Local Contract Fixture**: Demonstrates dispatch verification and state tracing locally. It is **not** a full client/server Model Context Protocol (MCP) transport or live network bridge.
* **Prerequisites**: Python 3 standard library only.

---

## 2. Canonical Task Fixture

* **Normal Calls**:
  * `add(2, 3)` $\rightarrow$ `5` (status: `success`)
  * `multiply(2, 3)` $\rightarrow$ `6` (status: `success`)
* **Error Cases**:
  * String argument `a="2"` $\rightarrow$ structured error `INVALID_ARGUMENTS`.
  * Unknown tool `"power"` $\rightarrow$ structured error `UNKNOWN_TOOL`.
* **State Trace Invariants**:
  * Successful call transitions through all 5 pipeline stages and outputs `DISPATCH_EXECUTION: SUCCESS`.
  * Failed call halts at validation, never logs `DISPATCH_EXECUTION`, and executes zero tool handlers.

---

## 3. Run and Verify

```bash
python3 Module06/applied-labs/r04-t014/example.py
python3 -m unittest discover -s Module06/applied-labs/r04-t014 -p "test_*.py"
```
Ran 14 tests in ~0.001s, OK.
