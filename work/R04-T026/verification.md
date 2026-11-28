# Verification Log — R04-T026

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Freeze `encoder` | `{"encoder": 100, "head": 20}`, `["encoder"]` | `total=120`, `trainable=20`, `frozen=100`, `unmatched_prefixes=[]`, `baseline == refactored` | Identical (`equivalent=True`) | PASS |
| Unmatched freeze prefix | `{"encoder": 100, "head": 20}`, `["encoder", "adapter"]` | `total=120`, `trainable=20`, `unmatched_prefixes=['adapter']`, `baseline == refactored` | Identical (`equivalent=True`) | PASS |
| No freeze prefixes | `{"encoder": 100, "head": 20}`, `[]` | `total=120`, `trainable=120`, `frozen=0`, `unmatched_prefixes=[]`, `baseline == refactored` | Identical (`equivalent=True`) | PASS |
| Invalid count / empty prefix | `{"encoder": -5}` or `prefixes=[""]` | Raises `ValueError` | Raised `ValueError` | PASS |

## Example Script Output
```text
$ python3 Module05/applied-labs/r04-t026/example.py
=== R04-T026 Trainable-Parameter Accounting (Baseline vs Refactored) ===
freeze=['encoder'] -> total=120, trainable=20, frozen=100, unmatched=[], equivalent=True
freeze=['encoder', 'adapter'] -> total=120, trainable=20, frozen=100, unmatched=['adapter'], equivalent=True
freeze=[] -> total=120, trainable=120, frozen=0, unmatched=[], equivalent=True
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module05/applied-labs/r04-t026 -p "test_*.py"
test_before_after_equivalence_across_multiple_fixtures (test_example.TestParameterAccountingRefactor.test_before_after_equivalence_across_multiple_fixtures)
Baseline and refactored functions stay equivalent across empty, full-freeze, and multi-layer manifests. ... ok
test_encoder_frozen_yields_total_120_trainable_20 (test_example.TestParameterAccountingRefactor.test_encoder_frozen_yields_total_120_trainable_20)
encoder:100, head:20 with encoder frozen gives total=120, trainable=20. ... ok
test_extracted_responsibility_classify_freeze_matches (test_example.TestParameterAccountingRefactor.test_extracted_responsibility_classify_freeze_matches) ... ok
test_invalid_manifest_or_prefix_rejected (test_example.TestParameterAccountingRefactor.test_invalid_manifest_or_prefix_rejected) ... ok
test_unmatched_freeze_prefix_reported_and_equivalent (test_example.TestParameterAccountingRefactor.test_unmatched_freeze_prefix_reported_and_equivalent)
Unmatched prefix 'decoder' is reported identically before and after refactor. ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module05/applied-labs/r04-t026'); from example import account_parameters_refactored; r = account_parameters_refactored({'encoder': 100, 'head': 20}, ['encoder']); assert r['trainable'] == 120, 'deliberate wrong trainable count'"
AssertionError: deliberate wrong trainable count
Exit code: 1
```
