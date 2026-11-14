# R04-T050 - Platform-compatibility preflight: boundary-case lesson extension

Companion to [Module01/04.EdgeDeployment.md](../../04.EdgeDeployment.md)
("Section 4: Edge AI Deployment Hardware Platforms").

## How this illustrates the lesson, and where it stops
This lesson is a **hardware platform overview**, not an install guide, so it has no prerequisites
checklist. What it does state, in its **Windows AI PCs** section, is the profile of the Snapdragon X
Elite/Plus platform: a Qualcomm Oryon CPU, a Hexagon NPU of 45+ TOPS, and a development approach
built on DirectML. `example.py` turns those statements into a small **manifest-driven** check
(`manifest.json`) that works on an *observation* you supply, so it is independent of the real hardware.

**The exact lesson requirements used** (recorded in `manifest.json` with the file, pinned commit
`e88f123a4bb5796594919db3a13257c429d1288c`, and where each rule comes from):

| Rule | Required | Where in the lesson |
|---|---|---|
| `os_name` | `Windows` | Windows AI PCs, introduction |
| `architecture` (field `cpu_family`) | `Qualcomm Oryon` | Windows AI PCs > Qualcomm Snapdragon X Elite/Plus, CPU bullet |
| `npu_tops` | 45 or more (the lesson writes `45+`) | Windows AI PCs > Qualcomm Snapdragon X Elite/Plus, Hexagon NPU bullet |
| `backend` | `DirectML` | Windows AI PCs > Development Approach; Tools and SDKs |

**Explicit unknowns** (listed in the manifest, so they are not guessed):
- The lesson gives no minimum Windows version, RAM or storage for these PCs, so none is checked.
- It names no instruction set (Arm or x86) for the Oryon CPU, so "architecture" means the CPU family the lesson names.
- The 45 TOPS figure is the lesson's statement; this checker only compares a number it is given and measures nothing.

**Simplifications:** observations are small dicts. Nothing here inspects a real PC, runs DirectML or a
model, and it says nothing about how fast any real device is. Intel Core Ultra and AMD Ryzen AI are
other platforms in the lesson with their own figures; they are not part of this profile.

## The exact boundary decision
The lesson writes the NPU as **`45+` TOPS**. This check reads that as **45 or more (inclusive)**.

| Observed `npu_tops` | Result | Why |
|---|---|---|
| `45` (or `45.0`) | passes | exactly on the boundary; `45+` includes 45 |
| `44.9`, `44.99999999999999` | fails | below 45; there is no rounding and no tolerance |
| `45.0000001` | passes | above 45 |
| `0` | fails (a valid observation) | a device can report 0; it is simply below the minimum |
| `"45"` (text), `True` | invalid input | text and booleans are never converted to numbers |
| `NaN`, infinity, negative | invalid input | not a usable measurement |
| not reported (absent, `None`) | `MISSING_DATA` | reported, never guessed |

The decision is stored in the manifest (`inclusive: true` plus a `boundary_note`), so it is printed in the
failure message and can be changed in one place. Text fields are compared exactly: no trimming and no
case-folding (so `directml` does not match `DirectML`), and a blank text field counts as missing.

| Public part | Role |
|---|---|
| `load_manifest(path)` / `validate_manifest` | read and validate the requirements (`ManifestError`) |
| `PlatformChecker(manifest).check(observed)` | the stateless check; returns a `Report` or raises `ObservationError` |
| `render_report`, `run_session` | the text shown to the user; `run_session` checks several observations in a row |

## Worked example: smallest valid, boundary and invalid cases (exact output)
**Input:** seven observations, checked one after another by the same checker (the fixtures are in
`example.py`): the smallest valid one (only the four required fields, `npu_tops` exactly 45); `44.9`; `0`;
a changed CPU family; no `npu_tops`; `npu_tops` as text; and `npu_tops` as NaN.

```
== case 1 - smallest valid: only the four required fields, npu_tops exactly 45
[ OK ] os_name: Windows (required: Windows)
[ OK ] architecture: Qualcomm Oryon (required: Qualcomm Oryon)
[ OK ] npu_tops: 45 (required: >= 45) - exactly on the boundary, which passes
[ OK ] backend: DirectML (required: DirectML)
RESULT: PASSED - 4 of 4 checks ok

== case 2 - boundary: npu_tops just below 45 (44.9)
[ OK ] os_name: Windows (required: Windows)
[ OK ] architecture: Qualcomm Oryon (required: Qualcomm Oryon)
[FAIL] npu_tops: MISMATCH on field 'npu_tops': observed 44.9, required >= 45 -> The lesson writes '45+ TOPS'. This check reads '45+' as 45 or more (inclusive), so exactly 45 passes and anything below 45 fails; there is no rounding or tolerance.
[ OK ] backend: DirectML (required: DirectML)
RESULT: FAILED - 1 of 4 checks need attention

== case 3 - boundary: npu_tops 0 (a valid number, but below the minimum)
[ OK ] os_name: Windows (required: Windows)
[ OK ] architecture: Qualcomm Oryon (required: Qualcomm Oryon)
[FAIL] npu_tops: MISMATCH on field 'npu_tops': observed 0, required >= 45 -> The lesson writes '45+ TOPS'. This check reads '45+' as 45 or more (inclusive), so exactly 45 passes and anything below 45 fails; there is no rounding or tolerance.
[ OK ] backend: DirectML (required: DirectML)
RESULT: FAILED - 1 of 4 checks need attention

== case 4 - changed architecture: cpu_family is 'Intel Core Ultra'
[ OK ] os_name: Windows (required: Windows)
[FAIL] architecture: MISMATCH on field 'cpu_family': observed 'Intel Core Ultra', required 'Qualcomm Oryon' -> This profile is the Snapdragon X Elite/Plus platform; Intel Core Ultra and AMD Ryzen AI are separate platforms in the lesson, not this profile.
[ OK ] npu_tops: 45 (required: >= 45) - exactly on the boundary, which passes
[ OK ] backend: DirectML (required: DirectML)
RESULT: FAILED - 1 of 4 checks need attention

== case 5 - missing capability: npu_tops not reported
[ OK ] os_name: Windows (required: Windows)
[ OK ] architecture: Qualcomm Oryon (required: Qualcomm Oryon)
[FAIL] npu_tops: MISSING_DATA: field 'npu_tops' was not reported; not guessing -> report 'npu_tops' and re-run
[ OK ] backend: DirectML (required: DirectML)
RESULT: FAILED - 1 of 4 checks need attention

== case 6 - invalid: npu_tops given as text '45'
INVALID INPUT (BAD_TYPE): 'npu_tops' must be a number, got str; text is never converted, so fix it and send the observation again

== case 7 - invalid: npu_tops is NaN
INVALID INPUT (BAD_VALUE): 'npu_tops' must be a finite number >= 0 (0 is allowed); fix it and send the observation again
```

**Why:**
- *Case 1* is the smallest valid observation. It sits exactly on the boundary and passes, and the output says so.
- *Cases 2 and 3* are just below the boundary. The failure names the field and explains the decision.
- *Case 4* changes only the architecture field, so only `cpu_family` fails.
- *Case 5* is a missing capability: reported as `MISSING_DATA`, other checks still run.
- *Cases 6 and 7* are invalid input: rejected with an explanation, nothing is checked, and the checker is not left in a bad state.

## Regression test
The tests re-run this exact session and require the output to equal `worked_example.txt` and the block above,
character for character. They also patch the `platform` module to raise, to show the checker never reads the machine.

## Run
```bash
python3 Module01/applied-labs/r04-t050/example.py
python3 -m unittest discover -s Module01/applied-labs/r04-t050 -p "test_*.py"
```
Python 3 standard library only. No model download, paid provider, GPU or device.

## Limits
This is a simulation on fixtures. It makes no claim about any real device, hardware, cloud service, or the
performance of any model, and passing it does not mean a real PC meets any requirement.
