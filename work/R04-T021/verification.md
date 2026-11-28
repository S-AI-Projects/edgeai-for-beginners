# Verification Log — R04-T021

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Normal (over budget) | `prompt="one two three four"`, `budget=3` | `retained_tokens=['one', 'two', 'three']`, `retained_count=3`, `removed_count=1`, `truncated=True` | `retained_tokens=['one', 'two', 'three']`, `retained_count=3`, `removed_count=1`, `truncated=True` | PASS |
| Within budget | `prompt="edge ai"`, `budget=5` | `retained_tokens=['edge', 'ai']`, `retained_count=2`, `removed_count=0`, `truncated=False` | `retained_tokens=['edge', 'ai']`, `retained_count=2`, `removed_count=0`, `truncated=False` | PASS |
| Exact boundary | `prompt="one two three"`, `budget=3` | `retained_tokens=['one', 'two', 'three']`, `removed_count=0`, `truncated=False` | `retained_tokens=['one', 'two', 'three']`, `removed_count=0`, `truncated=False` | PASS |
| Empty / whitespace | `prompt=""` / `"   \t\n  "`, `budget=3` | `retained_tokens=[]`, `retained_count=0`, `removed_count=0`, `truncated=False` | `retained_tokens=[]`, `retained_count=0`, `removed_count=0`, `truncated=False` | PASS |
| Zero boundary | `prompt="one two"`, `budget=0` | `retained_tokens=[]`, `removed_count=2`, `truncated=True` | `retained_tokens=[]`, `removed_count=2`, `truncated=True` | PASS |
| Negative budget | `prompt="one two"`, `budget=-1` | Raises `ValueError` | Raised `ValueError` | PASS |

## Example Script Output
```text
$ python3 Module01/applied-labs/r04-t021/example.py
Prompt: 'one two three four' | Budget: 3
Preflight Result: {'retained_tokens': ['one', 'two', 'three'], 'retained_count': 3, 'removed_count': 1, 'truncated': True, 'tokenizer_note': 'Teaching approximation (whitespace split), not a real model tokenizer.'}
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module01/applied-labs/r04-t021 -p "test_*.py"
test_empty_input_retains_none (test_example.TestTokenBudgetPreflight.test_empty_input_retains_none)
Empty or whitespace-only input retains no tokens. ... ok
test_exact_boundary_budget (test_example.TestTokenBudgetPreflight.test_exact_boundary_budget)
Prompt matching exact budget boundary retains all tokens without truncation. ... ok
test_negative_budget_rejected (test_example.TestTokenBudgetPreflight.test_negative_budget_rejected)
Negative budget raises ValueError. ... ok
test_truncation_over_budget (test_example.TestTokenBudgetPreflight.test_truncation_over_budget)
Budget 3 with 'one two three four' retains 3 tokens and removes 1. ... ok
test_within_budget_no_truncation (test_example.TestTokenBudgetPreflight.test_within_budget_no_truncation)
Prompt strictly within budget retains all tokens and removes none. ... ok
test_zero_budget_truncates_all (test_example.TestTokenBudgetPreflight.test_zero_budget_truncates_all)
Zero budget is valid and truncates all tokens. ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module01/applied-labs/r04-t021'); from example import check_token_budget; r = check_token_budget('one two three four', 3); assert r['removed_count'] == 0, 'deliberate wrong expected value'"
AssertionError: deliberate wrong expected value
Exit code: 1
```
