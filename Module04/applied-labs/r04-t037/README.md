# R04-T037: Optimization-Stage Ordering and Artifact Provenance

## Overview
This lab extends `Module04/06.workflow-synthesis.md` by demonstrating validation of an Edge AI optimization pipeline plan before execution.

### Stage Ordering & Lineage Constraints
1. **Stage Precedence**:
   $$\text{export} \prec \text{quantize} \prec \text{benchmark}$$
   `[export, quantize, benchmark]` is accepted. Any out-of-order execution (e.g. `benchmark` before `quantize`) raises `INVALID_STAGE_ORDER`.
2. **Artifact Provenance**:
   - Each stage declares `input_artifact` and `output_artifact`.
   - The initial stage consumes an existing artifact (e.g. `model_raw`).
   - Every subsequent input artifact must have been produced by an earlier stage. Referencing an unknown or unproduced artifact raises `UNKNOWN_ARTIFACT_REFERENCE`.

## Execution
```bash
python3 Module04/applied-labs/r04-t037/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module04/applied-labs/r04-t037 -p "test_*.py"
```
