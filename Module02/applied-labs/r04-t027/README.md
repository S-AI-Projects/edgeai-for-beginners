# R04-T027: Model-Manifest Selection — Worked Example with Checks

A deterministic worked example showing input-to-output model-manifest filtering against device RAM and requested context length, verified by an automated regression test.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module02/01.PhiFamily.md`:** Matching edge hardware constraints (available RAM and required context length) against model metadata determines which model variants can be deployed and why others must be excluded.
- **Where simplifications stop:** `Model-A` (RAM 4 / context 2048) and `Model-B` (RAM 8 / context 4096) are **invented synthetic teaching fixtures**, not claims about real Microsoft Phi model weights, quantization sizes, or hardware speed.

## Worked Input-to-Output Walkthrough
1. **Inputs:**
   - Manifest: `Model-A (ram_gb=4, max_context=2048)`, `Model-B (ram_gb=8, max_context=4096)`
   - Device budget & request: `ram_budget_gb=6`, `requested_context=1024`
2. **Evaluation:**
   - `Model-A`: `4 <= 6` (RAM fits) and `2048 >= 1024` (context fits) -> **eligible**.
   - `Model-B`: `8 > 6` (RAM exceeds budget) and `4096 >= 1024` (context fits) -> **excluded** with `['ram_exceeds_budget (needs 8 > budget 6)']`.
3. **Output:** `eligible=['Model-A']`, `excluded={'Model-B': ['ram_exceeds_budget (needs 8 > budget 6)']}`.

## Files
- `example.py` — `WORKED_MANIFEST`, `EXPECTED_WORKED_OUTPUT`, `select_eligible_models`, and `run_worked_example`.
- `test_example.py` — Regression test executing `run_worked_example()` plus boundary and failure cases.

## Prerequisites
- Python 3 standard library only (no model downloads, GPU, or external services).

## Usage & Verification
```bash
python3 Module02/applied-labs/r04-t027/example.py
python3 -m unittest discover -s Module02/applied-labs/r04-t027 -p "test_*.py"
```
