#!/usr/bin/env python3
"""R04-T049: manifest-driven platform-compatibility preflight (evaluation experiment).

Requirements come from manifest.json, whose entries quote the lesson
Module02/06.phisilica.md. The checker compares a *fixture* (a small JSON
description of a setup) with that manifest. It never inspects the computer it
runs on, so results are identical on any machine.

Outcomes
  pass        every field matches
  fail        at least one reported field mismatches (the field is named)
  incomplete  nothing mismatches, but a field was not reported; it is listed
              as unknown and is never guessed
  invalid     the fixture or manifest is malformed (an explained error)

Exit codes: 0 pass, 1 fail, 2 incomplete, 3 invalid input.

Evaluation experiment (--evaluate): three ways of treating a missing field are
compared on a controlled corpus of generated fixtures whose true answer is known:
  report       the contract: a missing field is reported as unknown
  assume_pass  guess that every missing field matches
  assume_fail  guess that every missing field mismatches
The corpus is synthetic. It measures decisions, not model accuracy, speed or power.
Exit code 0 when the contract policy makes no wrong decision, 1 otherwise.

Standard library only; written to run on Python 3.7+.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "manifest.json"
DEFAULT_LESSON = HERE.parent.parent / "06.phisilica.md"

PASS, FAIL, UNKNOWN = "pass", "fail", "unknown"
EXIT_PASS, EXIT_FAIL, EXIT_INCOMPLETE, EXIT_INVALID = 0, 1, 2, 3
VERDICT_EXIT = {"pass": EXIT_PASS, "fail": EXIT_FAIL, "incomplete": EXIT_INCOMPLETE}
KINDS = ("one_of", "flag")
STATES = ("correct", "wrong", "missing_correct", "missing_wrong")
POLICIES = ("report", "assume_pass", "assume_fail")


class ManifestError(ValueError):
    """The manifest or the lesson it quotes is unusable."""


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


def _fmt(value: Any) -> str:
    if value is None:
        return "<not reported>"
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value)


def _expected_text(result: FieldResult) -> str:
    if result.kind == "one_of":
        return "one of " + ", ".join(repr(e) for e in result.expected)
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
        seen.append(req["field"])
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
        elif not isinstance(req["expected"], bool):
            raise ManifestError("%s.expected must be true or false for kind 'flag'" % where)
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


def format_report(report: Report) -> str:
    lines = ["verdict: %s" % report.verdict.upper()]
    for r in report.results:
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


# ---------------------------------------------------------------- evaluation experiment

def decide(report: Report, policy: str) -> str:
    """Turn a report into a verdict under one of three ways of treating missing fields."""
    if policy == "report":
        return report.verdict
    if policy == "assume_pass":
        return "fail" if report.mismatched_fields() else "pass"
    if policy == "assume_fail":
        return "pass" if all(r.status == PASS for r in report.results) else "fail"
    raise ValueError("unknown policy %r (allowed: %s)" % (policy, ", ".join(POLICIES)))


def evaluation_values(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Per field, a test value that matches the lesson and one that does not (verified here)."""
    values: Dict[str, Dict[str, Any]] = {}
    for req in manifest["requirements"]:
        ev = req.get("evaluation")
        if not isinstance(ev, dict) or "correct" not in ev or "wrong" not in ev:
            raise ManifestError("requirement %r needs an 'evaluation' object with 'correct' and "
                                "'wrong' test values" % req["field"])
        for label, want in (("correct", PASS), ("wrong", FAIL)):
            try:
                report = check_platform({req["field"]: ev[label]}, manifest)
            except FixtureError as exc:
                raise ManifestError("evaluation %s value for %r is invalid: %s" % (label, req["field"], exc)) from None
            got = [r.status for r in report.results if r.field == req["field"]][0]
            if got != want:
                raise ManifestError("evaluation %s value for %r gives status %r, expected %r"
                                    % (label, req["field"], got, want))
        values[req["field"]] = ev
    return values


def build_corpus(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every combination of field states: 4 states per field, so 4 ** fields fixtures.

    correct / wrong: the field is reported with a matching / non-matching value.
    missing_correct / missing_wrong: the field is left out; the hidden truth is that it
    would have matched / not matched. A setup is truly compatible when no field is wrong.
    """
    values = evaluation_values(manifest)
    names = [r["field"] for r in manifest["requirements"]]
    corpus: List[Dict[str, Any]] = []
    for states in itertools.product(STATES, repeat=len(names)):
        fixture: Dict[str, Any] = {}
        for name, state in zip(names, states):
            if state == "correct":
                fixture[name] = values[name]["correct"]
            elif state == "wrong":
                fixture[name] = values[name]["wrong"]
        corpus.append({
            "states": dict(zip(names, states)),
            "fixture": fixture,
            "compatible": all(s in ("correct", "missing_correct") for s in states),
        })
    return corpus


def evaluate(manifest: Dict[str, Any], corpus: Optional[List[Dict[str, Any]]] = None
             ) -> Dict[str, Dict[str, Any]]:
    """Score each policy against the known truth of every corpus fixture."""
    if corpus is None:
        corpus = build_corpus(manifest)
    reports = [check_platform(item["fixture"], manifest) for item in corpus]
    results: Dict[str, Dict[str, Any]] = {}
    for policy in POLICIES:
        row = {"total": len(corpus), "decided": 0, "undecided": 0, "correct": 0,
               "false_pass": 0, "false_fail": 0}
        for item, report in zip(corpus, reports):
            verdict = decide(report, policy)
            if verdict == "incomplete":
                row["undecided"] += 1
                continue
            row["decided"] += 1
            if (verdict == "pass") == item["compatible"]:
                row["correct"] += 1
            elif verdict == "pass":
                row["false_pass"] += 1
            else:
                row["false_fail"] += 1
        row["coverage"] = row["decided"] / row["total"]
        wrong = row["false_pass"] + row["false_fail"]
        row["error_rate"] = wrong / row["decided"] if row["decided"] else 0.0
        results[policy] = row
    return results


def format_evaluation(results: Dict[str, Dict[str, Any]], corpus: List[Dict[str, Any]]) -> str:
    layout = "%-12s %8s %10s %8s %11s %11s %9s %11s"
    lines = [
        "corpus: %d generated fixtures (%d fields x 4 states: correct, wrong, missing-but-correct, "
        "missing-but-wrong); %d are truly compatible"
        % (len(corpus), len(corpus[0]["states"]), sum(1 for c in corpus if c["compatible"])),
        layout % ("policy", "decided", "undecided", "correct", "false_pass", "false_fail",
                  "coverage", "error_rate"),
    ]
    for policy in POLICIES:
        r = results[policy]
        lines.append(layout % (policy, r["decided"], r["undecided"], r["correct"], r["false_pass"],
                               r["false_fail"], "%.1f%%" % (100 * r["coverage"]),
                               "%.1f%%" % (100 * r["error_rate"])))
    rep, ap, af = results["report"], results["assume_pass"], results["assume_fail"]
    lines.append("trade-off: reporting missing fields as unknown makes %d wrong decisions and leaves %d "
                 "undecided; guessing decides all %d but makes %d false passes (assume_pass) or %d false "
                 "fails (assume_fail)"
                 % (rep["false_pass"] + rep["false_fail"], rep["undecided"], ap["total"],
                    ap["false_pass"], af["false_fail"]))
    lines.append("scope: counts over generated fixtures only; no model accuracy, speed or power is measured")
    return "\n".join(lines)


def run_evaluation(manifest: Dict[str, Any]) -> int:
    corpus = build_corpus(manifest)
    results = evaluate(manifest, corpus)
    print(format_evaluation(results, corpus))
    contract = results["report"]
    wrong = contract["false_pass"] + contract["false_fail"]
    print("check: the contract policy (report) made %d wrong decision(s): %s"
          % (wrong, "OK" if wrong == 0 else "FAILED"))
    return EXIT_PASS if wrong == 0 else EXIT_FAIL


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("fixture", nargs="?", type=Path, help="fixture JSON to check")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lesson", type=Path, default=DEFAULT_LESSON)
    parser.add_argument("--evaluate", action="store_true",
                        help="compare the three missing-field policies on the generated corpus")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        print(lesson_status(manifest, args.lesson))
        if args.evaluate:
            return run_evaluation(manifest)
        if args.fixture is None:
            print("INVALID INPUT: give a fixture file or --evaluate", file=sys.stderr)
            return EXIT_INVALID
        report = check_platform(load_fixture(args.fixture), manifest)
    except (ManifestError, FixtureError) as exc:
        print("INVALID INPUT: %s" % exc, file=sys.stderr)
        return EXIT_INVALID
    print(format_report(report))
    return VERDICT_EXIT[report.verdict]


if __name__ == "__main__":
    sys.exit(main())
