# Applied Lab R04-T058: Local Environment Preflight Check — Intermediate State Recording & Invariant Testing

## Overview

Deploying Small Language Models (SLMs) in local, privacy-first environments—such as with **Ollama**, **Microsoft Foundry Local**, or containerized local microservices—demands rigorous verification of host environment prerequisites before attempting model weight loading or API serving.

This applied lab extends **Section 2: Local Environment Deployment - Privacy-First Solutions** at `Module03/02.DeployingSLMinLocalEnv.md`. It implements a **read-only, non-intrusive environment preflight validator** that records the deterministic intermediate state after each evaluation step and verifies formal invariants linking those intermediate states directly to the final diagnostic output report.

### Core Pedagogical Principles
1. **Read-Only Non-Intrusive Validation**: Inspects listed executables and configuration parameters offline against synthetic local fixtures without installing packages, mutating system state, or initiating network connections.
2. **Intermediate State Recording**: Captures an explicit, auditable snapshot (`StepIntermediateState`) immediately following each evaluation step in the pipeline.
3. **Formal Invariant Verification**: Tests mathematical and logical invariants ensuring the final diagnostic report is a consistent, deterministic projection of the intermediate pipeline states.
4. **Discrete Actionable Diagnostic Categories**:
   - `MISSING_EXECUTABLE`: Pinpoints the exact binary missing from the environment and recommends installation or PATH updates.
   - `ABSENT_CONFIG_FIELD`: Pinpoints missing mandatory configuration parameters and provides the exact key to define.
   - `INVALID_CONFIG_VALUE`: Catches malformed values (e.g. non-numeric port, out-of-bounds port, or empty string values) with boundary remediation.
5. **Strict Credential Redaction**: All sensitive credentials (`api_token`, `secret_key`, `auth_token`, passwords) are masked with `***REDACTED***` and never printed, logged, or serialized in cleartext.

---

## Contract Specification

Requirements aligned with Section 2 of `Module03/02.DeployingSLMinLocalEnv.md`:

```python
DEFAULT_REQUIRED_EXECUTABLES = ["ollama", "docker"]
DEFAULT_REQUIRED_CONFIG_FIELDS = ["endpoint", "port", "model_name"]
DEFAULT_SECRET_KEYS = {
    "api_key",
    "api_token",
    "secret_key",
    "auth_token",
    "password",
    "token",
    "secret",
}
REDACTION_MASK = "***REDACTED***"
```

### Evaluation Pipeline & Intermediate States

```
+--------------------------------------------------------------------------+
| Input Fixture (executables, config with credentials)                     |
+--------------------------------------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| Step 1: Check Required Executables                                       |
| - Evaluates: "ollama", "docker"                                          |
| - Snapshot 1: StepIntermediateState(step_index=1, name="check_executables")|
| - Records: missing_executables, step status, cumulative issue count     |
+--------------------------------------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| Step 2: Check Required Configuration Fields & Values                     |
| - Evaluates: "endpoint", "port", "model_name"                            |
| - Validates TCP port integer bounds (1-65535) and non-empty strings      |
| - Snapshot 2: StepIntermediateState(step_index=2, name="check_config_fields")|
| - Records: absent_config_fields, invalid_config_fields, cumulative count|
+--------------------------------------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| Step 3: Sanitize Configuration & Redact Secrets                          |
| - Recursively masks sensitive keys with ***REDACTED***                   |
| - Verifies zero cleartext credential leaks                               |
| - Snapshot 3: StepIntermediateState(step_index=3, name="sanitize_secrets")|
| - Records: redacted_keys, leak count, cumulative issue count            |
+--------------------------------------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
| Step 4: Final Synthesis & Invariant Verification                         |
| - Synthesizes PreflightReport                                            |
| - Executes verify_invariants() against all recorded intermediate states  |
+--------------------------------------------------------------------------+
```

---

## Formal Invariants Linking Intermediate States to Final Report

| Invariant Name | Mathematical / Logical Expression | Pedagogical Purpose |
| :--- | :--- | :--- |
| **Status Equivalence** | `report.passed == all(s.passed for s in states)` | Guarantees that overall preflight passes if and only if every intermediate evaluation phase passed. |
| **Issue Partition & Union** | `report.issues == [issue for s in states for issue in s.issues]` | Ensures no diagnostics are lost, fabricated, or duplicated during pipeline aggregation. |
| **Categorical Consistency** | `report.missing_executables == step1.missing` and `report.absent_config_fields == step2.absent` | Assures each diagnostic category in the final output maps directly to the responsible pipeline phase. |
| **Strict Redaction Preservation** | `report.config[k] == "***REDACTED***"` for all $k \in \text{secrets}$ and $\text{leaks} = 0$ | Proves secrets masked in Step 3 remain securely redacted in the final report and strings. |
| **Chronological Monotonicity** | `states[i].step_index == i + 1` and `issues_count[i] <= issues_count[i+1]` | Confirms linear, un-reordered execution flow and non-decreasing diagnostic accumulation. |

---

## Unestablished Real-Service Behaviors

To maintain clear pedagogical boundaries, this offline mock explicitly identifies behaviors that it does **not** establish:

1. **Network Connectivity / Handshakes**: Does not attempt live network connections or TCP handshakes to live daemon endpoints (e.g. `http://localhost:11434`).
2. **Package Installation**: Does not invoke external package managers (`winget`, `brew`, `apt`) or execute shell installation scripts.
3. **Daemon / Process Inspection**: Does not inspect host OS process tables, systemd services, or container runtime daemons.
4. **Hardware Driver Probing**: Does not query physical GPU drivers, CUDA libraries, or Windows ML / NPU hardware registers.
5. **Model Weight Loading**: Does not download, load, or run inference on real SLM weights (e.g. Phi-4, Qwen 2.5).

---

## Concept Mapping to Module 03 (Section 2)

| Preflight Component | Lesson Concept in Module03/02.DeployingSLMinLocalEnv.md | Pedagogical Purpose |
| :--- | :--- | :--- |
| `intermediate_states` recording | Section 2 Deployment Platform Architecture & Verification | Illustrates deterministic step-by-step auditing of host requirements prior to launch. |
| Invariant verification engine | Section 2 Production Readiness & Quality Assurance | Formally guarantees that final diagnostic verdicts faithfully represent intermediate findings. |
| Discrete `MISSING_EXECUTABLE` vs `ABSENT_CONFIG_FIELD` categories | Section 2 Pre-Deployment Assessment and Troubleshooting Checklist | Ensures developers receive distinct, actionable remediation advice for distinct failure modes. |
| Strict credential redaction (`***REDACTED***`) | Section 2 Security and Compliance Considerations | Guarantees API keys and reverse-proxy auth tokens are never leaked into logs or diagnostics. |
| Read-only non-intrusive fixture inspection | Section 2 Privacy-First Local Solutions | Enforces zero-side-effect assessment without external network dependencies. |

---

## File Structure

- `example.py`: Core `LocalEnvironmentPreflight`, `PreflightReport`, `StepIntermediateState`, invariant verification engine, and demonstration workflows.
- `test_example.py`: Automated unit tests verifying passing fixtures, separate actionable failures, strict credential redaction, intermediate state recording, all 5 invariants, boundary cases, and negative invariant checks.
- `README.md`: Technical documentation, formal invariant specifications, and concept mapping.

---

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Unit Test Suite
```bash
python3 -m unittest discover -s Module03/applied-labs/r04-t058 -p "test_*.py"
```
