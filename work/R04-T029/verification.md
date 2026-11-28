# Verification Log — R04-T029

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Config 1 (`small_512`) | `format="GGUF"`, `dummy_model.gguf`, `max_context=2048`, `req=512` | `accepted=True`, `correct=True`, `utilization=0.25`, `headroom=1536`, `launch_calls=1` | Identical | PASS |
| Config 2 (`medium_1024`) | `format="GGUF"`, `dummy_model.gguf`, `max_context=2048`, `req=1024` | `accepted=True`, `correct=True`, `utilization=0.5`, `headroom=1024`, `launch_calls=1` | Identical | PASS |
| Boundary exact (`2048`) | `format="GGUF"`, `dummy_model.gguf`, `max_context=2048`, `req=2048` | `accepted=True`, `headroom=0`, `utilization=1.0` | Identical | PASS |
| Config 3 (`oversized_4096`) | `format="GGUF"`, `dummy_model.gguf`, `max_context=2048`, `req=4096` | Raises `PreflightValidationError`, `launch_calls=0` | Identical | PASS |
| Missing path | `path="nonexistent_weights.gguf"`, `req=1024` | Raises `PreflightValidationError`, `launch_calls=0` | Identical | PASS |
| Unsupported format | `format="SAFETENSORS"`, `dummy_model.gguf`, `req=1024` | Raises `PreflightValidationError`, `launch_calls=0` | Identical | PASS |

## Example Script Output
```text
$ python3 Module04/applied-labs/r04-t029/example.py
=== R04-T029 Local Model-File Preflight & Controlled Experiment ===
[small_512] req=512/2048 -> accepted=True, correct=True, utilization=0.25, headroom=1536, launch_calls=1
[medium_1024] req=1024/2048 -> accepted=True, correct=True, utilization=0.5, headroom=1024, launch_calls=1
[oversized_4096] req=4096/2048 -> accepted=False, correct=True, utilization=2.0, headroom=-2048, launch_calls=0
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module04/applied-labs/r04-t029 -p "test_*.py"
test_controlled_three_config_experiment_correctness_and_tradeoff (test_example.TestLlamaCppManifestPreflight.test_controlled_three_config_experiment_correctness_and_tradeoff)
Three controlled configurations report expected correctness and headroom trade-offs. ... ok
test_exact_boundary_2048_accepted (test_example.TestLlamaCppManifestPreflight.test_exact_boundary_2048_accepted)
Exact boundary requested_context == max_context (2048) is accepted with 0 headroom. ... ok
test_gguf_manifest_accepts_1024_and_launches_once (test_example.TestLlamaCppManifestPreflight.test_gguf_manifest_accepts_1024_and_launches_once)
GGUF manifest with max_context=2048 accepts request 1024 and invokes launcher once. ... ok
test_missing_model_path_fails_without_launching (test_example.TestLlamaCppManifestPreflight.test_missing_model_path_fails_without_launching)
Missing local model path fails preflight before any launcher call. ... ok
test_request_4096_rejected_without_launching (test_example.TestLlamaCppManifestPreflight.test_request_4096_rejected_without_launching)
Request 4096 exceeds max_context=2048 and rejects without launching backend. ... ok
test_unsupported_format_rejected_without_launching (test_example.TestLlamaCppManifestPreflight.test_unsupported_format_rejected_without_launching) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module04/applied-labs/r04-t029'); from example import DEFAULT_DUMMY_PATH, validate_and_launch_manifest; r = validate_and_launch_manifest({'format': 'GGUF', 'path': str(DEFAULT_DUMMY_PATH), 'max_context': 2048}, 1024); assert r['headroom_tokens'] == 0, 'deliberate wrong headroom'"
AssertionError: deliberate wrong headroom
Exit code: 1
```
