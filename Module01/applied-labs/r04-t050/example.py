"""R04-T050 - Platform-compatibility preflight: boundary-case lesson extension
(Module01/04.EdgeDeployment.md, "Section 4: Edge AI Deployment Hardware Platforms").

Contract (small and local):
  * The requirements live in manifest.json, which records the lesson file, the pinned commit and
    where in the lesson each rule comes from. The profile is the one the lesson spells out in its
    Windows AI PCs section: Snapdragon X Elite/Plus (Qualcomm Oryon CPU, Hexagon NPU, DirectML).
  * The checker is independent of the real hardware: it only looks at an OBSERVATION dict.
  * A matching observation passes. A changed architecture (the CPU family) fails and names the
    mismatched field. A capability that is not reported is MISSING_DATA, never guessed.

Focus - the smallest valid, boundary and invalid cases, and the exact boundary decision:
  * The lesson writes the NPU as "45+ TOPS". This check reads that as 45 OR MORE (inclusive):
    exactly 45 passes, 44.9999 fails, and there is no rounding or tolerance. The decision is stored
    in the manifest (`inclusive`, `boundary_note`) so it can be changed in one place and is printed
    in the failure message.
  * Smallest valid observation: only the four required fields, with npu_tops exactly 45.
  * A number of 0 is a VALID observation that fails the minimum; text, booleans, NaN, infinity and
    negative numbers are INVALID input (not converted, not guessed).
  * Text fields are compared exactly: no trimming, no case-folding. A blank text field is missing.

SIMULATION ONLY: observations are small fixtures. Nothing here inspects real hardware, and the
45 TOPS figure is the lesson's statement, not a measurement. It makes no claim about real devices,
cloud services or model performance. Standard library only (Python 3).
"""

import copy
import json
import math
import os
from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence, Tuple

KINDS = ("equals", "min_number")


class ManifestError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class ObservationError(ValueError):
    """The observation itself is malformed, so nothing can be checked. `message` says how to fix it."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# --- manifest ----------------------------------------------------------------------
def validate_manifest(manifest) -> None:
    if not isinstance(manifest, Mapping) or not isinstance(manifest.get("lesson"), Mapping):
        raise ManifestError("MISSING_KEY", "manifest needs a 'lesson' object")
    for key in ("file", "commit"):
        if not manifest["lesson"].get(key):
            raise ManifestError("MISSING_KEY", f"manifest lesson needs '{key}'")
    rules = manifest.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ManifestError("EMPTY_RULES", "manifest needs at least one rule")
    seen = set()
    for rule in rules:
        for key in ("id", "field", "kind", "lesson_section", "lesson_says"):
            if not rule.get(key):
                raise ManifestError("MISSING_KEY", f"rule {rule.get('id', '?')!r} needs '{key}'")
        if rule["kind"] not in KINDS:
            raise ManifestError("UNKNOWN_KIND", f"rule '{rule['id']}' has unknown kind '{rule['kind']}'")
        if rule["kind"] == "equals" and "expected" not in rule:
            raise ManifestError("MISSING_KEY", f"rule '{rule['id']}' needs 'expected'")
        if rule["kind"] == "min_number":
            if "minimum" not in rule:
                raise ManifestError("MISSING_KEY", f"rule '{rule['id']}' needs 'minimum'")
            if not isinstance(rule.get("inclusive"), bool):
                raise ManifestError("BAD_BOUNDARY", f"rule '{rule['id']}' must say whether its boundary is inclusive (true/false)")
            if not rule.get("boundary_note"):
                raise ManifestError("BAD_BOUNDARY", f"rule '{rule['id']}' must explain its boundary decision in 'boundary_note'")
        if rule["id"] in seen:
            raise ManifestError("DUPLICATE_RULE", f"rule id '{rule['id']}' is used twice")
        seen.add(rule["id"])


def load_manifest(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    validate_manifest(manifest)
    return manifest


# --- checking ----------------------------------------------------------------------
@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    field: str
    status: str   # OK, MISMATCH, MISSING_DATA
    message: str


@dataclass(frozen=True)
class Report:
    results: Tuple[RuleResult, ...]

    @property
    def failures(self) -> Tuple[RuleResult, ...]:
        return tuple(r for r in self.results if r.status != "OK")

    @property
    def passed(self) -> bool:
        return not self.failures


def fmt(value) -> str:
    """Show a number exactly: 45 -> '45', 44.9 -> '44.9', 44.99999999999999 stays distinguishable."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return repr(value)


def is_missing(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _validate_observation(rules: Sequence[Mapping], observed) -> None:
    if not isinstance(observed, Mapping):
        raise ObservationError("NOT_A_MAPPING", "the observation must be a mapping of field name to value; nothing was checked")
    for rule in rules:
        value, field = observed.get(rule["field"]), rule["field"]
        if is_missing(value):
            continue  # missing data is reported per rule; it is not malformed input
        if rule["kind"] == "equals" and not isinstance(value, str):
            raise ObservationError("BAD_TYPE", f"'{field}' must be text, got {type(value).__name__}; fix it and send the observation again")
        if rule["kind"] == "min_number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ObservationError("BAD_TYPE", f"'{field}' must be a number, got {type(value).__name__}; text is never converted, so fix it and send the observation again")
            if not math.isfinite(value) or value < 0:
                raise ObservationError("BAD_VALUE", f"'{field}' must be a finite number >= 0 (0 is allowed); fix it and send the observation again")


class PlatformChecker:
    """Manifest-driven checker. It keeps no state, so every observation is judged on its own."""

    def __init__(self, manifest: Mapping):
        validate_manifest(manifest)
        self.manifest = copy.deepcopy(manifest)

    def check(self, observed) -> Report:
        rules = self.manifest["rules"]
        _validate_observation(rules, observed)  # malformed input raises before any result exists
        results: List[RuleResult] = []
        for rule in rules:
            field, value = rule["field"], observed.get(rule["field"])
            if is_missing(value):
                results.append(RuleResult(rule["id"], field, "MISSING_DATA",
                                          f"{rule['id']}: MISSING_DATA: field '{field}' was not reported; "
                                          f"not guessing -> report '{field}' and re-run"))
            elif rule["kind"] == "equals":
                if value == rule["expected"]:
                    results.append(RuleResult(rule["id"], field, "OK",
                                              f"{rule['id']}: {value} (required: {rule['expected']})"))
                else:
                    results.append(RuleResult(rule["id"], field, "MISMATCH",
                                              f"{rule['id']}: MISMATCH on field '{field}': observed {value!r}, "
                                              f"required {rule['expected']!r} -> {rule['on_failure']}"))
            else:  # min_number, with an explicit boundary decision
                minimum, inclusive = rule["minimum"], rule["inclusive"]
                ok = value >= minimum if inclusive else value > minimum
                operator = ">=" if inclusive else ">"
                if ok:
                    note = " - exactly on the boundary, which passes" if (inclusive and value == minimum) else ""
                    results.append(RuleResult(rule["id"], field, "OK",
                                              f"{rule['id']}: {fmt(value)} (required: {operator} {fmt(minimum)}){note}"))
                else:
                    results.append(RuleResult(rule["id"], field, "MISMATCH",
                                              f"{rule['id']}: MISMATCH on field '{field}': observed {fmt(value)}, "
                                              f"required {operator} {fmt(minimum)} -> {rule['boundary_note']}"))
        return Report(tuple(results))


def render_report(report: Report) -> str:
    lines = [f"[{' OK ' if r.status == 'OK' else 'FAIL'}] {r.message}" for r in report.results]
    if report.failures:
        lines.append(f"RESULT: FAILED - {len(report.failures)} of {len(report.results)} checks need attention")
    else:
        lines.append(f"RESULT: PASSED - {len(report.results)} of {len(report.results)} checks ok")
    return "\n".join(lines)


def run_session(checker: PlatformChecker, cases: Sequence[Tuple[str, object]]) -> str:
    """Check observations one after another; an invalid one never stops the next."""
    blocks = []
    for label, observation in cases:
        try:
            body = render_report(checker.check(observation))
        except ObservationError as err:
            body = f"INVALID INPUT ({err.code}): {err.message}"
        blocks.append(f"== {label}\n{body}")
    return "\n\n".join(blocks) + "\n"


# --- fixtures (used by the demo, the README and the tests) ----------------------------
SMALLEST_VALID = {"os_name": "Windows", "cpu_family": "Qualcomm Oryon", "npu_tops": 45, "backend": "DirectML"}
JUST_BELOW = {**SMALLEST_VALID, "npu_tops": 44.9}
ZERO_NPU = {**SMALLEST_VALID, "npu_tops": 0}
CHANGED_ARCHITECTURE = {**SMALLEST_VALID, "cpu_family": "Intel Core Ultra"}
MISSING_NPU = {k: v for k, v in SMALLEST_VALID.items() if k != "npu_tops"}
TEXT_NPU = {**SMALLEST_VALID, "npu_tops": "45"}
NAN_NPU = {**SMALLEST_VALID, "npu_tops": float("nan")}

CASES = (
    ("case 1 - smallest valid: only the four required fields, npu_tops exactly 45", SMALLEST_VALID),
    ("case 2 - boundary: npu_tops just below 45 (44.9)", JUST_BELOW),
    ("case 3 - boundary: npu_tops 0 (a valid number, but below the minimum)", ZERO_NPU),
    ("case 4 - changed architecture: cpu_family is 'Intel Core Ultra'", CHANGED_ARCHITECTURE),
    ("case 5 - missing capability: npu_tops not reported", MISSING_NPU),
    ("case 6 - invalid: npu_tops given as text '45'", TEXT_NPU),
    ("case 7 - invalid: npu_tops is NaN", NAN_NPU),
)


def main(manifest_path: Optional[str] = None) -> None:
    path = manifest_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")
    print(run_session(PlatformChecker(load_manifest(path)), CASES), end="")


if __name__ == "__main__":
    main()
