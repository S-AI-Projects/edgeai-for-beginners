# Applied Lab R04-T010: Token-Budget Preflight — Scenario Assessment

## Overview

Real-world EdgeAI deployments require rigorous input governance to avoid resource exhaustion and silent generation failures. 

This lab couples a deterministic local token budget preflight check with a three-part **Scenario Assessment**:
1. **Predict an Output**: Calculating exact retained and removed tokens when prompt length exceeds the allocated budget.
2. **Diagnose a Failure**: Analyzing negative budget configuration errors and remediation steps.
3. **Choose a Boundary Policy**: Deciding truncation behavior when prompt token length exactly equals the budget limit.

## Scenario Questions & Factual Rationales

### Q1: Predict Output
- **Question**: Given budget `3` and input `"edge ai on device inference"`, what is the outcome?
- **Answer**: Retains `['edge', 'ai', 'on']`, removes `['device', 'inference']` (2 removed tokens), `truncated=True`.
- **Rationale**: The first 3 tokens fill the allocated budget; subsequent tokens are truncated to protect local buffer limits.

### Q2: Diagnose Failure
- **Question**: Why does `TokenBudgetPreflight(budget=-5)` fail?
- **Answer**: Raises `ValueError("Token budget cannot be negative: -5")`.
- **Rationale**: Memory token allocations cannot be negative integers.

### Q3: Choose Boundary Policy
- **Question**: For a 5-token prompt evaluated against budget `5`, should truncation occur?
- **Answer**: Retain all 5 tokens (`truncated=False`, `removed_count=0`).
- **Rationale**: Exact capacity (`len(tokens) == budget`) satisfies the constraint without exceeding memory limits.

## Scope & Limitations

> [!NOTE] Teaching Approximation
> Whitespace splitting (`text.split()`) is used as a deterministic teaching approximation. Production edge architectures must use the target SLM's native tokenizer.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module01/applied-labs/r04-t010 -p "test_*.py"
```
