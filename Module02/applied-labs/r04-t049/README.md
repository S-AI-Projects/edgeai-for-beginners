# R04-T049: Platform-compatibility preflight (evaluation experiment)

A small, local example for the lesson [Section 6: Phi-Silica - Optimized On-Device Language Models](../../06.phisilica.md),
in particular **Understanding the Specialized NPU Hardware**, **NPU-First Architecture**, **Windows ML Integration**,
**Windows App SDK** and **Hardware Requirements**. It adds a small controlled experiment that compares three ways of
treating a missing field and reports correctness and the trade-off.

> **Simulation notice.** Everything here is a simulation. The checker compares a small JSON *fixture* (a description
> of a setup) with a manifest. It never inspects the computer it runs on, calls Windows, uses an NPU, or runs
> Phi-Silica. A PASS here says nothing about how Phi-Silica would behave on a real Copilot+ PC. The lesson's
> figures (650 tokens per second, 1.5 watts, response latency) are not used, reproduced or verified.

## How this illustrates the lesson, and where it stops

The lesson says Phi-Silica is built for Windows 11 Copilot+ PCs, is designed NPU-first, runs on the Windows ML
runtime with DirectML acceleration, is reached by developers through the Windows App SDK, and that optimal
performance requires a Copilot+ PC with NPU hardware. The manifest (`manifest.json`) turns those statements into
four checkable fields and records the exact lesson wording next to each one.

Simplifications:

- Fixtures stand in for real setups. Real detection (Windows APIs, device queries) is left out on purpose.
- `architecture` means the compute architecture the lesson describes (`npu`), not a CPU instruction set. The lesson says *optimal performance* requires NPU hardware; it does not say the model cannot run without one. The example treats `npu` as the required value for the sake of the contract.
- `backend` accepts `windows-ml` or `directml`, the two runtime pieces the lesson names.
- The lesson gives no requirement for some things, so they are listed as *not checked* and never guessed: the Windows 11 build number, CPU instruction set, NPU performance floor, RAM and disk space, the Windows App SDK version, and which devices count as Copilot+ PCs.
- The experiment's test values (`evaluation` in the manifest, such as `"Windows 10"` or `"cpu"`) are values chosen to not match the requirement. They are test inputs, not claims from the lesson.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | The requirements, each with the exact lesson wording it was taken from (`lesson_quotes`), plus `lesson_unknowns` and the experiment's test values |
| `example.py` | The checker, the evaluation experiment and a small CLI (standard library only) |
| `fixtures/*.json` | Local setup descriptions used by the tests |
| `test_example.py` | `unittest` tests: pass, failure, missing data, invalid data, the experiment, exit codes, hardware independence |

## Run it

From the repository root:

```bash
python3 Module02/applied-labs/r04-t049/example.py Module02/applied-labs/r04-t049/fixtures/cpu_architecture.json
python3 Module02/applied-labs/r04-t049/example.py --evaluate
python3 -m unittest discover -s Module02/applied-labs/r04-t049 -p "test_*.py"
```

## Outcomes and exit codes

| Verdict | Meaning | Exit code |
|---|---|---|
| `PASS` | every field matches | 0 |
| `FAIL` | a reported field mismatches; the field is named with expected and actual values | 1 |
| `INCOMPLETE` | nothing mismatches but a field was not reported; it is listed as unknown, never guessed | 2 |
| invalid input | malformed fixture or manifest; the error says what to fix | 3 |

Each field line also prints the exact lesson requirement it came from. With `--evaluate`, the exit code is 0 when the contract policy makes no wrong decision and 1 otherwise.

## The evaluation experiment

**Question.** The contract says a missing field is *reported* rather than guessed. What does that choice cost, and what would guessing cost instead?

**Three controlled configurations**, applied to the same corpus:

| Policy | A missing field is treated as |
|---|---|
| `report` (the contract) | unknown, so the verdict is `incomplete` unless something else already mismatches |
| `assume_pass` | matching |
| `assume_fail` | mismatching |

**Corpus.** Every combination of four states for each of the four fields: `correct`, `wrong`, `missing_correct` and `missing_wrong` (the field is left out, and the hidden truth is that it would have matched or not). That is 4 x 4 x 4 x 4 = 256 generated fixtures, with no randomness. A setup is truly compatible when no field is wrong, which is 2 x 2 x 2 x 2 = 16 of them. The truth comes from the generator, not from the checker, so the checker is judged against an independent answer.

**Metric.** Decision correctness: for each policy, how many fixtures get a decision, how many are left undecided, and how many decisions are wrong (a false pass or a false fail).

**Observed result** (`python3 .../example.py --evaluate`):

```text
policy        decided  undecided  correct  false_pass  false_fail  coverage  error_rate
report            176         80      176           0           0     68.8%        0.0%
assume_pass       256          0      191          65           0    100.0%       25.4%
assume_fail       256          0      241           0          15    100.0%        5.9%
```

**Trade-off.** Reporting a missing field as unknown never makes a wrong decision, but 80 of the 256 setups stay undecided. Guessing decides everything, but `assume_pass` accepts 65 setups that are not compatible and `assume_fail` rejects 15 that are. The counts can be derived by hand (see the docstring of `EvaluationTests`), and the tests check them.

**What this does not show.** These are counts over generated fixtures. They say nothing about Phi-Silica's accuracy, speed, power use or behavior on real hardware, and they depend on the fields and test values chosen here.

## Fixture format

```json
{"os_name": "Windows 11", "architecture": "npu", "backend": "windows-ml", "windows_app_sdk": true}
```

`windows_app_sdk` is `true` or `false`. Extra fields are ignored.

## Keeping the manifest honest

When `Module02/06.phisilica.md` is present, the CLI and a test confirm every `lesson_quotes` entry still appears in it (markdown bold markers ignored). If the lesson wording changes, the check fails and says which quote is missing.
