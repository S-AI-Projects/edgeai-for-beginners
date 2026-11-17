# R04-T020 - Installation Preflight Report: Scenario Assessment

Companion applied lab to [Module01/03.PracticalImplementationGuide.md](../../03.PracticalImplementationGuide.md) ("Section 3: Practical Implementation Guide - 1. Development Environment Setup").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
Preparing an EdgeAI development environment requires verifying that host prerequisites and local configurations are satisfied before attempting model installation or inference. A read-only preflight checker verifies local configuration and tool availability deterministically:
1. **Read-Only Verification**: Checks explicitly declared executables (`python3`, `git`) and configuration keys (`cache_dir`, `api_token`) without installing software, mutating system state, or initiating network connections.
2. **Actionable Failure Differentiation**:
   * Missing executable $\rightarrow$ `EXECUTABLE_NOT_FOUND` with explicit PATH / installation guidance.
   * Missing configuration key $\rightarrow$ `CONFIG_FIELD_MISSING` with remediation instructions.
3. **Secret Redaction**: Any field matching credential substrings (`token`, `key`, `secret`, `password`, `auth`) is masked (`***`), preventing accidental exposure in log streams.
4. **Three Applied Questions (`questions.json`)**:
   * **Predict Output**: Forecasts `PASSED` status and masked token `***` on a complete fixture.
   * **Diagnose Failure**: Identifies `EXECUTABLE_NOT_FOUND` when `git` is absent.
   * **Choose Boundary Policy**: Enforces strict schema validation (`STRICT_SCHEMA_ENFORCEMENT`) rather than guessing silent defaults.

### Scope and Limitations
* **Fixture-Based Evaluation**: Checks observation dictionaries against preflight criteria. It **does not** perform actual software installations, modify the OS environment, or query live remote service APIs.
* **Prerequisites**: Python 3 standard library only.

---

## 2. Canonical Task Fixture

* **Required Executables**: `["python3", "git"]`
* **Required Config Keys**: `["cache_dir", "api_token"]`
* **Complete Fixture**:
  ```json
  {
    "executables": ["python3", "git"],
    "config": {
      "cache_dir": "/var/models/cache",
      "api_token": "secret_abc_123"
    }
  }
  ```
  $\rightarrow$ **Status: PASSED**, `api_token` reported as `***`.
* **Missing Tool**: `executables = ["python3"]` $\rightarrow$ **Status: FAILED**, code `EXECUTABLE_NOT_FOUND`.
* **Missing Config**: `config = {"cache_dir": "..."}` $\rightarrow$ **Status: FAILED**, code `CONFIG_FIELD_MISSING`.

---

## 3. Run and Verify

```bash
python3 Module01/applied-labs/r04-t020/example.py
python3 -m unittest discover -s Module01/applied-labs/r04-t020 -p "test_*.py"
```
Ran 10 tests in ~0.001s, OK.
