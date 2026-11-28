# Verification Log — R04-T023

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Primary fixture | `ram_budget_gb=6`, `requested_context=1024` | `eligible=['Model-A']`, `excluded={'Model-B': ['ram_exceeds_budget (needs 8 > budget 6)']}`, matches independent & table | Identical (`matches_independent=True`, `matches_table=True`) | PASS |
| Both eligible | `ram_budget_gb=8`, `requested_context=1024` | `eligible=['Model-A', 'Model-B']`, `excluded={}` | Identical (`matches_independent=True`, `matches_table=True`) | PASS |
| Boundary RAM & context | `ram_budget_gb=4`, `requested_context=2048` | `eligible=['Model-A']`, `Model-B` excluded for RAM | Identical | PASS |
| Context & RAM fail | `ram_budget_gb=2`, `requested_context=8192` | `eligible=[]`, both fail RAM & context (2 reasons each) | Identical | PASS |
| Invalid budget / manifest | `ram_budget_gb=0` / `requested_context=-1` / missing fields | Raises `ValueError` | Raised `ValueError` | PASS |

## Example Script Output
```text
$ python3 Module02/applied-labs/r04-t023/example.py
=== R04-T023 Model-Manifest Selection Comparison (Synthetic Fixture) ===
RAM=6, ctx=1024 -> eligible=['Model-A'], excluded={'Model-B': ['ram_exceeds_budget (needs 8 > budget 6)']}, matches_independent=True, matches_table=True
RAM=8, ctx=1024 -> eligible=['Model-A', 'Model-B'], excluded={}, matches_independent=True, matches_table=True
RAM=6, ctx=3072 -> eligible=[], excluded={'Model-A': ['context_below_request (max 2048 < requested 3072)'], 'Model-B': ['ram_exceeds_budget (needs 8 > budget 6)']}, matches_independent=True, matches_table=True
RAM=8, ctx=4096 -> eligible=['Model-B'], excluded={'Model-A': ['context_below_request (max 2048 < requested 4096)']}, matches_independent=True, matches_table=True
RAM=3, ctx=1024 -> eligible=[], excluded={'Model-A': ['ram_exceeds_budget (needs 4 > budget 3)'], 'Model-B': ['ram_exceeds_budget (needs 8 > budget 3)']}, matches_independent=True, matches_table=True
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module02/applied-labs/r04-t023 -p "test_*.py"
test_boundary_exact_ram_and_context_match (test_example.TestGemmaManifestSelectionComparison.test_boundary_exact_ram_and_context_match) ... ok
test_context_and_ram_combined_failure_reasons (test_example.TestGemmaManifestSelectionComparison.test_context_and_ram_combined_failure_reasons) ... ok
test_direct_matches_independent_and_expected_table_across_all_rows (test_example.TestGemmaManifestSelectionComparison.test_direct_matches_independent_and_expected_table_across_all_rows) ... ok
test_invalid_inputs_rejected (test_example.TestGemmaManifestSelectionComparison.test_invalid_inputs_rejected) ... ok
test_primary_fixture_admits_only_model_a (test_example.TestGemmaManifestSelectionComparison.test_primary_fixture_admits_only_model_a) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module02/applied-labs/r04-t023'); from example import SYNTHETIC_MANIFEST, select_eligible_models; r = select_eligible_models(SYNTHETIC_MANIFEST, 6, 1024); assert r['eligible'] == ['Model-A', 'Model-B'], 'deliberate wrong eligibility'"
AssertionError: deliberate wrong eligibility
Exit code: 1
```
