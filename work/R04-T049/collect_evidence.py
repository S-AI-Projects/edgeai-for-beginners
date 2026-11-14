#!/usr/bin/env python3
"""Collect R04-T049 evidence into work/R04-T049/. Run from the repository root:

    python3 work/R04-T049/collect_evidence.py

Writes tool versions, the inputs used, expected-versus-actual results, the unittest
output and a deliberate-failure check. Exits non-zero if anything differs from what
was expected. Keep work/ out of any later upstream branch.
"""
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
LAB = ROOT / "Module02" / "applied-labs" / "r04-t049"
OUT = ROOT / "work" / "R04-T049"
UNITTEST = [sys.executable, "-m", "unittest", "discover", "-s", "Module02/applied-labs/r04-t049",
            "-p", "test_*.py"]


def run(cmd, cwd=ROOT):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))


def tool_version(cmd):
    try:
        done = run(cmd)
        return (done.stdout or done.stderr).strip().splitlines()[0]
    except (OSError, IndexError):
        return "not available"


def main():
    if not LAB.is_dir():
        print("run this from the repository root (cannot find %s)" % LAB)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []

    # 1. tool versions
    versions = [
        "python3: " + tool_version([sys.executable, "--version"]),
        "platform: " + platform.platform(),
        "machine: " + platform.machine(),
        "git: " + tool_version(["git", "--version"]),
        "unittest: standard library (Python %s)" % platform.python_version(),
    ]
    (OUT / "tool_versions.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")

    # 2. inputs used
    inputs = OUT / "inputs"
    if inputs.exists():
        shutil.rmtree(inputs)
    inputs.mkdir()
    shutil.copy(LAB / "manifest.json", inputs / "manifest.json")
    for fixture in sorted((LAB / "fixtures").glob("*.json")):
        shutil.copy(fixture, inputs / fixture.name)

    # 3. expected versus actual, each scenario in a fresh process
    scenarios = [
        ("normal: matching OS/arch/backend", "ok_windows11_npu.json", 0, "verdict: PASS"),
        ("normal: second listed backend", "ok_directml_backend.json", 0, "verdict: PASS"),
        ("boundary: nothing reported", "empty_fixture.json", 2,
         "unknown (not guessed): os_name, architecture, backend, windows_app_sdk"),
        ("failure: changed architecture", "cpu_architecture.json", 1,
         "[FAIL] architecture: expected one of 'npu', actual 'cpu'"),
        ("failure: wrong OS", "wrong_os.json", 1,
         "[FAIL] os_name: expected one of 'Windows 11', actual 'Windows 10'"),
        ("failure: missing backend", "missing_backend.json", 2,
         "[UNKNOWN] backend: expected one of 'windows-ml', 'directml', actual <not reported>"),
        ("failure: invalid data", "invalid_sdk_flag.json", 3, "INVALID INPUT: windows_app_sdk must be true or false"),
    ]
    rows = ["| scenario | fixture | expected exit | actual exit | expected text found | match |",
            "|---|---|---|---|---|---|"]
    for label, name, code, text in scenarios:
        done = run([sys.executable, str(LAB / "example.py"), str(LAB / "fixtures" / name)])
        found = text in (done.stdout + done.stderr)
        ok = done.returncode == code and found
        if not ok:
            failures.append(label)
        rows.append("| %s | %s | %d | %d | %s | %s |" % (
            label, name, code, done.returncode, "yes" if found else "NO", "yes" if ok else "NO"))
    (OUT / "expected_vs_actual.md").write_text("\n".join(rows) + "\n", encoding="utf-8")

    evaluation = run([sys.executable, str(LAB / "example.py"), "--evaluate"])
    (OUT / "evaluation_output.txt").write_text(
        evaluation.stdout + evaluation.stderr + "exit code: %d\n" % evaluation.returncode, encoding="utf-8")
    if evaluation.returncode != 0 or "the contract policy (report) made 0 wrong decision(s): OK" not in evaluation.stdout:
        failures.append("evaluation")

    # 4. the official check
    tests = run(UNITTEST)
    (OUT / "unittest_output.txt").write_text(
        tests.stdout + tests.stderr + "exit code: %d\n" % tests.returncode, encoding="utf-8")
    if tests.returncode != 0 or "Ran 0 tests" in tests.stderr:
        failures.append("unittest")

    # 5. deliberate wrong results must make the tests fail
    lines = []
    mutations = [
        ("example.py", "ok = actual in expected", "ok = True",
         "choice check made always true"),
        ("example.py", "        return report.verdict",
         "        return \"pass\" if not report.mismatched_fields() else \"fail\"",
         "contract policy changed to guess missing fields"),
        ("manifest.json", '"expected": ["npu"]', '"expected": ["cpu"]',
         "manifest expectation changed (npu became cpu)"),
    ]
    for filename, old, new, label in mutations:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "Module02" / "applied-labs" / "r04-t049"
            shutil.copytree(LAB, copy)
            target = copy / filename
            text = target.read_text(encoding="utf-8")
            if old not in text:
                lines.append("%s: could not apply mutation (text not found)" % label)
                failures.append(label)
                continue
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
            broken = run([sys.executable, "-m", "unittest", "discover", "-s", str(copy), "-p", "test_*.py"],
                         cwd=Path(tmp))
            detected = broken.returncode != 0 and "FAILED" in broken.stderr
            summary = [l for l in broken.stderr.splitlines() if l.startswith(("Ran ", "FAILED", "OK"))]
            lines.append("%s -> tests exit %d (%s): %s" % (
                label, broken.returncode, "failure detected" if detected else "NOT DETECTED", " / ".join(summary)))
            if not detected:
                failures.append(label)
    (OUT / "deliberate_failure.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {"failures": failures, "files": sorted(p.name for p in OUT.iterdir())}
    print(json.dumps(summary, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
