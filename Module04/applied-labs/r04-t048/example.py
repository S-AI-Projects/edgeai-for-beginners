#!/usr/bin/env python3
"""R04-T048: manifest-driven platform-compatibility preflight (scenario assessment).

Requirements come from manifest.json, whose entries quote the lesson
Module04/07.QualcommQNN.md. The checker compares a *fixture* (a small JSON
description of a setup) with that manifest. It never inspects the computer it
runs on, so results are identical on any machine.

Outcomes
  pass        every applicable field matches
  fail        at least one reported field mismatches (the field is named)
  incomplete  nothing mismatches, but a needed field was not reported; it is
              listed as unknown and is never guessed
  invalid     the fixture or manifest is malformed (an explained error)

Exit codes: 0 pass, 1 fail, 2 incomplete, 3 invalid input.
With --questions: 0 when every worked answer is confirmed by running the
checker, 1 otherwise.

Standard library only; written to run on Python 3.7+.
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
DEFAULT_QUESTIONS = HERE / "questions.json"
DEFAULT_LESSON = HERE.parent.parent / "07.QualcommQNN.md"

PASS, FAIL, UNKNOWN, SKIPPED = "pass", "fail", "unknown", "skipped"
EXIT_PASS, EXIT_FAIL, EXIT_INCOMPLETE, EXIT_INVALID = 0, 1, 2, 3
VERDICT_EXIT = {"pass": EXIT_PASS, "fail": EXIT_FAIL, "incomplete": EXIT_INCOMPLETE}
KINDS = ("one_of", "min_version", "flag")
QUESTION_KINDS = ("predict_output", "diagnose_failure", "boundary_policy")


class ManifestError(ValueError):
    """The manifest, questions file or lesson it quotes is unusable."""


class FixtureError(ValueError):
    """The fixture is malformed. Nothing is guessed; the message says what to fix."""


@dataclass
class FieldResult:
    field: str
    status: str
    kind: str
    expected: Any
    actual: Any
    quotes: List[str]
    detail: str


@dataclass
class Report:
    verdict: str
    results: List[FieldResult]
    not_checked: List[str] = field(default_factory=list)

    def mismatched_fields(self) -> List[str]:
        return [r.field for r in self.results if r.status == FAIL]

    def unknown_fields(self) -> List[str]:
        return [r.field for r in self.results if r.status == UNKNOWN]

    def statuses(self) -> Dict[str, str]:
        return {r.field: r.status for r in self.results}


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
        raise exc("%s must look like 3 or 3.7 or 3.7.1 (digits separated by dots), got %r."
                  % (label, value))
    return tuple(int(p) for p in parts)


def _version_at_least(actual: Tuple[int, ...], minimum: Tuple[int, ...]) -> bool:
    width = max(len(actual), len(minimum))
    pad = lambda v: v + (0,) * (width - len(v))  # noqa: E731
    return pad(actual) >= pad(minimum)


def _fmt(value: Any) -> str:
    if value is None:
        return "<not reported>"
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value)


def _expected_text(result: FieldResult) -> str:
    if result.kind == "one_of":
        return "one of " + ", ".join(repr(e) for e in result.expected)
    if result.kind == "min_version":
        return "at least %r" % (result.expected,)
    return "true" if result.expected else "false"


# ---------------------------------------------------------------- manifest + lesson

def validate_manifest(manifest: Any) -> None:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("requirements"), list) \
            or not manifest["requirements"]:
        raise ManifestError("manifest must be an object with a non-empty 'requirements' list")
    seen: List[str] = []
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
        quotes = req["lesson_quotes"]
        if not isinstance(quotes, list) or not quotes \
                or not all(isinstance(q, str) and q.strip() for q in quotes):
            raise ManifestError("%s needs a non-empty list of lesson_quotes (the exact "
                                "lesson wording the requirement comes from)" % where)
        if req["kind"] == "one_of":
            allowed = req["expected"]
            if not isinstance(allowed, list) or not allowed \
                    or not all(isinstance(a, str) and a for a in allowed):
                raise ManifestError("%s.expected must be a non-empty list of strings for kind 'one_of'" % where)
        elif req["kind"] == "min_version":
            _parse_version(req["expected"], where + ".expected", ManifestError)
        elif not isinstance(req["expected"], bool):
            raise ManifestError("%s.expected must be true or false for kind 'flag'" % where)
        when = req.get("when")
        if when is not None:
            if not isinstance(when, dict) or when.get("field") not in seen \
                    or not isinstance(when.get("equals"), str):
                raise ManifestError("%s.when must name an earlier field and give an 'equals' string" % where)
        seen.append(req["field"])
    unknowns = manifest.get("lesson_unknowns", [])
    if not isinstance(unknowns, list) or not all(isinstance(u, str) and u for u in unknowns):
        raise ManifestError("lesson_unknowns must be a list of strings")


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
    for req in manifest["requirements"]:
        name, kind, expected = req["field"], req["kind"], req["expected"]
        quotes = list(req["lesson_quotes"])
        when = req.get("when")
        if when is not None:
            gate = fixture.get(when["field"])
            if gate is None:
                results.append(FieldResult(
                    name, UNKNOWN, kind, expected, None, quotes,
                    "%s applies only when %s is %r, and %s was not reported; not guessed"
                    % (name, when["field"], when["equals"], when["field"])))
                continue
            if gate != when["equals"]:
                results.append(FieldResult(
                    name, SKIPPED, kind, expected, fixture.get(name), quotes,
                    "not applicable because %s is %r (applies only when it is %r)"
                    % (when["field"], gate, when["equals"])))
                continue
        actual = fixture.get(name)
        if actual is None:
            results.append(FieldResult(name, UNKNOWN, kind, expected, None, quotes,
                                       "%s was not reported; it is listed as unknown, not guessed" % name))
            continue
        if kind == "one_of":
            if not isinstance(actual, str):
                raise FixtureError("%s must be a string such as %r, got %r (%s)"
                                   % (name, expected[0], actual, type(actual).__name__))
            ok = actual in expected
            detail = "matches" if ok else "expected one of %s, got %r" % (
                ", ".join(repr(e) for e in expected), actual)
        elif kind == "min_version":
            ok = _version_at_least(_parse_version(actual, name, FixtureError),
                                   _parse_version(expected, name, ManifestError))
            detail = ("%s is at least %s" if ok else "%s is below the required minimum %s") % (actual, expected)
        else:  # flag
            if not isinstance(actual, bool):
                raise FixtureError("%s must be true or false, got %r (%s). Nothing was guessed; "
                                   "fix the value and re-run." % (name, actual, type(actual).__name__))
            ok = actual == expected
            detail = "present" if ok else "reported as false, but the lesson requires it"
        results.append(FieldResult(name, PASS if ok else FAIL, kind, expected, actual, quotes, detail))

    if any(r.status == FAIL for r in results):
        verdict = "fail"
    elif any(r.status == UNKNOWN for r in results):
        verdict = "incomplete"
    else:
        verdict = "pass"
    return Report(verdict, results, list(manifest.get("lesson_unknowns", [])))


def load_fixture(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FixtureError("fixture file not found: %s" % path) from None
    except json.JSONDecodeError as exc:
        raise FixtureError("fixture is not valid JSON (%s). Fix the file and re-run." % exc) from None


# ---------------------------------------------------------------- output

def format_report(report: Report) -> str:
    lines = ["verdict: %s" % report.verdict.upper()]
    for r in report.results:
        if r.status == SKIPPED:
            lines.append("  [SKIPPED] %s: %s" % (r.field, r.detail))
        else:
            lines.append("  [%s] %s: expected %s, actual %s"
                         % (r.status.upper(), r.field, _expected_text(r), _fmt(r.actual)))
        lines.append("         lesson requirement: %s" % " | ".join('"%s"' % q for q in r.quotes))
    if report.mismatched_fields():
        lines.append("mismatched: " + ", ".join(report.mismatched_fields()))
    if report.unknown_fields():
        lines.append("unknown (not guessed): " + ", ".join(report.unknown_fields()))
    if report.not_checked:
        lines.append("not checked (the lesson gives no requirement): " + "; ".join(report.not_checked))
    return "\n".join(lines)


# ---------------------------------------------------------------- applied questions

def summarise(report: Report) -> Dict[str, Any]:
    return {"verdict": report.verdict, "mismatched": report.mismatched_fields(),
            "unknown": report.unknown_fields(), "statuses": report.statuses()}


def validate_questions(data: Any) -> List[Dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list) or not data["questions"]:
        raise ManifestError("questions file must be an object with a non-empty 'questions' list")
    for q in data["questions"]:
        where = "question %r" % (q.get("id") if isinstance(q, dict) else q)
        if not isinstance(q, dict):
            raise ManifestError("each question must be an object")
        for key in ("id", "kind", "prompt", "rationale", "fixture", "answer"):
            if key not in q:
                raise ManifestError("%s is missing '%s'" % (where, key))
        if q["kind"] not in QUESTION_KINDS:
            raise ManifestError("%s has unknown kind %r (allowed: %s)"
                                % (where, q["kind"], ", ".join(QUESTION_KINDS)))
        if not isinstance(q["rationale"], str) or not q["rationale"].strip():
            raise ManifestError("%s needs a rationale" % where)
        if q["kind"] == "diagnose_failure" and not ("fix" in q and "after_fix" in q):
            raise ManifestError("%s needs 'fix' and 'after_fix'" % where)
        if q["kind"] == "boundary_policy" and not ("field" in q and isinstance(q.get("cases"), list) and q["cases"]):
            raise ManifestError("%s needs 'field' and a non-empty 'cases' list" % where)
    return data["questions"]


def load_questions(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestError("questions file not found: %s" % path) from None
    except json.JSONDecodeError as exc:
        raise ManifestError("questions file is not valid JSON: %s" % exc) from None
    return validate_questions(data)


def _compare(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    for key in ("verdict", "mismatched", "unknown"):
        if key in expected and expected[key] != actual[key]:
            problems.append("%s: the answer says %r but the checker gives %r" % (key, expected[key], actual[key]))
    for name, status in expected.get("statuses", {}).items():
        if actual["statuses"].get(name) != status:
            problems.append("status of %s: the answer says %r but the checker gives %r"
                            % (name, status, actual["statuses"].get(name)))
    return problems


def check_question(q: Dict[str, Any], manifest: Dict[str, Any], base_dir: Path) -> Tuple[bool, str]:
    """Run the checker to confirm one worked answer. Returns (confirmed, message)."""
    fixture = load_fixture(base_dir / q["fixture"])
    problems: List[str] = []
    if q["kind"] in ("predict_output", "diagnose_failure"):
        summary = summarise(check_platform(fixture, manifest))
        problems += _compare(q["answer"], summary)
        message = "checker gives verdict %r, mismatched %r, unknown %r" % (
            summary["verdict"], summary["mismatched"], summary["unknown"])
        if q["kind"] == "diagnose_failure":
            fixed = dict(fixture)
            fixed.update(q["fix"])
            after = check_platform(fixed, manifest).verdict
            if after != q["after_fix"]:
                problems.append("after applying the fix %r the checker gives %r, not %r"
                                % (q["fix"], after, q["after_fix"]))
            message += "; after the fix %r the verdict is %r" % (q["fix"], after)
    else:  # boundary_policy
        parts = []
        for case in q["cases"]:
            data = dict(fixture)
            data[q["field"]] = case["value"]
            try:
                accepted = check_platform(data, manifest).verdict == "pass"
            except FixtureError as exc:
                problems.append("%s=%r is invalid: %s" % (q["field"], case["value"], exc))
                continue
            parts.append("%s=%s" % (case["value"], "accepted" if accepted else "rejected"))
            if accepted != case["accepted"]:
                problems.append("%s=%r: the answer says %s but the checker %s it" % (
                    q["field"], case["value"], "accepted" if case["accepted"] else "rejected",
                    "accepts" if accepted else "rejects"))
        message = "checker: " + ", ".join(parts)
    return (not problems), ("; ".join(problems) if problems else message)


def check_answers(questions: Sequence[Dict[str, Any]], manifest: Dict[str, Any],
                  base_dir: Path = HERE) -> List[Tuple[str, bool, str]]:
    outcomes = []
    for q in questions:
        try:
            ok, message = check_question(q, manifest, base_dir)
        except FixtureError as exc:
            ok, message = False, "fixture problem: %s" % exc
        outcomes.append((q["id"], ok, message))
    return outcomes


def run_questions(manifest: Dict[str, Any], questions_path: Path = DEFAULT_QUESTIONS) -> int:
    questions = load_questions(questions_path)
    outcomes = check_answers(questions, manifest, Path(questions_path).resolve().parent)
    confirmed = 0
    for q, (_, ok, message) in zip(questions, outcomes):
        print("== %s (%s)" % (q["id"], q["kind"]))
        print("prompt: %s" % q["prompt"])
        print("answer: %s" % json.dumps(q["answer"], sort_keys=True))
        print("rationale: %s" % q["rationale"])
        print("executable check: %s - %s" % ("CONFIRMED" if ok else "NOT CONFIRMED", message))
        confirmed += ok
    print("questions confirmed: %d/%d" % (confirmed, len(questions)))
    return EXIT_PASS if confirmed == len(questions) else EXIT_FAIL


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("fixture", nargs="?", type=Path, help="fixture JSON to check")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lesson", type=Path, default=DEFAULT_LESSON)
    parser.add_argument("--questions", action="store_true",
                        help="print the three applied questions and confirm each answer by running the checker")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        print(lesson_status(manifest, args.lesson))
        if args.questions:
            return run_questions(manifest)
        if args.fixture is None:
            print("INVALID INPUT: give a fixture file or --questions", file=sys.stderr)
            return EXIT_INVALID
        report = check_platform(load_fixture(args.fixture), manifest)
    except (ManifestError, FixtureError) as exc:
        print("INVALID INPUT: %s" % exc, file=sys.stderr)
        return EXIT_INVALID
    print(format_report(report))
    return VERDICT_EXIT[report.verdict]


if __name__ == "__main__":
    sys.exit(main())
