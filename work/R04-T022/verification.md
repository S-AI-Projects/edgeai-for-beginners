# Verification Log — R04-T022

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Smallest valid (empty) | `prompt=""`, `budget=0` | `retained_tokens=[]`, `removed_count=0`, `truncated=False`, `boundary_case="smallest_valid_empty"` | `retained_tokens=[]`, `removed_count=0`, `truncated=False`, `boundary_case="smallest_valid_empty"` | PASS |
| Smallest valid (single) | `prompt="edge"`, `budget=1` | `retained_tokens=['edge']`, `removed_count=0`, `truncated=False`, `boundary_case="exact_budget_boundary"` | `retained_tokens=['edge']`, `removed_count=0`, `truncated=False`, `boundary_case="exact_budget_boundary"` | PASS |
| Exact boundary | `prompt="one two three"`, `budget=3` | `retained_tokens=['one', 'two', 'three']`, `removed_count=0`, `truncated=False` | `retained_tokens=['one', 'two', 'three']`, `removed_count=0`, `truncated=False` | PASS |
| Over boundary by 1 | `prompt="one two three four"`, `budget=3` | `retained_tokens=['one', 'two', 'three']`, `removed_count=1`, `truncated=True` | `retained_tokens=['one', 'two', 'three']`, `removed_count=1`, `truncated=True` | PASS |
| Zero budget non-empty | `prompt="one"`, `budget=0` | `retained_tokens=[]`, `removed_count=1`, `truncated=True` | `retained_tokens=[]`, `removed_count=1`, `truncated=True` | PASS |
| Invalid negative budget | `prompt="one two"`, `budget=-1` | Raises `ValueError` | Raised `ValueError` | PASS |
| Invalid types (`bool` / `int` prompt) | `budget=True` / `prompt=123` | Raises `TypeError` | Raised `TypeError` | PASS |

## Example Script Output
```text
$ python3 Module05/applied-labs/r04-t022/example.py
=== R04-T022 Token-Budget Preflight (Teaching Approximation) ===
[smallest_valid_empty] prompt='' -> retained=[], removed=0, truncated=False, case=smallest_valid_empty
[smallest_valid_single] prompt='edge' -> retained=['edge'], removed=0, truncated=False, case=exact_budget_boundary
[exact_boundary] prompt='one two three' -> retained=['one', 'two', 'three'], removed=0, truncated=False, case=exact_budget_boundary
[over_budget_by_one] prompt='one two three four' -> retained=['one', 'two', 'three'], removed=1, truncated=True, case=over_budget_truncated
[zero_budget_non_empty] prompt='one' -> retained=[], removed=1, truncated=True, case=zero_budget_boundary
[invalid_negative_budget] budget=-1 -> ValueError: budget must be non-negative (>= 0).
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module05/applied-labs/r04-t022 -p "test_*.py"
test_exact_boundary_keeps_all_tokens (test_example.TestSLMOpsTokenBudgetBoundaries.test_exact_boundary_keeps_all_tokens) ... ok
test_invalid_negative_budget_rejected (test_example.TestSLMOpsTokenBudgetBoundaries.test_invalid_negative_budget_rejected) ... ok
test_invalid_types_rejected (test_example.TestSLMOpsTokenBudgetBoundaries.test_invalid_types_rejected) ... ok
test_over_budget_by_one_truncates_fourth_token (test_example.TestSLMOpsTokenBudgetBoundaries.test_over_budget_by_one_truncates_fourth_token) ... ok
test_smallest_valid_empty_prompt_zero_budget (test_example.TestSLMOpsTokenBudgetBoundaries.test_smallest_valid_empty_prompt_zero_budget) ... ok
test_smallest_valid_single_token (test_example.TestSLMOpsTokenBudgetBoundaries.test_smallest_valid_single_token) ... ok
test_whitespace_only_input_retains_none (test_example.TestSLMOpsTokenBudgetBoundaries.test_whitespace_only_input_retains_none) ... ok
test_zero_budget_with_non_empty_prompt_drops_all (test_example.TestSLMOpsTokenBudgetBoundaries.test_zero_budget_with_non_empty_prompt_drops_all) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module05/applied-labs/r04-t022'); from example import check_token_budget; r = check_token_budget('one two three four', 3); assert r['removed_count'] == 99, 'deliberate wrong boundary result'"
AssertionError: deliberate wrong boundary result
Exit code: 1
```
