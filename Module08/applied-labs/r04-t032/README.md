# R04-T032: Typed Tool Dispatch (Boundary-Case Lesson Extension)

## Overview
This lab extends `Module08/06.ModelsAsTools.md` by demonstrating strict typed tool dispatch with an explicit allowlist, type schema checking, and failure boundary enforcement.

### Key Behaviors & Invariants
1. **Allowlist Gating**: Only explicitly registered tools (`add`, `multiply`) can be invoked; unlisted tools yield `UNKNOWN_TOOL` errors.
2. **Strict Numeric Type Checking**: Arguments `a` and `b` must be numeric (`int` or `float`). Strings or booleans are rejected with structured error envelopes (`INVALID_ARGUMENT_TYPE`).
3. **Pipeline Failure Halting**: In a pipeline of operations, a failed invocation terminates execution immediately; subsequent tools are not executed.
4. **Boundary Decisions**:
   - Zero values (`0`, `0.0`) and floating points are valid numeric boundaries.
   - Booleans (even though `isinstance(True, int)` evaluates true in Python) are rejected as invalid types for arithmetic tools.

## Running the Example
```bash
python3 Module08/applied-labs/r04-t032/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module08/applied-labs/r04-t032 -p "test_*.py"
```
