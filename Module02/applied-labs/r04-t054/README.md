# Applied Lab R04-T054: Model-Manifest Selection — Offline Service Adapter

## Overview

In on-device Small Language Model (SLM) architectures—such as the Microsoft Mu model built into Windows 11—applications must validate candidate models against host resource constraints (RAM capacity and context window limits) before instantiating weights.

This lab demonstrates an **Offline Service Adapter** pattern that decouples catalog discovery behind a callable interface. It evaluates model eligibility against host hardware limits and generates explicit diagnostic explanations for any excluded models.

## Contract Specification

1. **Synthetic Teaching Fixtures**:
   - **Fixture A**: Requires 4GB RAM, supports maximum context of 2048 tokens.
   - **Fixture B**: Requires 8GB RAM, supports maximum context of 4096 tokens.
   - *Note: Values are invented teaching fixtures, not claims about named real models.*
2. **Selection Rule**:
   - A model is admitted if and only if:
     - `model.min_ram_gb <= available_ram_gb` (sufficient host RAM)
     - `model.max_context >= requested_context` (sufficient context capacity)
3. **Primary Evaluation Fixture**:
   - Host Budget: **6GB RAM**, Requested Context: **1024 tokens**.
   - **Result**: Admits **Fixture A** only.
   - **Exclusion Explanation**: Fixture B is rejected because its 8GB requirement exceeds the 6GB host budget.
4. **Offline Service Adapter**:
   - `SyntheticManifestAdapter` implements a callable interface (`Callable[[], List[Dict[str, Any]]]`) returning defensive copies of manifest entries, isolating the evaluator from external services.
5. **Validation & Boundaries**:
   - Boundary matches (e.g. 4GB RAM budget with Fixture A) admit the model.
   - Nonpositive budgets (`<= 0`) raise `ValueError`.

## Unestablished Real-Service Behaviors

To maintain clear pedagogical boundaries, this offline mock explicitly identifies behaviors that it does **not** establish:

1. **Network Transport & Catalog Synchronization**: Does not communicate with live Azure AI Foundry, Windows catalog APIs, or remote model registries.
2. **Dynamic Host Telemetry**: Does not inspect live Windows kernel page files, physical memory pressure, or DirectML NPU driver states.
3. **Authentication & Rate Limiting**: Does not establish OAuth tokens, subscription keys, or enterprise policy verification.
4. **Live Weight Verification**: Does not verify cryptographic weight signatures, file integrity, or execute on-device tensor operations.

## Concept Mapping to Microsoft Mu Model Fundamentals

| Component | Microsoft Mu Model Concept (Module 02, Section 5) |
| :--- | :--- |
| `available_ram_gb` | Allocated system memory budget on consumer Windows 11 hardware |
| `requested_context` | Desired token sequence length for multi-turn user/settings interaction |
| `min_ram_gb` | Minimal memory footprint needed to host on-device weights and KV cache |
| `max_context` | Maximum token capacity defined by model architecture |
| `admitted` | Models qualifying for local execution without exceeding system budget |
| `excluded` | Models rejected to prevent memory exhaustion, with explicit failure rationales |
| `offline adapter` | Architectural decoupling enabling preflight verification without external service calls |

## File Structure

- `example.py`: Core `SyntheticManifestAdapter`, `ModelManifestSelector`, and interactive demonstration.
- `test_example.py`: 12 automated unit tests verifying admission logic, boundaries, error handling, and adapter decoupling.
- `README.md`: Architectural documentation, contract specification, and execution instructions.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t054 -p "test_*.py"
```
