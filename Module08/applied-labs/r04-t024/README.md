# R04-T024: Capability Negotiation — Invariant and State Trace

A deterministic local simulation illustrating capability discovery, set intersection, pre-dispatch gating, intermediate state tracing, and invariant verification.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module08/02.AzureAIFoundryIntegration.md`:** Integrating client applications with Azure AI Foundry / Foundry Local backends requires discovering supported capabilities on both sides, intersecting them, and gating feature invocation so unsupported features never reach dispatch.
- **Where simplifications stop:** Capabilities are modeled as static Python string sets in memory (`{"tools", "resources"}`, `{"tools", "prompts"}`). This simulation does **not** perform real Azure OpenAI / Foundry Local HTTP calls, SDK handshake protocols, credential validation, or network error handling.

## Intermediate State Trace & Invariants
Each session records ordered intermediate states:
1. `discover_client` — captures client capabilities.
2. `discover_server` — captures server capabilities.
3. `intersect_capabilities` — computes `client & server`.
4. `pre_dispatch_gate` — records `allowed = (requested in negotiated)` and `dispatch_count_before`.
5. `dispatched` or `rejected_before_dispatch` — records final dispatch state.

`verify_trace_invariants(trace, final_output)` enforces that `negotiated == client & server`, gate matches intersection, and unnegotiated calls never increment `dispatch_count`.

## Files
- `example.py` — `CapabilityTraceSession`, `CapabilityNotNegotiatedError`, and `verify_trace_invariants`.
- `test_example.py` — Unit tests verifying negotiation, pre-dispatch rejection, disjoint sets, and invariant failure detection.

## Prerequisites
- Python 3 standard library only (no Azure credentials, model download, or GPU required).

## Usage & Verification
```bash
python3 Module08/applied-labs/r04-t024/example.py
python3 -m unittest discover -s Module08/applied-labs/r04-t024 -p "test_*.py"
```
