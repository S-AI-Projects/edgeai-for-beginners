# R04-T011 - Capability Negotiation: Runnable Concept Example

Companion applied lab to [Module06/01.IntroduceAgent.md](../../01.IntroduceAgent.md) ("Building Agents with Microsoft Agent Framework: Tool Integration for Edge Scenarios").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
In edge AI and SLM agent deployments, agents frequently interact with heterogeneous runtimes, local tools, and external services. An edge agent runtime must establish what capabilities (such as tools, prompts, and resources) are mutually supported between client and server components before executing any operations.

This lab isolates that principle:
1. **Capability Discovery & Declaration**: Client and server independently declare their capability sets.
2. **Intersection Negotiation**: The active capability set is strictly the mathematical intersection of what both parties support (`client_caps ∩ server_caps`).
3. **Pre-Dispatch Feature Gating**: When a capability invocation request is received, the system verifies that the capability is in the negotiated set **before** resolving or dispatching to any handler. Unnegotiated capabilities are rejected immediately.

### Scope and Limitations
* **Labels Only**: Capabilities (`tools`, `resources`, `prompts`) are represented as symbolic string identifiers.
* **No Network / Protocol Overhead**: Does not implement raw socket handshakes, HTTP/JSON-RPC protocols, or MCP transports.
* **Hardware Independence**: Python 3 standard library only. Does not require or assume any local NPU/GPU, model weights, or remote cloud services.

---

## 2. Architecture and Contract

| Function / Component | Contract & Responsibility |
|---|---|
| `validate_capability_set(caps)` | Ensures `caps` is a collection (set, list, tuple) of non-empty strings. Rejects bare strings to prevent character iteration. |
| `negotiate_capabilities(client, server)` | Pure function computing `client ∩ server`. Commutative, non-mutating, returns `frozenset`. |
| `invoke_capability(client, server, cap, ...)` | Validates the request, negotiates capabilities, enforces the pre-dispatch gate, and invokes the handler. |

### Error Codes
* `NOT_NEGOTIATED`: The requested capability is not part of the negotiated intersection. Rejected before handler dispatch.
* `NO_HANDLER`: The capability was negotiated, but no callable handler was registered in the dispatch table.
* `BAD_CAPABILITY_SET`: The capability set is not a collection of non-empty strings (e.g. `None`, bare string, empty string element).
* `BAD_REQUEST`: The target capability identifier is not a non-empty string.

---

## 3. Canonical Task Fixture

* **Client Capabilities**: `{"tools", "resources"}`
* **Server Capabilities**: `{"tools", "prompts"}`
* **Negotiated Set**: `{"tools"}`
* **Invocation Behavior**:
  * Invoking `tools` with payload `"ping"` -> **Dispatched** (`tools-handled:ping`).
  * Invoking `resources` -> **Rejected** with error `NOT_NEGOTIATED`. The resource handler is never called.

---

## 4. Execution and Testing

### Run the Example
```bash
python3 Module06/applied-labs/r04-t011/example.py
```

**Expected Output:**
```text
=== Capability Negotiation Example ===
Client capabilities: ['resources', 'tools']
Server capabilities: ['prompts', 'tools']
Negotiated (active) capabilities: ['tools']
Invocation of 'tools': OK -> tools-handled:ping
Invocation of 'resources': REJECTED -> code: NOT_NEGOTIATED, pre-dispatch rejection verified (handlers called: ['tools'])
```

### Run the Test Suite
```bash
python3 -m unittest discover -s Module06/applied-labs/r04-t011 -p "test_*.py"
```
Ran 21 tests in ~0.002s, OK.
