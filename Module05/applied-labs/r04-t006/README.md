# Applied Lab R04-T006: Token-Budget Preflight Refactoring

## Overview

In enterprise SLMOps pipelines, software maintainability and single-responsibility principles are essential for sustainable deployment operations. Monolithic input handlers that intertwine string parsing, token extraction, budget boundary checking, and truncation policies are fragile and difficult to test.

This lab demonstrates an engineering refactoring:
1. **Baseline**: `BaselineTokenBudgetPreflight` implements the token budget check in a single procedural routine.
2. **Refactored**: Extracts `TruncationPolicy` as a dedicated, reusable component responsible solely for token partitioning.
3. **Equivalence**: Mathematical and behavioral equivalence between baseline and refactored implementations is verified across multiple input fixtures and budgets.

## Contract Specification

- **Overflow**: Budget `3` with `"one two three four"` retains `['one', 'two', 'three']` and reports `1` removed token (`['four']`).
- **Empty Input**: Empty input string retains `[]` with `0` removed tokens.
- **Negative Budget**: Budget `< 0` raises `ValueError`.
- **Teaching Label**: Explicitly labels whitespace tokenization as a teaching approximation.

## Scope & Limitations

> [!NOTE] Teaching Approximation
> Whitespace tokenization (`text.split()`) is used as a deterministic approximation for unit testing. In production SLMOps serving architectures, plug in the target model's actual BPE/SentencePiece tokenizer.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module05/applied-labs/r04-t006 -p "test_*.py"
```
