# R04-T044 - Optimization-stage ordering: offline service adapter

Companion to [Module04/04.openvino.md](../../04.openvino.md)
("Section 4 : OpenVINO Toolkit Optimization Suite").

## How this illustrates the lesson, and where it stops
The lesson walks through exporting a model to OpenVINO IR, compressing or quantizing it with
NNCF, and then timing inference, and its "Output Structure" shows the model files each step
leaves behind. `example.py` keeps only the shape of that workflow: a plan of three stages in
a fixed order, **export -> quantize -> benchmark**, where each stage records the artifact IDs it
reads and writes, and the whole plan is checked **before** anything runs.

**Simplifications:** stages are plain data and artifacts are text labels. Nothing is exported,
quantized or timed, none of the lesson's code is run, and the lesson's NNCF/OpenVINO API calls
are not reproduced here.

## The external dependency behind a callable interface
The real work would be done by an external service. `execute_plan()` only knows this interface:

```
runner(stage, inputs) -> {output_artifact_id: descriptor}
```

| Part | Role |
|---|---|
| `validate_plan(plan, starting_artifacts)` | checks order and artifact provenance; runs nothing |
| `execute_plan(plan, starting_artifacts, runner)` | validates first, then calls `runner` once per stage |
| `LocalOfflineAdapter` | the deterministic local stand-in: same stage + inputs give the same `sim-...` labels |
| `FlakyAdapter` | wraps an adapter and fails at a chosen stage, to test failure handling |
| `PlanError.code` | `EMPTY_PLAN`, `UNKNOWN_STAGE`, `DUPLICATE_STAGE`, `OUT_OF_ORDER`, `MISSING_INPUT`, `MISSING_OUTPUT`, `UNKNOWN_ARTIFACT`, `DUPLICATE_ARTIFACT` |
| `AdapterError.code` | `BAD_OUTPUTS` (adapter broke the interface), `ADAPTER_FAILED` (adapter raised) |

## What this mock does NOT establish about the real service
- That OpenVINO, NNCF or any converter can actually export or quantize a given model.
- Any real latency, throughput, memory or accuracy number: a benchmark output here is just a label.
- Real service failures: timeouts, partial writes, version mismatches, missing devices or credentials.
- That the artifacts are valid IR/model files or are compatible with any particular device.

## Run
```bash
python3 Module04/applied-labs/r04-t044/example.py
python3 -m unittest discover -s Module04/applied-labs/r04-t044 -p "test_*.py"
```
Python 3 standard library only. No model download, paid provider, GPU or device.

## Expected output
```
starting artifacts: ['source_model']
good plan [export, quantize, benchmark]: ACCEPTED and run through LocalOfflineAdapter
  export: reads ['source_model'] -> writes ov_ir = sim-export-05aa1b72
  quantize: reads ['ov_ir'] -> writes ov_int8 = sim-quantize-d9759e1c
  benchmark: reads ['ov_int8'] -> writes bench_report = sim-benchmark-5a2e77c1
  adapter calls: ['export', 'quantize', 'benchmark']
benchmark before quantize: REJECTED OUT_OF_ORDER (adapter calls: 0)
unknown artifact reference: REJECTED UNKNOWN_ARTIFACT (adapter calls: 0)
adapter fails at quantize: ADAPTER_FAILED; stages completed before it: ['export']
not established by this mock:
  - That OpenVINO, NNCF or any converter can actually export or quantize a given model.
  - Any real latency, throughput, memory or accuracy number: a benchmark output here is just a label.
  - Real service failures: timeouts, partial writes, version mismatches, missing devices or credentials.
  - That the artifacts are valid IR/model files or are compatible with any particular device.
```

## Limits
This is a simulation of plan checking and adapter plumbing. It makes no claim about real
hardware, cloud service behaviour, or the performance of any trained model.
