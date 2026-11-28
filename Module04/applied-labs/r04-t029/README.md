# R04-T029: Local Model-File Preflight — Evaluation Experiment

A deterministic local GGUF manifest preflight validator and controlled three-configuration experiment verifying format, file existence, and context limits before backend launch.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module04/02.Llamacpp.md`:** `llama.cpp` workflows require checking model format (GGUF), verifying the local file path exists, and ensuring the requested `-c` context size does not exceed the model's context capacity to avoid runtime failures or out-of-memory errors.
- **Where simplifications stop:** `dummy_model.gguf` is a 19-byte placeholder file (`GGUF-DUMMY-FIXTURE`), **not** real model weights, and the backend launcher is a mock callable. No real `llama-cli` execution, RAM measurement, or model accuracy claim is made.

## Controlled Three-Configuration Experiment
Evaluated against `format="GGUF"`, `path="dummy_model.gguf"`, `max_context=2048`:

| Config | Requested Context | Accepted | Correct | Utilization (`req/max`) | Headroom (`max-req`) | Launch Calls |
|---|---|---|---|---|---|---|
| `small_512` | `512` | `True` | `True` | `0.25` | `1536` | `1` |
| `medium_1024` | `1024` | `True` | `True` | `0.50` | `1024` | `1` |
| `oversized_4096` | `4096` | `False` | `True` | `2.00` | `-2048` | `0` |

- **Observed trade-off:** Increasing `requested_context` from `512` to `1024` doubles context utilization (`0.25` -> `0.50`) while halving remaining token headroom (`1536` -> `1024`), and requesting `4096` exceeds the `2048` limit so preflight blocks launch (`launch_calls=0`).

## Files
- `dummy_model.gguf` — Tiny placeholder fixture file (not model weights).
- `example.py` — `validate_and_launch_manifest` and `run_controlled_experiment`.
- `test_example.py` — Unit tests covering 1024 acceptance, 2048 boundary, 4096 rejection, missing file rejection, format validation, and the 3-config experiment.

## Prerequisites
- Python 3 standard library only (no `llama.cpp` build, real model weights, or GPU required).

## Usage & Verification
```bash
python3 Module04/applied-labs/r04-t029/example.py
python3 -m unittest discover -s Module04/applied-labs/r04-t029 -p "test_*.py"
```
