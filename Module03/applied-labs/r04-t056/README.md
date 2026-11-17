# Applied Lab R04-T056: Local Environment Preflight Check — Failure and Recovery Teaching Example

## Overview

Deploying Small Language Models (SLMs) in local, privacy-first environments—such as with **Ollama**, **Microsoft Foundry Local**, or containerized local services—demands strict verification of the host environment before attempting model loading or API serving.

This applied lab implements a **read-only, non-intrusive preflight validator** that verifies local setup requirements without installing packages, modifying system state, or contacting external networks.

### Core Pedagogical Principles
1. **Read-Only Non-Intrusive Validation**: Inspects listed executables and configuration parameters offline against synthetic local fixtures.
2. **Discrete Actionable Diagnostic Categories**:
   - `MISSING_EXECUTABLE`: Pinpoints the exact binary missing from the environment and recommends installation or PATH updates.
   - `ABSENT_CONFIG_FIELD`: Pinpoints missing mandatory configuration parameters and provides the exact key to define.
   - `INVALID_CONFIG_VALUE`: Catches malformed values (e.g. non-numeric port or empty strings) with valid boundary instructions.
3. **Strict Credential Redaction**: All sensitive credentials (`api_token`, `secret_key`, `auth_token`, passwords) are masked with `***REDACTED***` and never printed, logged, or serialized in cleartext.
4. **Failure and Recovery Lifecycle**: Exercises a documented invalid/missing-data fixture, diagnoses the errors, and demonstrates clean recovery when supplied with valid input.

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

### Diagnostic Categories and Actionable Remedies

| Category | Trigger Condition | Example Diagnostic Message | Actionable Remedy |
| :--- | :--- | :--- | :--- |
| `MISSING_EXECUTABLE` | Binary not present in `executables` | `Required executable 'ollama' is missing or not found on PATH.` | `Install 'ollama' or update PATH before starting local SLM deployment.` |
| `ABSENT_CONFIG_FIELD` | Field missing or `None` in `config` | `Required configuration field 'model_name' is absent.` | `Specify 'model_name' in local deployment configuration or environment file.` |
| `INVALID_CONFIG_VALUE` | Port not integer in 1-65535 or empty string | `Port value 'not-a-port' is not a valid integer.` | `Provide a valid integer port between 1 and 65535 (e.g. 11434 or 8080).` |

---

## Failure & Recovery Cycle Walkthrough

```
+------------------------------------+
| 1. Initial Faulty Fixture          |
|    - Executable 'ollama': False    |
|    - Config 'model_name': Absent   |
|    - api_token: "secret-token-123" |
+-----------------+------------------+
                  |
                  v
+------------------------------------+
| 2. Preflight Diagnosis (FAIL)      |
|    - MISSING_EXECUTABLE: ollama    |
|    - ABSENT_CONFIG_FIELD: model_name|
|    - api_token masked: ***REDACTED*|
+-----------------+------------------+
                  |
                  v (Apply Recovery Patch)
+------------------------------------+
| 3. Recovery Patch                  |
|    - executables["ollama"] = True  |
|    - config["model_name"] = phi4   |
+-----------------+------------------+
                  |
                  v
+------------------------------------+
| 4. Recovered Attempt (PASS)        |
|    - All criteria satisfied        |
|    - Ready for local deployment    |
+------------------------------------+
```

---

## Redaction Guarantee

Any key matching known secret patterns (e.g. `api_token`, `secret_key`, `auth_token`, passwords) is sanitized at evaluation time:

```json
{
  "endpoint": "http://localhost:11434",
  "port": 11434,
  "model_name": "phi4:mini",
  "api_token": "***REDACTED***"
}
```

The raw secret value never appears in `report.summary()`, `str(report)`, or serialized JSON dictionaries.

---

## Unestablished Real-Service Behaviors

To maintain clear pedagogical boundaries, this offline mock explicitly identifies behaviors that it does **not** establish:

1. **Network Connectivity / Handshakes**: Does not attempt network connections or TCP handshakes to live daemon endpoints (e.g. `http://localhost:11434`).
2. **Package Installation**: Does not invoke external package managers (`winget`, `brew`, `apt`) or execute shell installation scripts.
3. **Daemon / Process Inspection**: Does not inspect host OS process tables, systemd services, or container runtime daemons.
4. **Hardware Driver Probing**: Does not query physical GPU drivers, CUDA libraries, or Windows ML / NPU hardware registers.
5. **Model Weight Loading**: Does not download, load, or run inference on real SLM weights (e.g. Phi-4, Qwen 2.5).

---

## Concept Mapping to Module 03 (Section 2)

| Preflight Component | Lesson Concept in Module03/02.DeployingSLMinLocalEnv.md | Pedagogical Purpose |
| :--- | :--- | :--- |
| `required_executables` (`"ollama"`, `"docker"`) | Section 2 Deployment Platform Architecture (Ollama CLI and Docker containerization) | Confirms presence of host runtime tools prior to launching model workloads. |
| `required_config_fields` (`"endpoint"`, `"port"`, `"model_name"`) | API Endpoints & Modelfile Configuration (Ollama REST API / Foundry Local) | Validates routing parameters without executing real HTTP requests. |
| `secret_keys` & `REDACTION_MASK` (`"***REDACTED***"`) | Enterprise Security and Compliance Considerations (GDPR, HIPAA, credential protection) | Guarantees API keys and reverse-proxy auth tokens are never leaked into logs. |
| Discrete `MISSING_EXECUTABLE` vs `ABSENT_CONFIG_FIELD` categories | Pre-Deployment Assessment and Troubleshooting Checklist | Ensures developers receive distinct, actionable remediation advice for distinct failure modes. |
| Failure and Recovery Workflow | Production Readiness and Resilient Operations | Demonstrates diagnosing invalid configuration and verifying clean recovery upon correction. |

---

## File Structure

- `example.py`: Core `LocalEnvironmentPreflight`, `PreflightReport`, redaction engine, and `demonstrate_failure_and_recovery` workflow.
- `test_example.py`: 10 automated unit tests verifying complete passing fixtures, separate actionable failure categories, strict credential redaction, boundary validation, and failure/recovery mechanics.
- `README.md`: Technical documentation, contract specification, and concept mapping.

---

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module03/applied-labs/r04-t056 -p "test_*.py"
```
