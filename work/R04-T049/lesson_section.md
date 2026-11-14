## Applied Example: Platform Compatibility Evaluation Experiment

This example turns the lesson's platform and hardware statements into a manifest-driven preflight check, then compares three ways of treating a missing field on a small controlled corpus and reports correctness and the trade-off.

> **Simulation:** the check compares a small JSON fixture with a manifest. It does not inspect your computer, call Windows, use an NPU or run Phi-Silica. A result here does not predict real Copilot+ PC behavior, and the speed and power figures in this lesson are not used or verified.

**Requirement used (from the NPU hardware, design philosophy, Windows ML, Windows App SDK and hardware requirements sections):** `Windows 11 Copilot+ PCs`, `NPU-First Architecture` and `Optimal performance requires a Windows Copilot+ PC with NPU hardware`, `Windows ML Runtime` and `DirectML Acceleration`, and `Developers can access Phi-Silica capabilities through the Windows App SDK`. The lesson gives no Windows build number, CPU instruction set, NPU performance floor, RAM or disk size, Windows App SDK version or list of Copilot+ devices, so the example lists these as not checked instead of guessing.

**Invocation** (from the repository root):

```bash
python3 Module02/applied-labs/r04-t049/example.py Module02/applied-labs/r04-t049/fixtures/cpu_architecture.json
```

**Fixture** (`cpu_architecture.json`):

```json
{"os_name": "Windows 11", "architecture": "cpu", "backend": "windows-ml", "windows_app_sdk": true}
```

**Expected output** (excerpt; exit code 1):

```text
verdict: FAIL
  [FAIL] architecture: expected one of 'npu', actual 'cpu'
         lesson requirement: "NPU-First Architecture" | "Optimal performance requires a Windows Copilot+ PC with NPU hardware"
mismatched: architecture
```

A fixture without `backend` gives `INCOMPLETE` (exit code 2) with `backend` listed as unknown rather than guessed.

**The experiment** (`python3 Module02/applied-labs/r04-t049/example.py --evaluate`, exit code 0):

```text
policy        decided  undecided  correct  false_pass  false_fail  coverage  error_rate
report            176         80      176           0           0     68.8%        0.0%
assume_pass       256          0      191          65           0    100.0%       25.4%
assume_fail       256          0      241           0          15    100.0%        5.9%
```

Over all 256 generated fixtures, reporting a missing field as unknown makes no wrong decision but leaves 80 undecided. Guessing decides everything but makes 65 false passes (`assume_pass`) or 15 false fails (`assume_fail`). These are counts over generated fixtures, not a measure of Phi-Silica's accuracy or speed.

Prerequisites: Python 3 standard library only. Full details, fixtures and tests: [applied-labs/r04-t049](applied-labs/r04-t049/README.md).
