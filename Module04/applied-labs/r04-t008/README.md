# Applied Lab R04-T008: Optimization-Stage Ordering — Failure and Recovery

## Overview

Microsoft Olive automates complex model optimization pipelines across multiple chained passes:
1. `export`: Translates model weights into ONNX intermediate representation.
2. `quantize`: Compresses precision (e.g. INT8 or INT4).
3. `benchmark`: Measures latency and throughput against target hardware execution providers.

In automated edge MLOps pipelines, submitting invalid execution requests—such as attempting to benchmark before quantization or referencing missing artifact dependencies—must be intercepted with actionable diagnostic errors, and the system must gracefully recover upon receiving a corrected plan.

## Failure & Recovery Contract

- **Acceptance Rule**: `[export, quantize, benchmark]` passes with sequential artifact chaining.
- **Order Failure**: Invoking `benchmark` prior to `quantize` halts execution and raises `OptimizationWorkflowError`.
- **Lineage Failure**: Specifying an unknown input artifact ID halts execution and raises `OptimizationWorkflowError`.
- **Fault Recovery**: Catching the validation error leaves the validator state uncorrupted; a corrected plan executes successfully on the subsequent invocation.

## Scope & Limitations

> [!NOTE] Simulation Notice
> This validator tests graph sequencing and artifact integrity checks in memory. It does not invoke actual Olive engine passes, GPU compilers, or hardware execution providers.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module04/applied-labs/r04-t008 -p "test_*.py"
```
