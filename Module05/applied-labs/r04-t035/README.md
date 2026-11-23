# R04-T035: Typed Tool Dispatch (Refactor Teaching Example)

## Overview
This lab extends `Module05/04.SLMOps.Deployment.md` by demonstrating a clean refactoring of a tool execution dispatch system.

### Refactoring Focus
- **Baseline**: A monolithic dispatch routine handling tool allowlist lookup, schema validation, type checking, and arithmetic execution together.
- **Extracted Responsibility**: `SchemaValidator`, isolating argument parsing, dictionary inspection, and type assertions.
- **Equivalence Verification**: Comprehensive test suites verify exact input/output equivalence between the baseline and refactored implementations across success cases, edge values, and error envelopes.

### Contract
- `add(2, 3)` -> `5`
- `multiply(2, 3)` -> `6`
- Unknown tools and non-numeric inputs yield structured errors (`UNKNOWN_TOOL`, `INVALID_ARGUMENT_TYPE`).
- Pipeline stops immediately on failure.

## Execution
```bash
python3 Module05/applied-labs/r04-t035/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module05/applied-labs/r04-t035 -p "test_*.py"
```
