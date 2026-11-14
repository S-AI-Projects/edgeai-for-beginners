# R04-T046 - Installation preflight report: worked example with checks

Companion to [Module08/01.FoundryLocalSetup.md](../../01.FoundryLocalSetup.md)
("Session 1: Getting Started with Foundry Local").

## How this illustrates the lesson, and where it stops
The lesson's prerequisites and "Verify Installation" steps ask the reader to confirm that tools
such as `foundry`, Python and `pip` are available, and its environment-variables table lists
settings such as `MODEL`, `BASE_URL` and `API_KEY` (plus `AZURE_OPENAI_API_KEY` for Azure).
`example.py` turns that checklist into a **read-only preflight**: it checks an explicit list of
executables and config fields and reports each problem separately, with what to do next.

The lesson does not discuss redacting secrets by name. This example adds that rule because the
lesson's table includes API keys: a secret value is **never printed** (and is never even stored in
the report).

**Simplifications:** the "machine" is a fixture (a fake PATH list and a plain dict). Nothing here
installs Foundry Local, starts a service, runs `foundry --version`, or checks the lesson's system
requirements (Windows version, RAM, disk, NPU/GPU). The lesson's `API_KEY` is usually not needed for
local runs; the fixture lists it only so that hiding a secret can be demonstrated.

## The contract
| Situation | Result |
|---|---|
| Every listed executable and config field is present | `RESULT: PASSED` |
| An executable is not found | its own `[FAIL] executable <name>: not found on PATH -> <what to do>` line (`MISSING_EXECUTABLE`) |
| A config field is absent | its own `[FAIL] config <name>: not set -> <what to do>` line (`ABSENT_CONFIG`) |
| A config field is set but blank | its own `[FAIL] ... set but empty ...` line (`EMPTY_CONFIG`) |
| A field is secret (flagged, or its name contains KEY, TOKEN, SECRET or PASSWORD) | `set (value hidden)`; the value appears nowhere in the output |

| Public part | Role |
|---|---|
| `Spec`, `ExecutableRequirement`, `ConfigRequirement` | the explicit list of things to check, each with an actionable hint |
| `check_environment(spec, probe, config)` | the read-only preflight; returns a `Report` and never modifies its inputs |
| `render_report(report)` | the text shown to the user |
| `FakeProbe` / `SystemProbe` | a fixture PATH / a read-only `shutil.which` lookup (nothing is run) |
| `SpecError.code` | `EMPTY_SPEC`, `BAD_REQUIREMENT`, `DUPLICATE_REQUIREMENT`, `BAD_CONFIG` |

## Worked example A - a complete environment
**Input** (the fixture in `example.py`):
- checks: executables `foundry`, `python`, `pip`; config fields `MODEL`, `BASE_URL`, `API_KEY` (secret)
- fake PATH contains: `foundry`, `python`, `pip`
- config: `MODEL = phi-4-mini`, `BASE_URL = http://localhost:8000`, `API_KEY = demo-key-0000` (an obviously fake demo value)

**Output** (exact):
```
Foundry Local preflight (read-only: nothing installed, no service contacted)
[ OK ] executable foundry: found on PATH
[ OK ] executable python: found on PATH
[ OK ] executable pip: found on PATH
[ OK ] config MODEL: set (value: phi-4-mini)
[ OK ] config BASE_URL: set (value: http://localhost:8000)
[ OK ] config API_KEY: set (value hidden)
RESULT: PASSED - 6 of 6 checks ok
```
**Why:** all six checks find what they need. The non-secret values are shown; the `API_KEY` value is not.

## Worked example B - one missing executable and one absent config field
**Input:** the same checks, but the fake PATH contains only `foundry` and `python`, and the config has
`MODEL` and `API_KEY` but no `BASE_URL`.

**Output** (exact):
```
Foundry Local preflight (read-only: nothing installed, no service contacted)
[ OK ] executable foundry: found on PATH
[ OK ] executable python: found on PATH
[FAIL] executable pip: not found on PATH -> install pip for your Python, then re-run
[ OK ] config MODEL: set (value: phi-4-mini)
[FAIL] config BASE_URL: not set -> set BASE_URL to your Foundry Local address
[ OK ] config API_KEY: set (value hidden)
RESULT: FAILED - 2 of 6 checks need attention
```
**Why:** the missing `pip` and the absent `BASE_URL` are reported as two separate failures, each
naming the problem and the next step. `API_KEY` is present, so it passes, and its value stays hidden.

## Regression test
The tests re-run both examples and require the output to equal `worked_example.txt` **and** the two
blocks above, character for character, so this explanation cannot drift away from the code.

## Run
```bash
python3 Module08/applied-labs/r04-t046/example.py
python3 -m unittest discover -s Module08/applied-labs/r04-t046 -p "test_*.py"
```
Python 3 standard library only. No model download, paid provider, GPU or device, and no network.

## Limits
This is a simulation on fixtures. It makes no claim about any real machine, hardware, cloud service,
or the performance of any model, and it does not check that Foundry Local actually works.
