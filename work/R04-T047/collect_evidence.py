#!/usr/bin/env python3
"""Collect R04-T047 evidence into work/R04-T047/. Run from the repository root:

    python3 work/R04-T047/collect_evidence.py

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
LAB = ROOT / "Module04" / "applied-labs" / "r04-t047"
OUT = ROOT / "work" / "R04-T047"
UNITTEST = [sys.executable, "-m", "unittest", "discover", "-s", "Module04/applied-labs/r04-t047",
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
        ("normal: matching OS/arch/backend", "ok_macos14_arm_mlx.json", 0, "verdict: PASS"),
        ("boundary: exact minimums", "ok_boundary_minimums.json", 0, "verdict: PASS"),
        ("failure: changed architecture", "rosetta_architecture_i386.json", 1,
         "[FAIL] architecture: expected 'arm', actual 'i386'"),
        ("failure: missing capability", "missing_backend.json", 2,
         "[UNKNOWN] backend: expected 'mlx', actual <not reported>"),
        ("failure: invalid data", "invalid_ram_gb.json", 3, "INVALID INPUT: ram_gb must be"),
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

    demo = run([sys.executable, str(LAB / "example.py"), "--demo"])
    (OUT / "demo_output.txt").write_text(demo.stdout + demo.stderr + "exit code: %d\n" % demo.returncode,
                                         encoding="utf-8")
    if demo.returncode != 0:
        failures.append("demo")

    # 4. the official check
    tests = run(UNITTEST)
    (OUT / "unittest_output.txt").write_text(
        tests.stdout + tests.stderr + "exit code: %d\n" % tests.returncode, encoding="utf-8")
    if tests.returncode != 0 or "Ran 0 tests" in tests.stderr:
        failures.append("unittest")

    # 5. deliberate wrong results must make the tests fail
    lines = []
    mutations = [
        ("example.py", "return pad(actual) >= pad(minimum)", "return pad(actual) > pad(minimum)",
         "boundary check made strict (>= became >)"),
        ("manifest.json", '"expected": "arm"', '"expected": "x86_64"',
         "manifest expectation changed (arm became x86_64)"),
    ]
    for filename, old, new, label in mutations:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "Module04" / "applied-labs" / "r04-t047"
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
