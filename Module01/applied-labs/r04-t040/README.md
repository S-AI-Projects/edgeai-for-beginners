# R04-T040: Token-Budget Preflight Comparison

## Overview
This lab extends `Module01/02.RealWorldCaseStudies.md` by demonstrating a preflight token budgeting checker comparing a direct implementation against an independent reference oracle.

### Scope and Approximation Label
> **⚠️ Teaching Approximation Note**: The tokenizer in this module is a local whitespace-splitting fixture implemented for conceptual verification of preflight budget trimming and bounds enforcement. It does **not** simulate production BPE, WordPiece, or SentencePiece subword tokenization used in physical models (such as Phi, Qwen, or Llama).

### Contracts & Invariants:
- **Budget Truncation**: A budget of 3 with `"one two three four"` retains `["one", "two", "three"]` and reports `removed_count = 1` and `truncated = True`.
- **Empty String**: Yields an empty token list with 0 removed tokens.
- **Negative Budget**: Raises `ValueError`.
- **Methodology Comparison**: The direct `TokenBudgetPreflight` implementation is checked against an independent reference calculation across boundary test cases.

## Execution
```bash
python3 Module01/applied-labs/r04-t040/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module01/applied-labs/r04-t040 -p "test_*.py"
```
