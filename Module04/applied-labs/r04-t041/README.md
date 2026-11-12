# R04-T041 - Optimization-stage ordering (runnable concept example)

Companion to [Module04/04.openvino.md](../../04.openvino.md), Section 4
("OpenVINO Toolkit Optimization Suite").

## What it teaches
An optimization pipeline has a fixed order - **export -> quantize -> benchmark** -
and every stage must read only artifacts that already exist. `example.py` checks a
plan *before* anything runs (validation before execution).

| Public part | Meaning in the lesson |
|---|---|
| `Stage(name, inputs, outputs)` | one pipeline step; `inputs`/`outputs` are artifact IDs (provenance) |
| `validate_plan(plan, starting_artifacts)` | returns the stage names if the plan is valid, else raises `PlanError` |
| `PlanError.code` | which rule failed: `OUT_OF_ORDER`, `UNKNOWN_ARTIFACT`, `UNKNOWN_STAGE`, `DUPLICATE_STAGE`, `DUPLICATE_ARTIFACT`, `EMPTY_PLAN` |

## Run
```bash
python3 Module04/applied-labs/r04-t041/example.py
python3 -m unittest discover -s Module04/applied-labs/r04-t041 -p "test_*.py"
```
Needs only Python 3 and the standard library. No model download, GPU, cloud service or device.

## Expected output
```
starting artifacts: ['source_model']
good plan: ACCEPTED ['export', 'quantize', 'benchmark']
benchmark before quantize: REJECTED OUT_OF_ORDER: 'quantize' cannot come after 'benchmark'
unknown artifact: REJECTED UNKNOWN_ARTIFACT: stage 'quantize' reads 'ov_int8_typo', which no earlier stage produced
```

## Limits (what this is NOT)
This is a **simulation of plan checking only**. It does not call OpenVINO, convert or
quantize any model, and makes no claim about real hardware, cloud behaviour or the speed
or accuracy of any trained model. Stages are plain data.
