"""Tests for R04-T049. Run from the repository root:

    python3 -m unittest discover -s Module02/applied-labs/r04-t049 -p "test_*.py"
"""
import ast
import contextlib
import copy
import io
import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import example

HERE = Path(__file__).resolve().parent
EXAMPLE_PY = HERE / "example.py"
DROP = object()  # sentinel: remove the key from the fixture


def fixture(name):
    return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))


GOOD = fixture("ok_windows11_npu.json")


def good(**changes):
    data = copy.deepcopy(GOOD)
    for key, value in changes.items():
        if value is DROP:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def run_cli(*args):
    """Fresh process, so nothing is shared with the test runner."""
    return subprocess.run([sys.executable, str(EXAMPLE_PY)] + [str(a) for a in args],
                          capture_output=True, text=True, cwd=str(HERE))


class Base(unittest.TestCase):
    def setUp(self):
        self.manifest = example.load_manifest(example.DEFAULT_MANIFEST)

    def check(self, data):
        return example.check_platform(data, self.manifest)


class ManifestTests(Base):
    def test_manifest_covers_os_architecture_backend_with_quotes(self):
        fields = [r["field"] for r in self.manifest["requirements"]]
        for needed in ("os_name", "architecture", "backend"):
            self.assertIn(needed, fields)
        for req in self.manifest["requirements"]:
            self.assertTrue(req["lesson_quotes"], req["field"])

    def test_explicit_unknowns_are_recorded(self):
        self.assertTrue(self.manifest["lesson_unknowns"])

    def test_invalid_manifests_are_rejected_with_a_reason(self):
        def req(**kw):
            base = {"field": "x", "kind": "one_of", "expected": ["a"], "lesson_quotes": ["q"]}
            base.update(kw)
            return {"requirements": [base]}
        cases = [
            (req(kind="bogus"), "unknown kind"),
            (req(lesson_quotes=[]), "lesson_quotes"),
            (req(expected=[]), "non-empty list"),
            (req(kind="flag", expected="yes"), "true or false"),
            ({"requirements": []}, "non-empty"),
        ]
        for manifest, pattern in cases:
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(example.ManifestError, pattern):
                    example.validate_manifest(manifest)

    def test_quotes_found_in_synthetic_lesson_even_with_bold_markers(self):
        lesson = "\n".join("- **%s**" % q for q in example.all_quotes(self.manifest))
        self.assertEqual(example.missing_quotes(self.manifest, lesson), [])

    def test_lesson_drift_is_detected(self):
        missing = example.missing_quotes(self.manifest, "- NPU-First Architecture")
        self.assertIn("Windows ML Runtime", missing)

    def test_lesson_drift_raises_from_lesson_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            lesson = Path(tmp) / "lesson.md"
            lesson.write_text("nothing relevant", encoding="utf-8")
            with self.assertRaisesRegex(example.ManifestError, "out of date"):
                example.lesson_status(self.manifest, lesson)

    def test_missing_lesson_file_is_reported_as_unverified(self):
        self.assertIn("NOT verified", example.lesson_status(self.manifest, HERE / "no-such-lesson.md"))

    @unittest.skipUnless(example.DEFAULT_LESSON.is_file(), "lesson not present in this checkout")
    def test_manifest_quotes_exist_in_the_real_lesson(self):
        text = example.DEFAULT_LESSON.read_text(encoding="utf-8")
        self.assertEqual(example.missing_quotes(self.manifest, text), [])


class PassTests(Base):
    def test_matching_fixtures_pass(self):
        for name in ("ok_windows11_npu.json", "ok_directml_backend.json"):
            with self.subTest(fixture=name):
                report = self.check(fixture(name))
                self.assertEqual(report.verdict, "pass")
                self.assertEqual(report.mismatched_fields(), [])
                self.assertEqual(report.unknown_fields(), [])

    def test_both_backends_the_lesson_names_are_accepted(self):
        for backend in ("windows-ml", "directml"):
            self.assertEqual(self.check(good(backend=backend)).verdict, "pass", backend)

    def test_extra_fields_are_ignored(self):
        self.assertEqual(self.check(good(ram_gb=4, tokens_per_second=650)).verdict, "pass")


class FailTests(Base):
    def test_changed_architecture_fails_and_names_the_field(self):
        report = self.check(fixture("cpu_architecture.json"))
        self.assertEqual(report.verdict, "fail")
        self.assertEqual(report.mismatched_fields(), ["architecture"])
        arch = [r for r in report.results if r.field == "architecture"][0]
        self.assertEqual((arch.expected, arch.actual), (["npu"], "cpu"))
        self.assertIn("expected one of 'npu', got 'cpu'", arch.detail)

    def test_each_mismatch_is_reported_on_its_own_field(self):
        cases = [
            ({"os_name": "Windows 10"}, "os_name"),
            ({"architecture": "gpu"}, "architecture"),
            ({"backend": "cuda"}, "backend"),
            ({"windows_app_sdk": False}, "windows_app_sdk"),
        ]
        for change, field_name in cases:
            with self.subTest(field=field_name):
                report = self.check(good(**change))
                self.assertEqual(report.verdict, "fail")
                self.assertEqual(report.mismatched_fields(), [field_name])

    def test_wrong_os_fixture_fails(self):
        self.assertEqual(self.check(fixture("wrong_os.json")).mismatched_fields(), ["os_name"])

    def test_several_mismatches_are_all_listed_in_manifest_order(self):
        report = self.check(good(os_name="Windows 10", architecture="cpu"))
        self.assertEqual(report.mismatched_fields(), ["os_name", "architecture"])


class MissingCapabilityTests(Base):
    def test_missing_backend_is_reported_not_guessed(self):
        report = self.check(fixture("missing_backend.json"))
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(report.unknown_fields(), ["backend"])
        self.assertEqual(report.mismatched_fields(), [])
        backend = [r for r in report.results if r.field == "backend"][0]
        self.assertEqual(backend.status, example.UNKNOWN)
        self.assertIsNone(backend.actual)

    def test_each_missing_field_is_unknown(self):
        for name in ("os_name", "architecture", "backend", "windows_app_sdk"):
            with self.subTest(field=name):
                report = self.check(good(**{name: DROP}))
                self.assertEqual(report.verdict, "incomplete")
                self.assertEqual(report.unknown_fields(), [name])

    def test_null_counts_as_not_reported(self):
        self.assertEqual(self.check(good(backend=None)).unknown_fields(), ["backend"])

    def test_a_mismatch_wins_over_unknown_but_both_are_listed(self):
        report = self.check(good(architecture="cpu", backend=DROP))
        self.assertEqual(report.verdict, "fail")
        self.assertEqual(report.mismatched_fields(), ["architecture"])
        self.assertEqual(report.unknown_fields(), ["backend"])

    def test_empty_fixture_is_all_unknown(self):
        report = self.check(fixture("empty_fixture.json"))
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(len(report.unknown_fields()), len(self.manifest["requirements"]))

    def test_lesson_unknowns_are_listed_not_checked(self):
        report = self.check(good())
        self.assertEqual(report.not_checked, self.manifest["lesson_unknowns"])
        text = example.format_report(report)
        self.assertIn("not checked (the lesson gives no requirement)", text)
        self.assertIn("CPU instruction set", text)


class InvalidInputTests(Base):
    def test_text_for_a_true_false_field_is_rejected_with_an_explanation(self):
        with self.assertRaisesRegex(example.FixtureError, r"windows_app_sdk must be true or false.*'yes'"):
            self.check(fixture("invalid_sdk_flag.json"))

    def test_non_string_choice_is_rejected(self):
        with self.assertRaisesRegex(example.FixtureError, "os_name must be a string"):
            self.check(good(os_name=11))

    def test_non_object_fixture_is_rejected(self):
        with self.assertRaisesRegex(example.FixtureError, "JSON object"):
            self.check(["Windows 11"])

    def test_broken_json_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(example.FixtureError, "not valid JSON"):
                example.load_fixture(path)


class EvaluationTests(Base):
    """The corpus is the full product of 4 states over 4 fields, so every count below can be
    derived by hand and does not depend on the code under test.

    states per field: correct, wrong, missing_correct, missing_wrong
      corpus                      4**4 = 256
      truly compatible            2**4 = 16   (every field correct or missing_correct)
      no field reported wrong     3**4 = 81   -> 175 fixtures have a reported mismatch
      ... and none missing        1           -> 1 pass, 80 incomplete
    """

    def setUp(self):
        super().setUp()
        self.corpus = example.build_corpus(self.manifest)
        self.results = example.evaluate(self.manifest, self.corpus)

    def test_corpus_size_and_truth_match_hand_derived_counts(self):
        self.assertEqual(len(self.corpus), 256)
        self.assertEqual(sum(1 for c in self.corpus if c["compatible"]), 16)
        combos = {tuple(c["states"].values()) for c in self.corpus}
        self.assertEqual(len(combos), 256)
        self.assertEqual(combos, set(itertools.product(example.STATES, repeat=4)))

    def test_missing_states_really_omit_the_field(self):
        for item in self.corpus:
            for name, state in item["states"].items():
                self.assertEqual(name in item["fixture"], state in ("correct", "wrong"))

    def test_checker_verdict_counts_match_hand_derived_counts(self):
        verdicts = [example.check_platform(c["fixture"], self.manifest).verdict for c in self.corpus]
        self.assertEqual(verdicts.count("pass"), 1)
        self.assertEqual(verdicts.count("fail"), 175)
        self.assertEqual(verdicts.count("incomplete"), 80)

    def test_report_policy_makes_no_wrong_decision_on_any_fixture(self):
        for item in self.corpus:
            verdict = example.decide(example.check_platform(item["fixture"], self.manifest), "report")
            if verdict == "pass":
                self.assertTrue(item["compatible"], item["states"])
            elif verdict == "fail":
                self.assertFalse(item["compatible"], item["states"])

    def test_report_policy_row(self):
        row = self.results["report"]
        self.assertEqual((row["decided"], row["undecided"], row["correct"]), (176, 80, 176))
        self.assertEqual((row["false_pass"], row["false_fail"]), (0, 0))
        self.assertEqual(row["error_rate"], 0.0)

    def test_assume_pass_policy_row(self):
        row = self.results["assume_pass"]
        self.assertEqual((row["decided"], row["undecided"], row["correct"]), (256, 0, 191))
        self.assertEqual((row["false_pass"], row["false_fail"]), (65, 0))

    def test_assume_fail_policy_row(self):
        row = self.results["assume_fail"]
        self.assertEqual((row["decided"], row["undecided"], row["correct"]), (256, 0, 241))
        self.assertEqual((row["false_pass"], row["false_fail"]), (0, 15))

    def test_observed_trade_off(self):
        rep, ap, af = (self.results[p] for p in example.POLICIES)
        self.assertLess(rep["coverage"], ap["coverage"])
        self.assertEqual(ap["coverage"], 1.0)
        self.assertEqual(af["coverage"], 1.0)
        self.assertGreater(ap["false_pass"], 0)
        self.assertGreater(af["false_fail"], 0)
        self.assertEqual(rep["false_pass"] + rep["false_fail"], 0)

    def test_every_row_adds_up(self):
        for policy, row in self.results.items():
            with self.subTest(policy=policy):
                self.assertEqual(row["decided"] + row["undecided"], row["total"])
                self.assertEqual(row["correct"] + row["false_pass"] + row["false_fail"], row["decided"])

    def test_unknown_policy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown policy"):
            example.decide(self.check(good()), "optimistic")

    def test_evaluation_values_must_behave_as_labelled(self):
        broken = copy.deepcopy(self.manifest)
        broken["requirements"][0]["evaluation"]["wrong"] = "Windows 11"  # actually matches
        with self.assertRaisesRegex(example.ManifestError, "gives status 'pass', expected 'fail'"):
            example.build_corpus(broken)
        broken = copy.deepcopy(self.manifest)
        broken["requirements"][2]["evaluation"]["correct"] = "cuda"  # actually does not match
        with self.assertRaisesRegex(example.ManifestError, "gives status 'fail', expected 'pass'"):
            example.build_corpus(broken)
        broken = copy.deepcopy(self.manifest)
        del broken["requirements"][1]["evaluation"]
        with self.assertRaisesRegex(example.ManifestError, "needs an 'evaluation' object"):
            example.build_corpus(broken)

    def test_a_guessing_contract_policy_is_caught(self):
        guess = lambda report, policy: "pass" if not report.mismatched_fields() else "fail"  # noqa: E731
        with mock.patch.object(example, "decide", side_effect=guess):
            self.assertGreater(example.evaluate(self.manifest)["report"]["false_pass"], 0)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = example.run_evaluation(self.manifest)
        self.assertEqual(code, example.EXIT_FAIL)
        self.assertIn("FAILED", out.getvalue())

    def test_report_formats_the_table_and_the_scope_line(self):
        text = example.format_evaluation(self.results, self.corpus)
        self.assertIn("256 generated fixtures", text)
        self.assertIn("16 are truly compatible", text)
        self.assertIn("no model accuracy, speed or power is measured", text)
        report_row = [l for l in text.splitlines() if l.startswith("report ")][0].split()
        self.assertEqual(report_row[1:6], ["176", "80", "176", "0", "0"])

    def test_evaluate_command_succeeds_in_a_fresh_process(self):
        result = run_cli("--evaluate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("the contract policy (report) made 0 wrong decision(s): OK", result.stdout)
        self.assertIn("65 false passes (assume_pass) or 15 false fails (assume_fail)", result.stdout)


class CliExitCodeTests(unittest.TestCase):
    """Each scenario runs in a fresh process and must exit non-zero when it should."""

    def test_exit_codes(self):
        expected = {
            "ok_windows11_npu.json": 0,
            "ok_directml_backend.json": 0,
            "cpu_architecture.json": 1,
            "wrong_os.json": 1,
            "missing_backend.json": 2,
            "empty_fixture.json": 2,
            "invalid_sdk_flag.json": 3,
        }
        for name, code in expected.items():
            with self.subTest(fixture=name):
                result = run_cli(HERE / "fixtures" / name)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def test_failure_output_names_field_and_lesson_requirement(self):
        result = run_cli(HERE / "fixtures" / "cpu_architecture.json")
        self.assertIn("[FAIL] architecture: expected one of 'npu', actual 'cpu'", result.stdout)
        self.assertIn('"NPU-First Architecture"', result.stdout)
        self.assertIn("mismatched: architecture", result.stdout)

    def test_missing_capability_output_says_not_guessed(self):
        result = run_cli(HERE / "fixtures" / "missing_backend.json")
        self.assertIn("[UNKNOWN] backend: expected one of 'windows-ml', 'directml', actual <not reported>",
                      result.stdout)
        self.assertIn("unknown (not guessed): backend", result.stdout)

    def test_missing_fixture_file_is_invalid_input(self):
        result = run_cli(HERE / "fixtures" / "nope.json")
        self.assertEqual(result.returncode, 3)
        self.assertIn("fixture file not found", result.stderr)

    def test_no_arguments_is_invalid_input(self):
        self.assertEqual(run_cli().returncode, 3)


class HardwareIndependenceTests(Base):
    def test_example_imports_nothing_that_can_probe_the_host(self):
        tree = ast.parse(EXAMPLE_PY.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        for forbidden in ("platform", "subprocess", "socket", "urllib", "http", "ctypes", "os", "time", "random"):
            self.assertNotIn(forbidden, imported)

    def test_result_does_not_change_when_host_probes_are_poisoned(self):
        import platform
        with mock.patch.object(platform, "machine", side_effect=AssertionError("host probed")), \
                mock.patch.object(platform, "system", side_effect=AssertionError("host probed")), \
                mock.patch.object(platform, "processor", side_effect=AssertionError("host probed")):
            self.assertEqual(self.check(good()).verdict, "pass")
            self.assertEqual(self.check(good(architecture="cpu")).verdict, "fail")
            self.assertEqual(example.evaluate(self.manifest)["report"]["decided"], 176)


if __name__ == "__main__":
    unittest.main()
