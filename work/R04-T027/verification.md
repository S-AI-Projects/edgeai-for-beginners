# Verification Log — R04-T027

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Worked example regression | `ram_budget_gb=6`, `requested_context=1024` | `eligible=['Model-A']`, `excluded={'Model-B': ['ram_exceeds_budget (needs 8 > budget 6)']}` | Identical (`actual == EXPECTED_WORKED_OUTPUT`) | PASS |
| Boundary both admitted | `ram_budget_gb=8`, `requested_context=2048` | `eligible=['Model-A', 'Model-B']`, `excluded={}` | Identical | PASS |
| Context exclusion | `ram_budget_gb=8`, `requested_context=3072` | `eligible=['Model-B']`, `excluded={'Model-A': ['context_below_request (max 2048 < requested 3072)']}` | Identical | PASS |
| Invalid inputs | `ram_budget_gb=-1` / `requested_context=0` / missing fields | Raises `ValueError` | Raised `ValueError` | PASS |

## Example Script Output
```text
$ python3 Module02/applied-labs/r04-t027/example.py
=== R04-T027 Worked Model-Manifest Selection (Synthetic Fixture) ===
Input: ram_budget_gb=6, requested_context=1024
Output: {'eligible': ['Model-A'], 'excluded': {'Model-B': ['ram_exceeds_budget (needs 8 > budget 6)']}, 'ram_budget_gb': 6, 'requested_context': 1024, 'fixture_note': 'Invented synthetic teaching fixture, not a claim about real Phi models or hardware.'}
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module02/applied-labs/r04-t027 -p "test_*.py"
test_context_exclusion_reported (test_example.TestPhiManifestWorkedExample.test_context_exclusion_reported)
Budget RAM 8 with requested context 3072 excludes Model-A for insufficient context. ... ok
test_exact_boundary_both_admitted (test_example.TestPhiManifestWorkedExample.test_exact_boundary_both_admitted)
Budget RAM 8 and requested context 2048 admits both Model-A and Model-B. ... ok
test_exact_worked_example_regression (test_example.TestPhiManifestWorkedExample.test_exact_worked_example_regression)
Regression test executing the exact published input-to-output worked example. ... ok
test_invalid_inputs_rejected (test_example.TestPhiManifestWorkedExample.test_invalid_inputs_rejected) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module02/applied-labs/r04-t027'); from example import run_worked_example; r = run_worked_example(); assert r['eligible'] == ['Model-B'], 'deliberate wrong worked output'"
AssertionError: deliberate wrong worked output
Exit code: 1
```
