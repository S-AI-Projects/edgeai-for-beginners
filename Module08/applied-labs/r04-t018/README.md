# R04-T018 - Typed Tool Dispatch: Failure and Recovery Example

Companion applied lab to [Module08/06.ModelsAsTools.md](../../06.ModelsAsTools.md) ("Overview - Models as Tools").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
Deploying models as modular tools requires resilience: when an agent passes invalid parameters or requests unsupported tools, the runtime must reject the malformed call safely without contaminating state or crashing the service, and seamlessly process subsequent valid requests.

This lab demonstrates:
1. **Typed Tool Allowlist**: Enforces `add(a, b)` and `multiply(a, b)` with numeric validation.
2. **Structured Errors**: Returns `INVALID_ARGUMENTS` for non-numeric types or missing keys, and `UNKNOWN_TOOL` for unlisted functions.
3. **Execution Isolation**: A failed call halts immediately without executing another tool.
4. **State Isolation & Recovery**: Demonstrates a documented sequence:
   * `add(2, 3)` $\rightarrow$ `5` (success)
   * `add("2", 3)` $\rightarrow$ `INVALID_ARGUMENTS` (failure, explained)
   * `multiply(4)` $\rightarrow$ `INVALID_ARGUMENTS` (missing parameter `b`)
   * `multiply(2, 3)` $\rightarrow$ `6` (immediate successful recovery)

### Scope and Limitations
* **Local Contract Fixture**: Validates dispatch robustness and error recovery locally. It is **not** a full MCP client/server transport.
* **Prerequisites**: Python 3 standard library only.

---

## 2. Canonical Task Fixture

* `add(2, 3)` $\rightarrow$ `5`
* `multiply(2, 3)` $\rightarrow$ `6`
* Non-numeric string argument `a="2"` $\rightarrow$ `INVALID_ARGUMENTS`
* Unknown tool $\rightarrow$ `UNKNOWN_TOOL`
* Subsequent valid call succeeds without dispatcher state poisoning.

---

## 3. Run and Verify

```bash
python3 Module08/applied-labs/r04-t018/example.py
python3 -m unittest discover -s Module08/applied-labs/r04-t018 -p "test_*.py"
```
Ran 7 tests in ~0.001s, OK.
