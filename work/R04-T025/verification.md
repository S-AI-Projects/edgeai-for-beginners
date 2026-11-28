# Verification Log — R04-T025

## Tool Versions
- `python3 --version`: `Python 3.14.7`
- `git --version`: `git version 2.54.0 (Apple Git-157)`

## Inputs, Expected vs Actual Results

| Scenario | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Negotiated dispatch via adapter | `client={"tools", "resources"}`, `server={"tools", "prompts"}`, call `"tools"` | Negotiates `["tools"]`, dispatches via `DeterministicLocalAdapter (mock)`, `len(dispatched_calls)==1` | Identical | PASS |
| Unnegotiated rejection | Same negotiated state, call `"resources"` | Raises `CapabilityNotNegotiatedError` before calling adapter (`dispatched_calls` unchanged) | Raised `CapabilityNotNegotiatedError`, `dispatched_calls` unchanged | PASS |
| Callable interface decoupling | Custom `fake_callable` returning `{"prompts"}` | Negotiates `{"prompts"}`, allows `"prompts"`, rejects `"tools"` | Identical | PASS |
| Empty capability name | `call_capability("")` | Raises `ValueError` | Raised `ValueError` | PASS |

## Example Script Output
```text
$ python3 Module08/applied-labs/r04-t025/example.py
=== R04-T025 Capability Negotiation — Offline Service Adapter (Mock) ===
Negotiated capabilities: ['tools']
Dispatched 'tools': DeterministicLocalAdapter (mock) | payload: {'prompt': 'hello'}
Rejected 'resources' before dispatch: Capability 'resources' not in negotiated set ['tools']; rejected before calling service adapter.
Adapter dispatch count after rejection: 1
```

## Unit Test Output
```text
$ python3 -m unittest discover -v -s Module08/applied-labs/r04-t025 -p "test_*.py"
test_custom_callable_stub_proves_interface_decoupling (test_example.TestOfflineServiceAdapter.test_custom_callable_stub_proves_interface_decoupling)
Any callable matching the ServiceBackend interface works without concrete adapter class. ... ok
test_empty_capability_rejected (test_example.TestOfflineServiceAdapter.test_empty_capability_rejected) ... ok
test_negotiate_and_dispatch_through_callable_adapter (test_example.TestOfflineServiceAdapter.test_negotiate_and_dispatch_through_callable_adapter)
Client {tools,resources} + server {tools,prompts} negotiates {tools} and dispatches via adapter. ... ok
test_unnegotiated_capability_rejected_before_adapter_dispatch (test_example.TestOfflineServiceAdapter.test_unnegotiated_capability_rejected_before_adapter_dispatch)
Calling 'resources' raises before the callable adapter's dispatch branch is ever invoked. ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```
Exit code: `0`

## Deliberate Failure Verification
```text
$ python3 -c "import sys; sys.path.insert(0, 'Module08/applied-labs/r04-t025'); from example import DeterministicLocalAdapter, CapabilityGateway; a = DeterministicLocalAdapter({'tools', 'prompts'}); g = CapabilityGateway({'tools', 'resources'}, a); assert g.negotiate() == {'tools', 'resources'}, 'deliberate wrong intersection'"
AssertionError: deliberate wrong intersection
Exit code: 1
```
