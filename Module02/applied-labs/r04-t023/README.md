# R04-T023: Model-Manifest Selection — Compare Two Approaches

A deterministic local synthetic model-manifest selector comparing a structured direct implementation against an independent predicate calculation and an explicit expected-result table using identical inputs.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module02/03.GemmaFamily.md`:** Selecting an edge SLM variant requires matching device RAM and required context length against model metadata and understanding why candidates are disqualified.
- **Where simplifications stop:** `Model-A` (RAM 4 / context 2048) and `Model-B` (RAM 8 / context 4096) are **invented synthetic teaching fixtures**, not claims about real Gemma parameter counts, quantization footprints, KV-cache scaling, or runtime speed.

## Approach Comparison
1. **Direct implementation (`select_eligible_models`):** Evaluates each manifest entry field-by-field and returns structured `eligible` and `excluded` failure-reason lists plus the synthetic fixture disclaimer.
2. **Independent calculation & table (`independent_eligible_calculation` & `EXPLICIT_EXPECTED_TABLE`):** Recomputes admissibility using an independent list-comprehension predicate and verifies exact agreement against a hand-verified lookup table across normal, boundary, and all-excluded scenarios.

## Files
- `example.py` — Synthetic manifest, direct selector, independent calculation, expected table, and comparison runner.
- `test_example.py` — Unit tests checking fixture eligibility, parity across all expected-table rows, boundary matches, and invalid inputs.

## Prerequisites
- Python 3 standard library only (no model downloads, GPU, or external services).

## Usage & Verification
```bash
python3 Module02/applied-labs/r04-t023/example.py
python3 -m unittest discover -s Module02/applied-labs/r04-t023 -p "test_*.py"
```
