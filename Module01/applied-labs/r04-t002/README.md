# Applied Lab R04-T002: Token-Budget Preflight Boundary Extension

## Overview

Deploying Small Language Models (SLMs) on edge hardware requires predictable resource bounds. Edge devices cannot allocate unbounded memory buffers on demand without crashing or causing OS-level thrashing.

This lab provides a deterministic **Token Budget Preflight** check emphasizing boundary conditions:
- Smallest valid cases (empty string `""`, single token `"word"`).
- Exact boundary limits (`total_tokens == budget`).
- Off-by-one boundary overflows (`total_tokens == budget + 1`).
- Invalid inputs (negative budgets, null pointers).

## Scope & Limitations

> [!NOTE] Teaching Approximation Notice
> This implementation employs deterministic whitespace splitting (`cleaned.split()`) as a pedagogical fixture.
> It demonstrates boundary conditions and preflight rejection rules, but is **not** a production tokenizer (such as tiktoken, SentencePiece, or Hugging Face BPE).

## Boundary Matrix

| Input | Budget | Retained Tokens | Removed Count | Boundary Decision |
|---|---|---|---|---|
| `""` | 3 | `[]` | 0 | `EMPTY_INPUT` (Smallest valid input) |
| `"word"` | 3 | `['word']` | 0 | `UNDER_BUDGET` |
| `"one two three"` | 3 | `['one', 'two', 'three']` | 0 | `EXACT_CAPACITY` (Exact match) |
| `"one two three four"` | 3 | `['one', 'two', 'three']` | 1 | `OVER_BUDGET` (1-token overflow) |
| `"any text"` | -1 | Exception | - | Invalid (raises `ValueError`) |

## Verification & Execution

### Run CLI Demo
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module01/applied-labs/r04-t002 -p "test_*.py"
```
