# R04-T022: Token-Budget Preflight (Boundary-Case Lesson Extension)

A deterministic local whitespace-token fixture illustrating how SLMOps preflight gates enforce configured token budgets across smallest valid, exact-boundary, over-budget, and invalid inputs.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module05/01.IntroduceSLMOps.md`:** SLMOps emphasizes intelligent resource management and automated pre-deployment/runtime validation for constrained edge nodes. Enforcing a deterministic token-budget preflight check catches oversized prompts early and reports explicit truncation counts before inference runs.
- **Where simplifications stop:** `prompt.split()` is a teaching approximation, **not** a real subword model tokenizer (BPE/WordPiece/SentencePiece). It does not model actual token-ID length, memory/KV-cache footprint, device latency, or model output quality.

## Exact Boundary Decision
Given `tokens = prompt.split()` and `budget >= 0`:
1. **Invalid inputs (fail fast):** `budget < 0` raises `ValueError`; non-`int` or `bool` budgets and non-`str` prompts raise `TypeError` before tokenization.
2. **Smallest valid (`""`, `budget=0` and `"edge"`, `budget=1`):** Produces `0` removed tokens (`truncated=False`).
3. **Exact boundary (`len(tokens) <= budget`):** Retains all tokens (`removed_count=0`, `truncated=False`).
4. **Over boundary (`len(tokens) > budget`):** Retains `tokens[:budget]` and reports `removed_count = len(tokens) - budget` (`truncated=True`). For `"one two three four"` with `budget=3`, `['one', 'two', 'three']` is retained and `1` token is removed.

## Files
- `example.py` — `check_token_budget(prompt, budget)` and `run_boundary_suite()`.
- `test_example.py` — Unit tests covering smallest valid, boundary, empty, and invalid cases.

## Prerequisites
- Python 3 standard library only (no model downloads, GPU, or external services).

## Usage & Verification
```bash
python3 Module05/applied-labs/r04-t022/example.py
python3 -m unittest discover -s Module05/applied-labs/r04-t022 -p "test_*.py"
```
