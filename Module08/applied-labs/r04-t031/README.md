# R04-T031: Capability Negotiation Concept Example

## Overview
This module demonstrates client-server capability negotiation and feature gating for AI model integrations (such as Foundry Local and Azure OpenAI).

When connecting an edge/client environment with an AI provider or gateway:
- The client advertises supported capabilities (e.g., `{"tools", "resources"}`).
- The server/gateway advertises supported capabilities (e.g., `{"tools", "prompts"}`).
- The negotiated capability set is computed as the strict intersection: `client_caps ∩ server_caps` -> `{"tools"}`.
- Any attempt to invoke unnegotiated capabilities (such as `resources`) is rejected before dispatch.

## Contract & Invariants
1. **Intersection Invariant**: $C_{negotiated} = C_{client} \cap C_{server}$
2. **Pre-dispatch Gate Invariant**: If $c \notin C_{negotiated}$, `dispatch(c, ...)` raises `CapabilityNegotiationError` before any underlying handler or network call is executed.
3. **No Hardware/Cloud Dependency**: Pure Python standard library implementation without requiring cloud credentials, GPU, or local model daemons.

## Running the Example
```bash
python3 Module08/applied-labs/r04-t031/example.py
```

## Running Tests
```bash
python3 -m unittest discover -s Module08/applied-labs/r04-t031 -p "test_*.py"
```
