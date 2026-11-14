# R04-T047: Platform-compatibility preflight (failure and recovery)

A small, local example for the lesson [Section 4: Apple MLX Framework Deep Dive](../../05.AppleMLX.md),
in particular its **Installation Guide > System Requirements** and the Rosetta check under
**Troubleshooting > Installation Problems**.

> **Simulation notice.** Everything here is a simulation. The checker compares a small JSON
> *fixture* (a description of a machine) with a manifest. It never inspects the computer it runs on,
> installs MLX, downloads a model, or uses a GPU. A PASS here says nothing about how MLX would
> behave on real hardware.

## How this illustrates the lesson, and where it stops

The lesson tells readers that MLX needs macOS 13.0+, Python 3.8+, Apple Silicon, a native ARM
(not Rosetta) environment and 8GB+ RAM, and that `platform.processor()` should print `arm`, not
`i386`. This example turns those sentences into a manifest (`manifest.json`), so a reader can see
what a preflight check does when a machine matches, when one field is wrong (the Rosetta case), when
a fact is missing, and when the input is malformed.

Simplifications:

- Fixtures stand in for real machines. Real detection (`platform`, `sysctl`) is deliberately left out.
- `architecture` uses the lesson's `platform.processor()` values (`arm` / `i386`), not `platform.machine()` (`arm64`).
- The lesson names no GPU API. The manifest's `backend` is `mlx`, taken from the lesson's `pip install mlx-lm`; nothing about Metal is assumed.
- The chip family (M1 to M4) and the Python build (native ARM Python) are not separate fields.
- RAM below the recommended 16GB is a warning, not a failure, because the lesson only recommends it.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | The requirements, each with the exact lesson wording it was taken from (`lesson_quotes`) |
| `example.py` | The checker and a small CLI (standard library only) |
| `fixtures/*.json` | Local machine descriptions used by the tests and the demo |
| `test_example.py` | `unittest` tests: pass, boundary, failure, missing data, invalid data, recovery, exit codes |

## Run it

From the repository root:

```bash
python3 Module04/applied-labs/r04-t047/example.py Module04/applied-labs/r04-t047/fixtures/rosetta_architecture_i386.json
python3 Module04/applied-labs/r04-t047/example.py --demo
python3 -m unittest discover -s Module04/applied-labs/r04-t047 -p "test_*.py"
```

## Outcomes and exit codes

| Verdict | Meaning | Exit code |
|---|---|---|
| `PASS` | every field matches | 0 |
| `FAIL` | a reported field mismatches; the field is named with expected and actual values | 1 |
| `INCOMPLETE` | nothing mismatches but a field was not reported; it is listed as unknown, never guessed | 2 |
| invalid input | malformed fixture or manifest; the error says what to fix | 3 |

Each field line also prints the exact lesson requirement it came from.

## Failure and recovery

`--demo` runs five inputs in order. The checker keeps no state, so every input is judged on its own:

1. `ok_macos14_arm_mlx.json` passes.
2. `rosetta_architecture_i386.json` fails on `architecture` (expected `'arm'`, actual `'i386'`).
3. `missing_backend.json` has no `backend`, so the result is `INCOMPLETE` with `backend` unknown.
4. `invalid_ram_gb.json` has `"ram_gb": "lots"`. This is rejected with an explanation and nothing is guessed.
5. `ok_boundary_minimums.json` is the next valid input. It passes (with a RAM advisory), which is the recovery.

## Fixture format

```json
{"os_name": "macOS", "os_version": "14.5", "architecture": "arm", "python_version": "3.11", "backend": "mlx", "ram_gb": 16}
```

Versions are strings (`"3.10"`, not `3.10`, which JSON would read as 3.1) and are compared number by number. Extra fields are ignored.

## Keeping the manifest honest

When `Module04/05.AppleMLX.md` is present, the CLI and a test confirm every `lesson_quotes` entry still appears in it (markdown bold markers ignored). If the lesson wording changes, the check fails and says which quote is missing.
