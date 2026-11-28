# R04-T025: Capability Negotiation — Offline Service Adapter

A deterministic offline service adapter isolating an external backend behind a callable interface (`ServiceBackend`) to test capability intersection and pre-dispatch feature gating without live Chainlit or Foundry Local servers.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module08/04.CuttingEdgeModels.md`:** Production chat applications integrate UI clients with local or remote model backends. Placing the backend behind a callable interface lets the client discover server capabilities, intersect them with client capabilities, and block unnegotiated features before dispatch.
- **What real-service behavior this mock does NOT establish:**
  1. Network transport latency, connection drops, timeouts, and retry backoff.
  2. HTTP/WebSocket framing and Chainlit streaming UI backpressure.
  3. Authentication token expiry, TLS validation, and server-side RBAC enforcement.
  4. Runtime server capability drift or mid-session feature revocation.

## Files
- `example.py` — `ServiceBackend` protocol, `DeterministicLocalAdapter` callable mock, and `CapabilityGateway`.
- `test_example.py` — Unit tests verifying capability intersection, pre-dispatch rejection, callable decoupling, and explicit non-established behavior reporting.

## Prerequisites
- Python 3 standard library only (no Chainlit server, Foundry Local runtime, or GPU required).

## Usage & Verification
```bash
python3 Module08/applied-labs/r04-t025/example.py
python3 -m unittest discover -s Module08/applied-labs/r04-t025 -p "test_*.py"
```
