# Applied Lab R04-T001: Token-Budget Preflight

## Overview

In resource-constrained Edge AI environments, Small Language Models (SLMs) operate with bounded context windows (e.g., 2048 or 4096 tokens) and restricted KV-cache memory. Attempting to process prompts exceeding the allocated budget can cause unexpected runtime out-of-memory (OOM) failures or unintended truncation.

This lab provides a deterministic local **Token Budget Preflight** check that inspects prompt lengths prior to model invocation, reporting retained tokens, truncated tokens, and boundary decisions.

## Scope & Limitations

> [!NOTE] Teaching Approximation Notice
> The tokenization logic in this lab uses deterministic whitespace splitting (`cleaned.split()`) as a pedagogical approximation to illustrate preflight accounting and boundary handling.
> It is **not** a production subword tokenizer (such as Byte-Pair Encoding or SentencePiece) and does not represent hardware-specific memory allocations or trained-model inference.

## Contract Specification

1. **Configured Budget**: Non-negative integer representing the token limit. A negative budget raises a `ValueError`.
2. **Overflow Handling**: Given budget `3` and input `"one two three four"`, the checker retains `['one', 'two', 'three']` and reports `1` removed token (`['four']`) with `truncated = True`.
3. **Empty Input**: Given empty string `""` or whitespace-only input, the checker retains `[]` and reports `0` removed tokens with `truncated = False`.
4. **Boundary**: Given prompt length equal to budget, all tokens are retained with `0` removed tokens.
5. **Preflight Report**: Outputs a structured report containing original prompt, token counts, retained/removed lists, and explicit clarification of the teaching approximation.

## File Structure

- `example.py`: Core `TokenBudgetPreflight` class and interactive CLI demonstration.
- `test_example.py`: Automated unit tests covering normal, boundary, and error conditions.
- `README.md`: Architectural documentation, contract specification, and test instructions.

## Verification & Execution

### Run the Example
```bash
python3 example.py
```

### Run the Test Suite
```bash
python3 -m unittest discover -s Module03/applied-labs/r04-t001 -p "test_*.py"
```
