# R04-T034: Model-Manifest Selection (Offline Service Adapter)

## Overview
This lab extends `Module02/02.QwenFamily.md` by placing model manifest retrieval behind a callable interface (`ModelCatalogService`) and providing a deterministic offline adapter (`OfflineModelCatalogAdapter`).

### Service Adapter Scope & Mock Boundaries
- **Callable Protocol**: Decouples filtering logic from remote catalog HTTP endpoints or authentication headers.
- **Offline Determinism**: Serves fixed teaching fixtures without external network requests or tokens.
- **Real-Service Limitations**: This offline mock does **not** establish or verify:
  - Network timeouts, DNS resolution, and TLS handshake failures.
  - Remote authentication token refresh and authorization scopes.
  - Asynchronous catalog pagination or dynamic rate limits.
  - Actual weight downloads or hardware capability probing.

### Selection Contract:
- Fixture A: RAM 4GB, Context 2048
- Fixture B: RAM 8GB, Context 4096
- Available RAM 6GB, Requested Context 1024 -> Admits only Fixture A.

## Execution
```bash
python3 Module02/applied-labs/r04-t034/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t034 -p "test_*.py"
```
