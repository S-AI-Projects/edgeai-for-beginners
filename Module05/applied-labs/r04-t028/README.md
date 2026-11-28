# R04-T028: Trainable-Parameter Accounting — Failure and Recovery Example

A deterministic local named-parameter accounting lab demonstrating explicit error diagnosis on missing/invalid manifest data and clean recovery on the next valid input.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module05/03.SLMOps-Finetuing.md`:** Fine-tuning pipelines must catch corrupted or missing layer manifests and misconfigured freeze prefixes before training starts, report clear diagnostics, and continue processing subsequent valid configurations cleanly.
- **Where simplifications stop:** The manifest (`{"encoder": 100, "head": 20}`) is a synthetic dictionary of integer counts, not real PyTorch weights, optimizer states, or GPU memory usage.

## Failure & Recovery Flow
1. **Invalid / missing-data cases:** `None` or `{}` manifest, negative/non-int parameter counts, or blank freeze prefixes raise `ManifestValidationError` with an explanatory message.
2. **Recovery:** `process_manifest_stream` isolates each manifest evaluation so an invalid configuration is logged as `"status": "error"` without corrupting state, and the next valid manifest (`{"encoder": 100, "head": 20}`, freeze `["encoder"]`) succeeds with `total=120`, `trainable=20`.

## Files
- `example.py` — `ManifestValidationError`, `account_parameters`, and `process_manifest_stream`.
- `test_example.py` — Unit tests verifying normal fixture counts, unmatched prefix reporting, invalid/missing-data errors, and recovery.

## Prerequisites
- Python 3 standard library only (no model downloads, PyTorch, or GPU required).

## Usage & Verification
```bash
python3 Module05/applied-labs/r04-t028/example.py
python3 -m unittest discover -s Module05/applied-labs/r04-t028 -p "test_*.py"
```
