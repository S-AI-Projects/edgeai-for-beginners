# Applied Lab R04-T055: Qualcomm QNN Platform-Compatibility Preflight — Refactor Teaching Example

## Overview

Deploying AI models on Qualcomm hardware accelerators using the **Qualcomm QNN Optimization Suite** requires preflight validation of operating system, processor architecture, hardware capabilities, and runtime backend (e.g. Hexagon Tensor Processor / `libQnnHtp.so`).

This lab demonstrates a manifest-driven platform preflight check and demonstrates code refactoring principles:
1. **Baseline Monolithic Implementation**: `BaselineQNNPlatformChecker` combines preflight coordination and validation rules in a single class.
2. **Extracted Single Responsibility**: `PlatformRuleValidator` isolates the discrete evaluation of platform attributes and capability set differences.
3. **Refactored Architecture**: `RefactoredQNNPlatformChecker` delegates evaluation to the extracted validator while maintaining identical API contracts and execution behavior.
4. **Before/After Equivalence Proof**: Verifies that baseline and refactored implementations produce identical outputs across all test fixtures.

## Contract Specification

Requirements extracted directly from Section 7 of `Module04/07.QualcommQNN.md`:

```python
QNN_LESSON_REQUIREMENTS = {
    "lesson_source": "Module04/07.QualcommQNN.md",
    "target_suite": "Qualcomm QNN (Qualcomm Neural Network) Optimization Suite",
    "required_os": "Linux",
    "required_architecture": "aarch64",
    "required_backend": "htp",
    "required_capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
}
```

### Evaluation Behaviors
1. **Matching Fixture**: Matches OS, architecture, backend, and all capabilities -> **`PASS`** (`compatible = True`).
2. **Changed Architecture**: Fixture with `architecture = "x86_64"` -> **`FAIL`**, reporting exact mismatch:
   `{"field": "architecture", "expected": "aarch64", "actual": "x86_64"}`.
3. **Missing Capabilities**: Fixture missing `Hexagon_NPU` and `HTP_Backend` -> **`FAIL`**, explicitly reporting missing capabilities rather than guessing.
4. **Audit Trail**: Output preserves `lesson_source` and full `requirements` dictionary for traceability.

## Refactoring Equivalence Matrix

| Fixture Description | Probe Attributes | Baseline Status | Refactored Status | Equivalence |
| :--- | :--- | :---: | :---: | :---: |
| **Fully Compliant** | OS: Linux, Arch: aarch64, Backend: htp, Caps: Full | `PASS` | `PASS` | **Identical** |
| **Changed Arch** | OS: Linux, Arch: x86_64, Backend: htp, Caps: Full | `FAIL` (arch mismatch) | `FAIL` (arch mismatch) | **Identical** |
| **Missing Capabilities** | OS: Linux, Arch: aarch64, Backend: htp, Caps: [QNN_SDK] | `FAIL` (2 missing caps) | `FAIL` (2 missing caps) | **Identical** |
| **Non-Compliant OS** | OS: Windows, Arch: arm64, Backend: cpu, Caps: [] | `FAIL` (3 mismatches) | `FAIL` (3 mismatches) | **Identical** |
| **Empty Probe** | `{}` | `FAIL` (all missing) | `FAIL` (all missing) | **Identical** |

## Unestablished Real-Service Behaviors

To maintain clear pedagogical boundaries, this offline mock explicitly identifies behaviors that it does **not** establish:

1. **Hardware Register Probing**: Does not probe physical Hexagon NPU registers, DSP clock domains, or Snapdragon SoC firmware.
2. **Dynamic Library Loading**: Does not `dlopen` `libQnnHtp.so` or verify dynamic linker symbols.
3. **Kernel Device Node Inspection**: Does not inspect `/dev/kgsl-3d0` or Qualcomm NPU character devices.
4. **Runtime Execution**: Does not allocate NPU memory or execute real quantized QNN inference graphs.

## Concept Mapping to Qualcomm QNN Optimization Suite

| Component | Qualcomm QNN Concept (Module 04, Section 7) |
| :--- | :--- |
| `required_os = "Linux"` | Supported host development environment (Section 7, Prerequisites) |
| `required_architecture = "aarch64"` | Snapdragon target architecture (`-t aarch64-android`) |
| `required_backend = "htp"` | Hexagon Tensor Processor backend (`--backend libQnnHtp.so`) |
| `required_capabilities` | Prerequisite hardware accelerators and SDK tool binaries |
| `mismatches` | Explicit field discrepancies reported without guessing |
| `extracted_responsibility` | `PlatformRuleValidator` decoupling rule evaluation from coordination |

## File Structure

- `example.py`: Core `BaselineQNNPlatformChecker`, extracted `PlatformRuleValidator`, `RefactoredQNNPlatformChecker`, and equivalence runner.
- `test_example.py`: 11 automated unit tests proving before/after equivalence, contract compliance, and error handling.
- `README.md`: Technical documentation, contract specification, and equivalence matrix.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module04/applied-labs/r04-t055 -p "test_*.py"
```
