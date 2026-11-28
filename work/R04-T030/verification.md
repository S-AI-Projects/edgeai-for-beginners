# Verification Log — R04-T030

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Q1 (Predict output) | `prompt="one two three four"`, `budget=3` | `retained_tokens=['one', 'two', 'three']`, `removed_count=1`, `truncated=True` | Identical | PASS |
| Q2 (Diagnose failure) | `prompt="alpha beta"`, `budget=-2` | Raises `ValueError` | Raised `ValueError` | PASS |
| Q3 (Exact fit boundary) | `prompt="one two three"`, `budget=3` | `retained_tokens=['one', 'two', 'three']`, `removed_count=0`, `truncated=False` | Identical | PASS |
| Q3 (Zero budget policy) | `prompt="one"`, `budget=0` | `retained_tokens=[]`, `removed_count=1`, `truncated=True` | Identical | PASS |
| Empty input | `prompt=""` / `"   \t\n"`, `budget=3` | `retained_tokens=[]`, `removed_count=0`, `truncated=False` | Identical | PASS |
| Invalid types | `budget=True` / `prompt=42` | Raises `TypeError` | Raised `TypeError` | PASS |

## Example Script Output
```text
$ python3 Module03/applied-labs/r04-t030/example.py
=== R04-T030 Token-Budget Preflight Scenario Assessment ===
Q1 (predict output): {'retained_tokens': ['one', 'two', 'three'], 'retained_count': 3, 'removed_count': 1, 'truncated': True, 'tokenizer_note': "Teaching approximation (whitespace split), not the model's real tokenizer."}
Q2 (diagnose failure): ValueError raised as expected: budget must be non-negative (>= 0).
Q3 (boundary exact): {'retained_tokens': ['one', 'two', 'three'], 'retained_count': 3, 'removed_count': 0, 'truncated': False, 'tokenizer_note': "Teaching approximation (whitespace split), not the model's real tokenizer."}
Q3 (boundary zero): {'retained_tokens': [], 'retained_count': 0, 'removed_count': 1, 'truncated': True, 'tokenizer_note': "Teaching approximation (whitespace split), not the model's real tokenizer."}
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module03/applied-labs/r04-t030 -p "test_*.py"
test_empty_input_retains_none (test_example.TestSLMScenarioAssessment.test_empty_input_retains_none)
Empty and whitespace-only inputs retain zero tokens with no truncation. ... ok
test_invalid_argument_types_rejected (test_example.TestSLMScenarioAssessment.test_invalid_argument_types_rejected) ... ok
test_q1_predict_output_budget_3_four_tokens (test_example.TestSLMScenarioAssessment.test_q1_predict_output_budget_3_four_tokens)
Q1 executable check: budget 3 with 'one two three four' retains 3 and removes 1. ... ok
test_q2_diagnose_failure_negative_budget (test_example.TestSLMScenarioAssessment.test_q2_diagnose_failure_negative_budget)
Q2 executable check: negative budget fails with ValueError rather than silent slicing. ... ok
test_q3_choose_boundary_policy_exact_and_zero (test_example.TestSLMScenarioAssessment.test_q3_choose_boundary_policy_exact_and_zero)
Q3 executable check: len==budget keeps all tokens; budget=0 drops all tokens. ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module03/applied-labs/r04-t030'); from example import check_token_budget; r = check_token_budget('one two three four', 3); assert r['removed_count'] == 0, 'deliberate wrong truncation count'"
AssertionError: deliberate wrong truncation count
Exit code: 1
```
