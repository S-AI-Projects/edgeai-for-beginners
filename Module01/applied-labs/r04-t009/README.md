# Applied Lab R04-T009: Installation Preflight Report — Evaluation Experiment

## Overview

Setting up edge developer workstations or edge compute gateways requires verifying software toolchains and configuration profiles before executing tasks.

This lab provides an **Environment Preflight Checker** and an **Evaluation Experiment** comparing three configuration sizes:
- **Minimal Tier**: 2 binaries, 2 config keys.
- **Standard Tier**: 4 binaries, 4 config keys.
- **Enterprise Tier**: 6 binaries, 6 config keys.

## Evaluation Experiment Trade-offs

| Profile Tier | Total Checks | Pass / Fail | Failure Breakdown | Secret Redaction |
|---|---|---|---|---|
| `tier_minimal` | 4 | PASS | 0 missing | 100% |
| `tier_standard` | 8 | PASS | 0 missing | 100% |
| `tier_enterprise` | 12 | FAIL | 1 missing binary, 1 missing config | 100% |

- **Trade-off Observation**: Increasing preflight scope linearly increases check count while retaining sub-millisecond execution times in local memory. Failure isolation successfully distinguishes executable defects from configuration omissions.

## Scope & Limitations

> [!NOTE] Non-Functional Mock Notice
> This experiment benchmarks preflight check count and error isolation across synthetic input dictionaries. It does **not** assert real-world model accuracy, GPU FLOPs, or network bandwidth.

## Verification & Execution

### Run Evaluation Experiment Demo
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module01/applied-labs/r04-t009 -p "test_*.py"
```
