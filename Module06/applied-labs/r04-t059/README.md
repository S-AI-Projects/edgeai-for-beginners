# Applied Lab R04-T059: AI Agent Capability Negotiation & Feature Gating

## Overview

In distributed AI agent systems and Model Context Protocol (MCP) architectures, client and server agents must establish a mutually understood capability envelope prior to dispatching tool calls, reading resources, or rendering prompts.

This applied lab extends **AI Agents and Small Language Models: A Comprehensive Guide** at `Module06/01.IntroduceAgent.md`. It implements a deterministic local fixture for **capability negotiation (set intersection)** and **pre-dispatch feature gating**, ensuring that any attempt to invoke an unnegotiated capability is rejected *before* execution dispatch.

### Core Pedagogical Principles
1. **Set-Theoretic Capability Discovery**: Computes the strict intersection of client-requested and server-offered capability sets: $\text{Negotiated} = C \cap S$.
2. **Pre-Dispatch Feature Gating**: Blocks invocation of unnegotiated capabilities before dispatch occurs, protecting against unauthorized execution, downstream serialization errors, and server state corruption.
3. **Discrete Actionable Rejection Diagnostics**: When an unnegotiated capability is invoked, provides an actionable reason explaining the rejection and listing the active negotiated capabilities.
4. **Three Controlled Configurations Comparison**: Evaluates trade-offs across three controlled input sizes (Small, Medium, Large) using metrics appropriate to capability negotiation (correctness rate, capability retention ratio, Jaccard overlap, unauthorized dispatches).

---

## Canonical Contract Specification

Requirements aligned with `Module06/01.IntroduceAgent.md`:

```python
client_capabilities = {"tools", "resources"}
server_capabilities = {"tools", "prompts"}

# Negotiation via set intersection
negotiated_capabilities = client_capabilities.intersection(server_capabilities)
# Result: {"tools"}
```

### Pre-Dispatch Gating Matrix

| Capability Called | In Client Set? | In Server Set? | Negotiated? | Dispatch Status | Action / Outcome |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `tools` | Yes | Yes | **Yes** | **DISPATCHED** | Executed successfully with structured result output. |
| `resources` | Yes | **No** | **No** | **REJECTED** | Blocked before dispatch with actionable rejection diagnostic. |
| `prompts` | **No** | Yes | **No** | **REJECTED** | Blocked before dispatch; client did not request capability. |

---

## Controlled Configurations & Trade-off Analysis (Contribution Focus)

Three controlled configurations were benchmarked to analyze capability negotiation and gating dynamics:

| Metric | Config-Small (Canonical) | Config-Medium (Multi-Feature) | Config-Large (Expanded) |
| :--- | :---: | :---: | :---: |
| **Client Capabilities** | 2 (`tools`, `resources`) | 4 (`tools`, `resources`, `sampling`, `roots`) | 8 (multi-modal + system tools) |
| **Server Capabilities** | 2 (`tools`, `prompts`) | 4 (`tools`, `prompts`, `sampling`, `logging`) | 8 (multi-modal + backend services) |
| **Negotiated Capabilities** | 1 (`tools`) | 2 (`tools`, `sampling`) | 4 (`tools`, `sampling`, `vision`, `telemetry`) |
| **Capability Retention** ($|C \cap S| / |C|$) | 50.0% | 50.0% | 50.0% |
| **Jaccard Overlap** ($|C \cap S| / |C \cup S|$) | 33.3% | 33.3% | 33.3% |
| **Total Test Calls** | 5 | 8 | 12 |
| **Permitted Dispatches** | 2 (40%) | 4 (50%) | 6 (50%) |
| **Rejected Dispatches** | 3 (60%) | 4 (50%) | 6 (50%) |
| **Unauthorized Dispatches** | **0** | **0** | **0** |
| **Enforcement Correctness** | **100.0%** | **100.0%** | **100.0%** |

### Observed Trade-offs
1. **Security Surface vs Operational Breadth**:
   - Small configurations minimize attack surface and reduce communication metadata overhead by negotiating only the minimal common denominator (`tools`), but reject 60% of attempted actions.
   - Expanded configurations unlock rich multi-modal agent workflows (`vision`, `sampling`, `telemetry`), admitting more valid requests while maintaining 100% pre-dispatch security gating.
2. **Pre-Dispatch Elimination of Downstream Waste**:
   - In all configurations, unnegotiated calls are intercepted in $O(1)$ time prior to dispatch. This prevents wasted token serialization, redundant RPC round-trips, and unhandled remote daemon exceptions.
3. **Teaching Approximation Notice**:
   - This benchmark measures algorithmic gating efficiency and protocol negotiation correctness. It makes *no claims* about real-world LLM accuracy, reasoning performance, or physical hardware benchmarks.

---

## Unestablished Real-Service Behaviors

To maintain clear pedagogical boundaries, this offline mock explicitly declares behaviors that it does **not** establish:

1. **Network Connectivity & IPC**: Does not establish live TCP/Unix socket connections or run Model Context Protocol STDIO transport.
2. **Daemon / Process Inspection**: Does not inspect OS process tables, systemd services, or container daemons.
3. **Hardware Driver Probing**: Does not query physical GPU/NPU hardware registers or measure VRAM allocation.
4. **Model Weight Loading & Accuracy**: Does not download model weights, evaluate token generation throughput, or measure model accuracy.
5. **Paid / Cloud API Integration**: Does not contact external cloud provider endpoints or paid LLM services.

---

## Concept Mapping to Module 06 (01.IntroduceAgent.md)

| Lab Component | Lesson Concept in Module06/01.IntroduceAgent.md | Pedagogical Purpose |
| :--- | :--- | :--- |
| `CapabilityNegotiator.negotiate()` | Agent Discovery & Tool/Capability Negotiation | Demonstrates set-theoretic capability intersection between heterogeneous client and server agents. |
| `CapabilityDispatcher.dispatch()` gating | Agent Operational Boundaries & Safe Tool Execution | Proves that unnegotiated operations are blocked prior to dispatch, preventing state corruption. |
| Actionable Rejection Diagnostics | Troubleshooting & Agent Error Handling Strategies | Provides distinct reasons for unnegotiated capability calls with actionable remediation. |
| Three-Configuration Comparison | SLM Resource Constraints & Performance Optimization | Evaluates feature-set retention vs security surface trade-offs across controlled input sizes. |
| Offline Read-Only Fixtures | Privacy-First Edge Deployments | Enforces safe, zero-side-effect assessment without external network dependencies. |

---

## File Structure

- `example.py`: Core `CapabilityNegotiator`, `CapabilityDispatcher`, benchmark runner, and canonical demonstration workflow.
- `test_example.py`: 11 automated unit tests verifying negotiation intersection, dispatch gating, strict mode exceptions, configuration benchmarks, and teaching boundaries.
- `README.md`: Technical documentation, trade-off matrix, and concept mapping.

---

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Unit Test Suite
```bash
python3 -m unittest discover -s Module06/applied-labs/r04-t059 -p "test_*.py"
```
