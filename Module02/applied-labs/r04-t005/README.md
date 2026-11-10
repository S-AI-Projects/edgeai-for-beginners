# Applied Lab R04-T005: Platform-Compatibility Preflight — Offline Service Adapter

## Overview

Microsoft's **Phi-Silica** is designed exclusively for on-device inference on Windows 11 Copilot+ PCs powered by dedicated Neural Processing Units (NPUs) and DirectML runtime acceleration. Attempting to deploy Phi-Silica on incompatible OS or processor platforms leads to failure or fallback to unoptimized, power-inefficient compute paths.

This lab implements a manifest-driven platform compatibility checker using an **Offline Service Adapter** pattern that evaluates system capability manifests without requiring physical access to Qualcomm Snapdragon X Elite or Copilot+ PC silicon.

## Exact Lesson Requirements Used

Extracted from `Module02/06.phisilica.md`:
- **Target Model**: Phi-Silica
- **Required OS**: Windows 11 (Copilot+ PC baseline)
- **Required Architecture**: ARM64 (Snapdragon NPU architecture)
- **Required Backend**: DirectML / Windows ML Runtime
- **Required Capabilities**: `["NPU", "DirectML", "WindowsAppSDK"]`

## Offline Service Adapter Pattern

The checker decouples system environment detection behind a callable probe interface (`Callable[[], Dict[str, Any]]`). 
- `MockPlatformAdapter`: Injects deterministic platform profiles for testing.
- Missing capabilities (e.g. absent NPU hardware flag) are explicitly surfaced in `missing_capabilities` rather than guessed or defaulted.

## Scope & Limitations

> [!NOTE] Offline Mock Notice
> This validator verifies platform manifest schema and system profiles purely in memory. It does **not** establish real hardware register states, measure NPU TOPS throughput (e.g., 40+ TOPS for Copilot+), or test DirectML driver stability.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t005 -p "test_*.py"
```
