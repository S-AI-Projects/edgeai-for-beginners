# Applied Lab R04-T007: Local Model-File Preflight

## Overview

Deploying quantized models with frameworks such as `llama.cpp` requires validating model manifests before initializing execution backends. Failure to validate inputs prior to launch can cause cryptic segfaults, out-of-memory panics, or unintended silent fallback.

This lab provides a deterministic local **Model Manifest Validator**:
1. Confirms the file format is `GGUF`.
2. Verifies physical existence of the model artifact on local disk without attempting to parse multi-gigabyte weights.
3. Enforces context window bounds (`requested_context <= max_context`).

## Contract Behavior

- **Context Boundary**: With a `max_context=2048` GGUF manifest, request `1024` is accepted (`allocated_context=1024`), while request `4096` is rejected with `ValueError`.
- **Missing File**: A non-existent file path immediately raises `FileNotFoundError` without launching any backend process.
- **Dummy Fixture**: Tests and demonstrations use a minimal binary header fixture (`create_dummy_gguf_file`), ensuring quick test runs without downloading multi-gigabyte models.

## Scope & Limitations

> [!NOTE] Simulation Notice
> This preflight check validates file existence, header metadata, and configuration limits. It does **not** evaluate tensor numerical precision, check SIMD/AVX instruction set support on the host CPU, or benchmark token throughput.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module04/applied-labs/r04-t007 -p "test_*.py"
```
