# R04-T016 - Platform-Compatibility Preflight: Refactor the Teaching Example

Companion applied lab to [Module04/05.AppleMLX.md](../../05.AppleMLX.md) ("Section 4 : Apple MLX Framework Deep Dive - System Requirements").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
Apple MLX relies on hardware-specific capabilities, operating directly on Apple Silicon's unified memory architecture via Metal Performance Shaders. Deployments require preflight verification against strict platform specifications read directly from the lesson:
* **OS**: Darwin (macOS 13.0+)
* **Architecture**: `arm64` (Native Apple Silicon, not Rosetta translation)
* **Backend**: `metal` (Metal acceleration)
* **RAM**: Minimum 8GB unified memory
* **Explicit Unknowns**: GPU core count, Apple Silicon generation (M1-M4)

This lab demonstrates:
1. **Manifest-Driven Checking**: Platform rules are recorded in an explicit manifest with pinned lesson citations.
2. **Hardware Independence**: Operates purely on provided observation dictionaries. It never queries host APIs (`os.uname` or `platform.system`).
3. **Explicit Mismatch & Missing Reporting**: A changed architecture fails reporting the exact mismatch field. Missing observations (such as an omitted `backend`) are recorded in `missing` and never guessed.
4. **Refactor Invariant**: Extracts `evaluate_field_requirement()` as a separate responsibility and proves before/after equivalence against the monolithic baseline.

---

## 2. Canonical Task Fixture

* **Matching Observation**:
  `{"os": "Darwin", "architecture": "arm64", "backend": "metal", "ram_gb": 16}` $\rightarrow$ **Compatible: True**
* **Changed Architecture**:
  `{"os": "Darwin", "architecture": "x86_64", "backend": "metal", "ram_gb": 16}` $\rightarrow$ **Compatible: False** (Failed field: `architecture`)
* **Missing Capability**:
  `{"os": "Darwin", "architecture": "arm64", "ram_gb": 16}` (missing `backend`) $\rightarrow$ **Compatible: False** (Missing field: `backend`)

---

## 3. Run and Verify

```bash
python3 Module04/applied-labs/r04-t016/example.py
python3 -m unittest discover -s Module04/applied-labs/r04-t016 -p "test_*.py"
```
Ran 10 tests in ~0.001s, OK.
