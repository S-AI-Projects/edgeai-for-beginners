#!/usr/bin/env python3
"""R04-T047: manifest-driven platform-compatibility preflight (failure and recovery).

The requirements come from a manifest (manifest.json) whose entries quote the
lesson Module04/05.AppleMLX.md. The checker only compares a *fixture* (a small
JSON description of a machine) against that manifest. It never inspects the
machine it runs on, so results are identical on any computer.

Outcomes
  pass        every required field matches
  fail        at least one reported field mismatches (the field is named)
  incomplete  nothing mismatches, but a required field was not reported;
              it is listed as unknown and is never guessed
  invalid     the fixture or manifest is malformed (an explained error)

Exit codes: 0 pass, 1 fail, 2 incomplete, 3 invalid input.

Standard library only; written to run on Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "manifest.json"
DEFAULT_LESSON = HERE.parent.parent / "05.AppleMLX.md"
FIXTURE_DIR = HERE / "fixtures"

PASS, FAIL, UNKNOWN = "pass", "fail", "unknown"
EXIT_PASS, EXIT_FAIL, EXIT_INCOMPLETE, EXIT_INVALID = 0, 1, 2, 3
VERDICT_EXIT = {"pass": EXIT_PASS, "fail": EXIT_FAIL, "incomplete": EXIT_INCOMPLETE}
KINDS = ("equals", "min_version", "min_number")

DEMO_SEQUENCE = (
    "ok_macos14_arm_mlx.json",
    "rosetta_architecture_i386.json",
    "missing_backend.json",
    "invalid_ram_gb.json",
    "ok_boundary_minimums.json",  # recovery: next valid input
)


class ManifestError(ValueError):
    """The manifest (or the lesson it quotes) is unusable."""


class FixtureError(ValueError):
    """The fixture is malformed. Nothing is guessed; the message says what to fix."""


@dataclass
class FieldResult:
    field: str
    status: str
    expected: Any
    actual: Any
    quotes: List[str]
    detail: str


@dataclass
class Report:
    verdict: str
    results: List[FieldResult]
    warnings: List[str] = field(default_factory=list)

    def mismatched_fields(self) -> List[str]:
        return [r.field for r in self.results if r.status == FAIL]

    def unknown_fields(self) -> List[str]:
        return [r.field for r in self.results if r.status == UNKNOWN]


# ---------------------------------------------------------------- parsing helpers

def _parse_version(value: Any, label: str, exc: type) -> Tuple[int, ...]:
    """'3.10' -> (3, 10). Versions must be strings: JSON 3.10 would silently become 3.1."""
    if not isinstance(value, str):
        raise exc(
            "%s must be a version string such as \"3.10\", got %r (%s). "
            "Write versions as strings so 3.10 is not read as 3.1."
            % (label, value, type(value).__name__)
        )
    parts = value.strip().split(".")
    if not all(p.isdigit() and p.isascii() for p in parts):
        raise exc(
            "%s must look like 14 or 14.5 or 14.5.1 (digits separated by dots), got %r."
            % (label, value)
        )
    return tuple(int(p) for p in parts)


def _version_at_least(actual: Tuple[int, ...], minimum: Tuple[int, ...]) -> bool:
    width = max(len(actual), len(minimum))
    pad = lambda v: v + (0,) * (width - len(v))  # noqa: E731
    return pad(actual) >= pad(minimum)


def _as_number(value: Any, label: str, exc: type) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise exc(
            "%s must be a non-negative number of gigabytes (for example 16), got %r (%s). "
            "Nothing was guessed; fix the value and re-run."
            % (label, value, type(value).__name__)
        )
    return value


def _fmt(value: Any) -> str:
    return "<not reported>" if value is None else repr(value)


# ---------------------------------------------------------------- manifest + lesson

def validate_manifest(manifest: Any) -> None:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("requirements"), list) \
            or not manifest["requirements"]:
        raise ManifestError("manifest must be an object with a non-empty 'requirements' list")
    seen = set()
    for i, req in enumerate(manifest["requirements"]):
        where = "requirements[%d]" % i
        if not isinstance(req, dict):
            raise ManifestError("%s must be an object" % where)
        for key in ("field", "kind", "expected", "lesson_quotes"):
            if key not in req:
                raise ManifestError("%s is missing '%s'" % (where, key))
        if req["kind"] not in KINDS:
            raise ManifestError("%s has unknown kind %r (allowed: %s)"
                                % (where, req["kind"], ", ".join(KINDS)))
        if req["field"] in seen:
            raise ManifestError("%s repeats field %r" % (where, req["field"]))
        seen.add(req["field"])
        quotes = req["lesson_quotes"]
        if not isinstance(quotes, list) or not quotes \
                or not all(isinstance(q, str) and q.strip() for q in quotes):
            raise ManifestError("%s needs a non-empty list of lesson_quotes (the exact "
                                "lesson wording the requirement comes from)" % where)
        if req["kind"] == "min_version":
            _parse_version(req["expected"], where + ".expected", ManifestError)
        elif req["kind"] == "min_number":
            _as_number(req["expected"], where + ".expected", ManifestError)
            if "advisory_min" in req:
                _as_number(req["advisory_min"], where + ".advisory_min", ManifestError)
        elif not isinstance(req["expected"], str):
            raise ManifestError("%s.expected must be a string for kind 'equals'" % where)


def load_manifest(path: Path) -> Dict[str, Any]:
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestError("manifest not found: %s" % path) from None
    except json.JSONDecodeError as exc:
        raise ManifestError("manifest is not valid JSON: %s" % exc) from None
    validate_manifest(manifest)
    return manifest


def _normalise(text: str) -> str:
    """Drop markdown bold markers and collapse whitespace before comparing quotes."""
    return " ".join(text.replace("*", "").split())


def all_quotes(manifest: Dict[str, Any]) -> List[str]:
    quotes: List[str] = []
    for req in manifest["requirements"]:
        for q in req["lesson_quotes"]:
            if q not in quotes:
                quotes.append(q)
    return quotes


def missing_quotes(manifest: Dict[str, Any], lesson_text: str) -> List[str]:
    haystack = _normalise(lesson_text)
    return [q for q in all_quotes(manifest) if _normalise(q) not in haystack]


def lesson_status(manifest: Dict[str, Any], lesson_path: Path) -> str:
    """Confirm the quoted requirements still appear in the lesson, if it is available."""
    name = manifest.get("lesson", "lesson")
    if not Path(lesson_path).is_file():
        return "lesson check: %s not found; quotes NOT verified against the lesson" % name
    missing = missing_quotes(manifest, Path(lesson_path).read_text(encoding="utf-8"))
    if missing:
        raise ManifestError(
            "the lesson %s no longer contains these quoted requirements (manifest is out "
            "of date): %s" % (name, "; ".join(repr(q) for q in missing)))
    return "lesson check: all %d quoted requirement(s) found in %s" % (len(all_quotes(manifest)), name)


# ---------------------------------------------------------------- the checker

def check_platform(fixture: Any, manifest: Dict[str, Any]) -> Report:
    """Compare a fixture with the manifest. Pure function: no hardware, no network, no files."""
    if not isinstance(fixture, dict):
        raise FixtureError("fixture must be a JSON object of field -> value, got %s"
                           % type(fixture).__name__)
    results: List[FieldResult] = []
    warnings: List[str] = []
    for req in manifest["requirements"]:
        name, kind, expected = req["field"], req["kind"], req["expected"]
        quotes = list(req["lesson_quotes"])
        actual = fixture.get(name)
        if actual is None:
            results.append(FieldResult(name, UNKNOWN, expected, None, quotes,
                                       "%s was not reported; it is listed as unknown, not guessed" % name))
            continue
        if kind == "equals":
            if not isinstance(actual, str):
                raise FixtureError("%s must be a string such as %r, got %r (%s)"
                                   % (name, expected, actual, type(actual).__name__))
            ok = actual == expected
            detail = "matches" if ok else "expected %r, got %r" % (expected, actual)
        elif kind == "min_version":
            ok = _version_at_least(_parse_version(actual, name, FixtureError),
                                   _parse_version(expected, name, ManifestError))
            detail = ("%s is at least %s" if ok else "%s is below the required minimum %s") % (actual, expected)
        else:  # min_number
            number = _as_number(actual, name, FixtureError)
            ok = number >= expected
            detail = ("%g is at least %g" if ok else "%g is below the required minimum %g") % (number, expected)
            advisory = req.get("advisory_min")
            if ok and advisory is not None and number < advisory:
                warnings.append("%s: %g is below the lesson's recommended %g (%s)"
                                % (name, number, advisory, quotes[0]))
        results.append(FieldResult(name, PASS if ok else FAIL, expected, actual, quotes, detail))

    if any(r.status == FAIL for r in results):
        verdict = "fail"
    elif any(r.status == UNKNOWN for r in results):
        verdict = "incomplete"
    else:
        verdict = "pass"
    return Report(verdict, results, warnings)


def load_fixture(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FixtureError("fixture file not found: %s" % path) from None
    except json.JSONDecodeError as exc:
        raise FixtureError("fixture is not valid JSON (%s). Fix the file and re-run." % exc) from None


def run_batch(items: Sequence[Tuple[str, Any]], manifest: Dict[str, Any]
              ) -> List[Tuple[str, Optional[Report], Optional[str]]]:
    """Check each (name, fixture). A malformed fixture is reported and the batch carries on."""
    outcomes: List[Tuple[str, Optional[Report], Optional[str]]] = []
    for name, data in items:
        try:
            outcomes.append((name, check_platform(data, manifest), None))
        except FixtureError as exc:
            outcomes.append((name, None, str(exc)))
    return outcomes


# ---------------------------------------------------------------- output

def format_report(report: Report) -> str:
    lines = ["verdict: %s" % report.verdict.upper()]
    for r in report.results:
        lines.append("  [%s] %s: expected %s, actual %s" % (r.status.upper(), r.field, _fmt(r.expected), _fmt(r.actual)))
        lines.append("         lesson requirement: %s" % " | ".join('"%s"' % q for q in r.quotes))
    for w in report.warnings:
        lines.append("  [WARN] " + w)
    if report.mismatched_fields():
        lines.append("mismatched: " + ", ".join(report.mismatched_fields()))
    if report.unknown_fields():
        lines.append("unknown (not guessed): " + ", ".join(report.unknown_fields()))
    return "\n".join(lines)


def run_demo(manifest: Dict[str, Any], fixture_dir: Path = FIXTURE_DIR) -> int:
    items: List[Tuple[str, Any]] = []
    for name in DEMO_SEQUENCE:
        try:
            items.append((name, load_fixture(fixture_dir / name)))
        except FixtureError as exc:
            items.append((name, exc))  # surfaced as invalid below
    counts = {"pass": 0, "fail": 0, "incomplete": 0, "invalid": 0}
    last_verdict = None
    for index, (name, data) in enumerate(items, 1):
        print("== input %d/%d: %s" % (index, len(items), name))
        if isinstance(data, FixtureError):
            outcome: Tuple[str, Optional[Report], Optional[str]] = (name, None, str(data))
        else:
            outcome = run_batch([(name, data)], manifest)[0]
        _, report, error = outcome
        if report is None:
            counts["invalid"] += 1
            last_verdict = "invalid"
            print("INVALID INPUT: %s" % error)
            print("  -> this input was rejected without guessing; the next input is checked normally")
        else:
            counts[report.verdict] += 1
            last_verdict = report.verdict
            print(format_report(report))
    print("summary: pass=%(pass)d fail=%(fail)d incomplete=%(incomplete)d invalid=%(invalid)d" % counts)
    recovered = last_verdict == "pass" and counts["invalid"] > 0
    print("recovery: %s" % ("last input passed after the invalid one" if recovered else "NOT demonstrated"))
    return EXIT_PASS if recovered else EXIT_FAIL


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("fixture", nargs="?", type=Path, help="fixture JSON to check")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lesson", type=Path, default=DEFAULT_LESSON)
    parser.add_argument("--demo", action="store_true", help="run the failure-and-recovery sequence")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        print(lesson_status(manifest, args.lesson))
        if args.demo:
            return run_demo(manifest)
        if args.fixture is None:
            print("INVALID INPUT: give a fixture file or --demo", file=sys.stderr)
            return EXIT_INVALID
        report = check_platform(load_fixture(args.fixture), manifest)
    except (ManifestError, FixtureError) as exc:
        print("INVALID INPUT: %s" % exc, file=sys.stderr)
        return EXIT_INVALID
    print(format_report(report))
    return VERDICT_EXIT[report.verdict]


if __name__ == "__main__":
    sys.exit(main())
