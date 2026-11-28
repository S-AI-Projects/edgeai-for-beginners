# Verification Log — R04-T028

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Missing manifest | `manifest=None`, `freeze=["encoder"]` | Raises `ManifestValidationError` ("missing or empty") | Raised `ManifestValidationError` | PASS |
| Negative count | `{"encoder": -10, "head": 20}`, `freeze=["encoder"]` | Raises `ManifestValidationError` ("invalid count") | Raised `ManifestValidationError` | PASS |
| Recovery valid fixture | `{"encoder": 100, "head": 20}`, `freeze=["encoder"]` | `total=120`, `trainable=20`, `frozen=100`, `unmatched=[]` | Identical | PASS |
| Unmatched freeze prefix | `{"encoder": 100, "head": 20}`, `freeze=["encoder", "decoder"]` | `total=120`, `trainable=20`, `unmatched=['decoder']` | Identical | PASS |

## Example Script Output
```text
$ python3 Module05/applied-labs/r04-t028/example.py
=== R04-T028 Trainable-Parameter Accounting — Failure & Recovery ===
[invalid_missing_manifest] ERROR: Manifest is missing or empty; provide at least one named parameter entry.
[invalid_negative_count] ERROR: Parameter 'encoder' has invalid count -10; expected non-negative int.
[recovery_valid_fixture] OK: total=120, trainable=20, frozen=100, unmatched=[]
[unmatched_prefix_case] OK: total=120, trainable=20, frozen=100, unmatched=['decoder']
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module05/applied-labs/r04-t028 -p "test_*.py"
test_missing_and_invalid_data_raise_explained_error (test_example.TestParameterAccountingFailureRecovery.test_missing_and_invalid_data_raise_explained_error)
Missing manifest or negative count raises ManifestValidationError with explanation. ... ok
test_recovery_on_next_valid_input_after_failure (test_example.TestParameterAccountingFailureRecovery.test_recovery_on_next_valid_input_after_failure)
Batch processor records error on invalid input and cleanly recovers on next valid manifest. ... ok
test_unmatched_freeze_prefix_reported (test_example.TestParameterAccountingFailureRecovery.test_unmatched_freeze_prefix_reported)
Unmatched freeze prefix is reported explicitly. ... ok
test_valid_fixture_encoder_frozen (test_example.TestParameterAccountingFailureRecovery.test_valid_fixture_encoder_frozen)
encoder:100, head:20 with encoder frozen gives total=120, trainable=20. ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module05/applied-labs/r04-t028'); from example import account_parameters; r = account_parameters({'encoder': 100, 'head': 20}, ['encoder']); assert r['trainable'] == 0, 'deliberate wrong trainable count'"
AssertionError: deliberate wrong trainable count
Exit code: 1
```
