## Applied Example: Platform Compatibility Scenario Assessment

This example turns the [Prerequisites](#prerequisites) and the `-t` and `--target_backends` options above into a manifest-driven preflight check, then asks three applied questions about it: predict an output, diagnose a failure and choose a boundary policy.

> **Simulation:** the check compares a small JSON fixture with a manifest. It does not inspect your computer, install the QNN SDK, convert a model or use Qualcomm hardware or a simulator. A result here does not predict real device behavior.

**Requirement used (from Prerequisites, Quick Start and Example Step 2):** `Linux or Windows development environment`, `Python 3.7 or higher`, `-t x86_64-linux-clang` and `-t aarch64-android`, `--target_backends htp,gpu,cpu`, `Qualcomm QNN SDK (requires registration with Qualcomm)`, and `Android NDK (for mobile deployment)` (required only for the `aarch64-android` target). The lesson gives no minimum OS version, SDK or NDK version, compatible hardware list, host CPU architecture or RAM, so the example lists these as not checked instead of guessing.

**Invocation** (from the repository root):

```bash
python3 Module04/applied-labs/r04-t048/example.py Module04/applied-labs/r04-t048/fixtures/armv7_android_target.json
```

**Fixture** (`armv7_android_target.json`):

```json
{"os_name": "Linux", "python_version": "3.11", "architecture": "armv7-android", "backend": "htp", "qnn_sdk": true, "android_ndk": true}
```

**Expected output** (excerpt; exit code 1):

```text
verdict: FAIL
  [FAIL] architecture: expected one of 'x86_64-linux-clang', 'aarch64-android', actual 'armv7-android'
         lesson requirement: "-t x86_64-linux-clang" | "-t aarch64-android"
  [SKIPPED] android_ndk: not applicable because architecture is 'armv7-android' (applies only when it is 'aarch64-android')
mismatched: architecture
```

A fixture without `backend` gives `INCOMPLETE` (exit code 2) with `backend` listed as unknown rather than guessed. To see the three applied questions, each with its rationale and a check that runs the example to confirm the answer, run `python3 Module04/applied-labs/r04-t048/example.py --questions`.

Prerequisites: Python 3 standard library only. Full details, fixtures and tests: [applied-labs/r04-t048](applied-labs/r04-t048/README.md).
