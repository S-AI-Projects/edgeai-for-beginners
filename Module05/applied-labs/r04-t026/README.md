# R04-T026: Trainable-Parameter Accounting — Refactor the Teaching Example

A deterministic local named-parameter manifest counter that starts with a baseline implementation, extracts prefix-matching into a named helper (`classify_freeze_matches`), and proves before/after equivalence.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module05/03.SLMOps-Finetuing.md`:** Fine-tuning workflows (such as LoRA or partial layer freezing) rely on freezing base layers while keeping task heads trainable. A prefix typo leaves unintended layers trainable or silently matches nothing unless unmatched freeze prefixes are explicitly surfaced.
- **Where simplifications stop:** The manifest (`{"encoder": 100, "head": 20}`) is a synthetic dictionary of integer parameter counts, not a real PyTorch/ONNX model, and makes no claims about optimizer state memory, gradient checkpointing, or training speed.

## Refactored Responsibility
- **Baseline:** `account_parameters_baseline(manifest, freeze_prefixes)` performs prefix matching and summation inline.
- **Extracted responsibility:** `classify_freeze_matches(param_names, freeze_prefixes)` isolates prefix matching and unmatched-prefix detection; `account_parameters_refactored(...)` preserves the exact same return contract.

## Files
- `example.py` — Baseline, extracted helper, and refactored accounting functions.
- `test_example.py` — Unit tests verifying contract values, unmatched-prefix reporting, before/after equivalence, and validation errors.

## Prerequisites
- Python 3 standard library only (no model download, PyTorch, or GPU required).

## Usage & Verification
```bash
python3 Module05/applied-labs/r04-t026/example.py
python3 -m unittest discover -s Module05/applied-labs/r04-t026 -p "test_*.py"
```
