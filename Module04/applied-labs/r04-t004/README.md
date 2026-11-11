# Applied Lab R04-T004: Optimization-Stage Ordering — Invariant & State Trace

## Overview

Model optimization pipelines for edge deployment require a strict topological order:
1. **Export**: Convert source weights to target intermediate representation (e.g., ONNX, GGUF).
2. **Quantize**: Compress numerical precision (e.g., INT8, INT4, AWQ, GPTQ).
3. **Benchmark**: Profile latency, memory footprint, and quality on target runtimes.

Executing benchmark before quantize produces unrepresentative performance profiles, and referencing unknown artifacts breaks deployment provenance.

## Pipeline Contract

- **Accepted Order**: `[export, quantize, benchmark]` with matching input/output artifact IDs.
- **Order Violations**: Executing `benchmark` before `quantize` or any other permutation raises `ValueError`.
- **Lineage Integrity**: Any stage consuming an unregistered artifact ID raises `ValueError`.
- **State Trace Invariant**: Intermediate states record cumulative artifact availability. The final benchmark report is linked back to the original source model.

## Scope & Limitations

> [!NOTE] Simulation Notice
> This validator inspects optimization manifests and plans statically in Python. It does not invoke native compilers (e.g., `cmake`, `onnxruntime`, `llama.cpp` binaries) or measure hardware power draw.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module04/applied-labs/r04-t004 -p "test_*.py"
```
