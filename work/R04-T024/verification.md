# Verification Log — R04-T024

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Negotiated invocation | `client={"tools", "resources"}`, `server={"tools", "prompts"}`, invoke `"tools"` | `negotiated=["tools"]`, `status="dispatched"`, `dispatch_count=1`, invariant passes | Identical (`status="dispatched"`, `dispatch_count=1`) | PASS |
| Unnegotiated invocation | `client={"tools", "resources"}`, `server={"tools", "prompts"}`, invoke `"resources"` | Raises `CapabilityNotNegotiatedError` before dispatch (`dispatch_log=[]`), invariant passes | Raised `CapabilityNotNegotiatedError`, `dispatch_log=[]` | PASS |
| Disjoint capability sets | `client={"resources"}`, `server={"prompts"}`, invoke `"prompts"` | `negotiated=set()`, raises `CapabilityNotNegotiatedError` | Identical | PASS |
| Deliberate invariant violation | `verify_trace_invariants` with corrupted `status="dispatched"` on rejected trace | Raises `AssertionError` | Raised `AssertionError` | PASS |
| Invalid capability name | `invoke("   ")` | Raises `ValueError` | Raised `ValueError` | PASS |

## Example Script Output
```text
$ python3 Module08/applied-labs/r04-t024/example.py
=== R04-T024 Capability Negotiation & State Trace (Simulation) ===
Allowed call 'tools': status=dispatched, negotiated=['tools']
Blocked call 'resources': Capability 'resources' rejected before dispatch; negotiated capabilities=['tools']. (dispatch_count=1)
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module08/applied-labs/r04-t024 -p "test_*.py"
test_disjoint_sets_negotiate_empty_and_reject_all (test_example.TestCapabilityNegotiationStateTrace.test_disjoint_sets_negotiate_empty_and_reject_all)
Disjoint capability sets negotiate empty set and reject every capability. ... ok
test_empty_capability_name_rejected (test_example.TestCapabilityNegotiationStateTrace.test_empty_capability_name_rejected) ... ok
test_intersect_and_dispatch_negotiated_capability (test_example.TestCapabilityNegotiationStateTrace.test_intersect_and_dispatch_negotiated_capability)
Client {tools,resources} and server {tools,prompts} negotiate {tools} and allow dispatch. ... ok
test_invariant_checker_fails_on_deliberate_wrong_state (test_example.TestCapabilityNegotiationStateTrace.test_invariant_checker_fails_on_deliberate_wrong_state)
A deliberate invariant violation (claiming dispatch when unnegotiated) must fail. ... ok
test_unnegotiated_capability_rejected_before_dispatch (test_example.TestCapabilityNegotiationStateTrace.test_unnegotiated_capability_rejected_before_dispatch)
Calling 'resources' fails pre-dispatch gate without incrementing dispatch_log. ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module08/applied-labs/r04-t024'); from example import CapabilityTraceSession, verify_trace_invariants; s = CapabilityTraceSession({'tools', 'resources'}, {'tools', 'prompts'}); r = s.invoke('tools'); verify_trace_invariants(r['trace'], {'status': 'rejected', 'dispatch_count': 0})"
AssertionError: Invariant violated: negotiated capability was rejected.
Exit code: 1
```
