# R04-T048: Platform-compatibility preflight (scenario assessment)

A small, local example for the lesson [Section 7: Qualcomm QNN Optimization Suite](../../07.QualcommQNN.md),
in particular **Installation > Prerequisites**, the `-t` target in the Quick Start, and `--target_backends`
in Example Step 2. It comes with three applied questions (predict an output, diagnose a failure, choose a
boundary policy), each with a rationale and a check that runs the example to confirm the answer.

> **Simulation notice.** Everything here is a simulation. The checker compares a small JSON *fixture*
> (a description of a setup) with a manifest. It never inspects the computer it runs on, installs the QNN
> SDK, converts a model, or touches Qualcomm hardware or a simulator. A PASS here says nothing about how
> QNN would behave on a real device.

## How this illustrates the lesson, and where it stops

The lesson lists what you need before using QNN: the QNN SDK, Python 3.7 or higher, a Linux or Windows
development environment, and the Android NDK for mobile deployment. Its commands also show the build targets
(`-t x86_64-linux-clang`, `-t aarch64-android`) and the backends (`--target_backends htp,gpu,cpu`). The
manifest (`manifest.json`) turns those statements into checkable fields and records the exact lesson wording
next to each one.

Simplifications:

- Fixtures stand in for real setups. Real detection (SDK paths, `ldd`, `adb`) is left out on purpose.
- The Android NDK is required only when the target is `aarch64-android`, matching "for mobile deployment". For other targets the field is reported as SKIPPED.
- The lesson gives no requirement for some things, so they are listed as *not checked* and never guessed: minimum OS version, which Qualcomm hardware or simulator is compatible, SDK and NDK versions, host CPU architecture and RAM.
- `architecture` means the lesson's `-t` build target (architecture and compiler), not the host machine.
- No performance, power or speed claims are made; the lesson's benchmark figures are not used.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | The requirements, each with the exact lesson wording it was taken from (`lesson_quotes`), plus `lesson_unknowns` |
| `example.py` | The checker, the question runner and a small CLI (standard library only) |
| `questions.json` | The three applied questions with prompts, answers and rationales |
| `fixtures/*.json` | Local setup descriptions used by the tests and the questions |
| `test_example.py` | `unittest` tests: pass, boundary, failure, missing data, invalid data, questions, exit codes, hardware independence |

## Run it

From the repository root:

```bash
python3 Module04/applied-labs/r04-t048/example.py Module04/applied-labs/r04-t048/fixtures/armv7_android_target.json
python3 Module04/applied-labs/r04-t048/example.py --questions
python3 -m unittest discover -s Module04/applied-labs/r04-t048 -p "test_*.py"
```

## Outcomes and exit codes

| Verdict | Meaning | Exit code |
|---|---|---|
| `PASS` | every applicable field matches | 0 |
| `FAIL` | a reported field mismatches; the field is named with expected and actual values | 1 |
| `INCOMPLETE` | nothing mismatches but a needed field was not reported; it is listed as unknown, never guessed | 2 |
| invalid input | malformed fixture or manifest; the error says what to fix | 3 |

Each field line also prints the exact lesson requirement it came from.

## The three applied questions

`python3 .../example.py --questions` prints each question, its answer and rationale, then runs the checker
to confirm the answer (exit code 0 only if all three are confirmed).

1. **Predict an output** (`predict_output`): `ndk_not_needed.json` targets `x86_64-linux-clang` and reports `android_ndk` as `false`. The answer is `PASS` with `android_ndk` SKIPPED.
2. **Diagnose a failure** (`diagnose_failure`): `armv7_android_target.json` exits 1. The answer is that `architecture` is not one of the lesson's two `-t` targets; changing it to `aarch64-android` makes the fixture pass.
3. **Choose a boundary policy** (`boundary_policy`): for "Python 3.7 or higher" the example uses an inclusive minimum compared number by number, so `3.7`, `3.7.0`, `3.8` and `3.10` are accepted and `3.6.15` is rejected.

The tests also change each answer to a wrong one and check that it is no longer confirmed.

## Fixture format

```json
{"os_name": "Linux", "python_version": "3.11", "architecture": "x86_64-linux-clang", "backend": "htp", "qnn_sdk": true}
```

Versions are strings (`"3.10"`, not `3.10`, which JSON would read as 3.1). `qnn_sdk` and `android_ndk` are `true` or `false`. Extra fields are ignored.

## Keeping the manifest honest

When `Module04/07.QualcommQNN.md` is present, the CLI and a test confirm every `lesson_quotes` entry still appears in it (markdown bold markers ignored). If the lesson wording changes, the check fails and says which quote is missing.
