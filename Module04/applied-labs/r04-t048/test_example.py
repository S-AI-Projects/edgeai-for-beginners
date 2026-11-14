"""Tests for R04-T048. Run from the repository root:

    python3 -m unittest discover -s Module04/applied-labs/r04-t048 -p "test_*.py"
"""
import ast
import copy
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


GOOD = fixture("ok_linux_x86_64_htp.json")


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
        for needed in ("os_name", "architecture", "backend", "python_version"):
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
            (req(kind="min_version", expected=3.7), "version string"),
            (req(when={"field": "later", "equals": "a"}), "earlier field"),
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
        lesson = "- Python 3.9 or higher\n- Linux or Windows development environment"
        missing = example.missing_quotes(self.manifest, lesson)
        self.assertIn("Python 3.7 or higher", missing)

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
        for name in ("ok_linux_x86_64_htp.json", "ok_windows_x86_64_cpu.json", "ok_android_with_ndk.json"):
            with self.subTest(fixture=name):
                report = self.check(fixture(name))
                self.assertEqual(report.verdict, "pass")
                self.assertEqual(report.mismatched_fields(), [])
                self.assertEqual(report.unknown_fields(), [])

    def test_every_listed_backend_and_os_is_accepted(self):
        for backend in ("htp", "gpu", "cpu"):
            self.assertEqual(self.check(good(backend=backend)).verdict, "pass", backend)
        for os_name in ("Linux", "Windows"):
            self.assertEqual(self.check(good(os_name=os_name)).verdict, "pass", os_name)

    def test_python_boundary_is_inclusive_and_numeric(self):
        for version in ("3.7", "3.7.0", "3.8", "3.10", "4"):
            with self.subTest(version=version):
                self.assertEqual(self.check(good(python_version=version)).verdict, "pass")
        self.assertEqual(self.check(fixture("boundary_python_3_7.json")).verdict, "pass")

    def test_ndk_is_skipped_when_target_is_not_android(self):
        report = self.check(fixture("ndk_not_needed.json"))
        self.assertEqual(report.verdict, "pass")
        self.assertEqual(report.statuses()["android_ndk"], example.SKIPPED)

    def test_ndk_is_required_for_android_target(self):
        report = self.check(fixture("ok_android_with_ndk.json"))
        self.assertEqual(report.statuses()["android_ndk"], example.PASS)

    def test_extra_fields_are_ignored(self):
        self.assertEqual(self.check(good(chip="Snapdragon", ram_gb=4)).verdict, "pass")


class FailTests(Base):
    def test_changed_architecture_fails_and_names_the_field(self):
        report = self.check(fixture("armv7_android_target.json"))
        self.assertEqual(report.verdict, "fail")
        self.assertEqual(report.mismatched_fields(), ["architecture"])
        arch = [r for r in report.results if r.field == "architecture"][0]
        self.assertEqual(arch.actual, "armv7-android")
        self.assertIn("expected one of 'x86_64-linux-clang', 'aarch64-android', got 'armv7-android'", arch.detail)

    def test_each_mismatch_is_reported_on_its_own_field(self):
        cases = [
            ({"os_name": "macOS"}, "os_name"),
            ({"python_version": "3.6.15"}, "python_version"),
            ({"python_version": "3.6"}, "python_version"),
            ({"architecture": "i686-linux-clang"}, "architecture"),
            ({"backend": "npu"}, "backend"),
            ({"qnn_sdk": False}, "qnn_sdk"),
        ]
        for change, field_name in cases:
            with self.subTest(field=field_name, change=change):
                report = self.check(good(**change))
                self.assertEqual(report.verdict, "fail")
                self.assertEqual(report.mismatched_fields(), [field_name])

    def test_android_target_without_ndk_flag_true_fails(self):
        data = fixture("ok_android_with_ndk.json")
        data["android_ndk"] = False
        report = self.check(data)
        self.assertEqual(report.mismatched_fields(), ["android_ndk"])

    def test_several_mismatches_are_all_listed_in_manifest_order(self):
        report = self.check(good(os_name="macOS", architecture="armv7-android"))
        self.assertEqual(report.mismatched_fields(), ["os_name", "architecture"])


class MissingCapabilityTests(Base):
    def test_missing_backend_is_reported_not_guessed(self):
        report = self.check(fixture("missing_backend.json"))
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(report.unknown_fields(), ["backend"])
        self.assertEqual(report.mismatched_fields(), [])

    def test_missing_ndk_on_android_target_is_unknown_not_pass_or_fail(self):
        report = self.check(fixture("missing_android_ndk.json"))
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(report.unknown_fields(), ["android_ndk"])

    def test_missing_architecture_also_leaves_the_ndk_question_open(self):
        report = self.check(good(architecture=DROP))
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(report.unknown_fields(), ["architecture", "android_ndk"])

    def test_null_counts_as_not_reported(self):
        self.assertEqual(self.check(good(backend=None)).unknown_fields(), ["backend"])

    def test_a_mismatch_wins_over_unknown_but_both_are_listed(self):
        report = self.check(good(os_name="macOS", backend=DROP))
        self.assertEqual(report.verdict, "fail")
        self.assertEqual(report.mismatched_fields(), ["os_name"])
        self.assertEqual(report.unknown_fields(), ["backend"])

    def test_empty_fixture_is_all_unknown(self):
        report = self.check({})
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(len(report.unknown_fields()), len(self.manifest["requirements"]))

    def test_lesson_unknowns_are_listed_not_checked(self):
        report = self.check(good())
        self.assertEqual(report.not_checked, self.manifest["lesson_unknowns"])
        text = example.format_report(report)
        self.assertIn("not checked (the lesson gives no requirement)", text)
        self.assertIn("minimum operating system version", text)


class InvalidInputTests(Base):
    def test_text_for_a_true_false_field_is_rejected_with_an_explanation(self):
        with self.assertRaisesRegex(example.FixtureError, r"qnn_sdk must be true or false.*'yes'"):
            self.check(fixture("invalid_sdk_flag.json"))

    def test_numeric_version_is_rejected_because_3_10_would_become_3_1(self):
        with self.assertRaisesRegex(example.FixtureError, "version string"):
            self.check(good(python_version=3.10))

    def test_malformed_version_text_is_rejected(self):
        with self.assertRaisesRegex(example.FixtureError, "digits separated by dots"):
            self.check(good(python_version="3.x"))

    def test_non_string_choice_is_rejected(self):
        with self.assertRaisesRegex(example.FixtureError, "os_name must be a string"):
            self.check(good(os_name=5))

    def test_non_object_fixture_is_rejected(self):
        with self.assertRaisesRegex(example.FixtureError, "JSON object"):
            self.check(["Linux"])

    def test_broken_json_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(example.FixtureError, "not valid JSON"):
                example.load_fixture(path)


class AppliedQuestionTests(Base):
    def setUp(self):
        super().setUp()
        self.questions = example.load_questions(example.DEFAULT_QUESTIONS)

    def test_three_questions_of_the_required_kinds_each_with_a_rationale(self):
        self.assertEqual([q["kind"] for q in self.questions],
                         ["predict_output", "diagnose_failure", "boundary_policy"])
        for q in self.questions:
            self.assertTrue(q["rationale"].strip(), q["id"])

    def test_every_worked_answer_is_confirmed_by_running_the_checker(self):
        for qid, ok, message in example.check_answers(self.questions, self.manifest, HERE):
            with self.subTest(question=qid):
                self.assertTrue(ok, message)

    def test_a_wrong_prediction_is_not_confirmed(self):
        wrong = copy.deepcopy(self.questions)
        wrong[0]["answer"]["verdict"] = "fail"
        outcomes = example.check_answers(wrong, self.manifest, HERE)
        self.assertFalse(outcomes[0][1])
        self.assertIn("verdict", outcomes[0][2])

    def test_a_wrong_status_in_the_answer_is_not_confirmed(self):
        wrong = copy.deepcopy(self.questions)
        wrong[0]["answer"]["statuses"]["android_ndk"] = "fail"
        self.assertFalse(example.check_answers(wrong, self.manifest, HERE)[0][1])

    def test_a_wrong_diagnosis_is_not_confirmed(self):
        wrong = copy.deepcopy(self.questions)
        wrong[1]["answer"]["mismatched"] = ["backend"]
        self.assertFalse(example.check_answers(wrong, self.manifest, HERE)[1][1])

    def test_a_fix_that_does_not_work_is_not_confirmed(self):
        wrong = copy.deepcopy(self.questions)
        wrong[1]["fix"] = {"architecture": "armv7-android"}
        outcomes = example.check_answers(wrong, self.manifest, HERE)
        self.assertFalse(outcomes[1][1])
        self.assertIn("after applying the fix", outcomes[1][2])

    def test_a_wrong_boundary_answer_is_not_confirmed(self):
        for case_index in range(len(self.questions[2]["cases"])):
            with self.subTest(case=self.questions[2]["cases"][case_index]["value"]):
                wrong = copy.deepcopy(self.questions)
                case = wrong[2]["cases"][case_index]
                case["accepted"] = not case["accepted"]
                self.assertFalse(example.check_answers(wrong, self.manifest, HERE)[2][1])

    def test_invalid_questions_files_are_rejected(self):
        with self.assertRaisesRegex(example.ManifestError, "non-empty"):
            example.validate_questions({"questions": []})
        bad = {"questions": [{"id": "Q", "kind": "bogus", "prompt": "p", "rationale": "r",
                              "fixture": "f", "answer": {}}]}
        with self.assertRaisesRegex(example.ManifestError, "unknown kind"):
            example.validate_questions(bad)
        bad["questions"][0]["kind"] = "predict_output"
        bad["questions"][0]["rationale"] = " "
        with self.assertRaisesRegex(example.ManifestError, "rationale"):
            example.validate_questions(bad)

    def test_questions_command_succeeds_in_a_fresh_process(self):
        result = run_cli("--questions")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("questions confirmed: 3/3", result.stdout)
        self.assertEqual(result.stdout.count("executable check: CONFIRMED"), 3)


class CliExitCodeTests(unittest.TestCase):
    """Each scenario runs in a fresh process and must exit non-zero when it should."""

    def test_exit_codes(self):
        expected = {
            "ok_linux_x86_64_htp.json": 0,
            "ok_windows_x86_64_cpu.json": 0,
            "ok_android_with_ndk.json": 0,
            "boundary_python_3_7.json": 0,
            "ndk_not_needed.json": 0,
            "armv7_android_target.json": 1,
            "missing_backend.json": 2,
            "missing_android_ndk.json": 2,
            "invalid_sdk_flag.json": 3,
        }
        for name, code in expected.items():
            with self.subTest(fixture=name):
                result = run_cli(HERE / "fixtures" / name)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def test_failure_output_names_field_and_lesson_requirement(self):
        result = run_cli(HERE / "fixtures" / "armv7_android_target.json")
        self.assertIn("[FAIL] architecture: expected one of 'x86_64-linux-clang', 'aarch64-android', "
                      "actual 'armv7-android'", result.stdout)
        self.assertIn('"-t x86_64-linux-clang" | "-t aarch64-android"', result.stdout)
        self.assertIn("mismatched: architecture", result.stdout)

    def test_missing_capability_output_says_not_guessed(self):
        result = run_cli(HERE / "fixtures" / "missing_android_ndk.json")
        self.assertIn("[UNKNOWN] android_ndk: expected true, actual <not reported>", result.stdout)
        self.assertIn("unknown (not guessed): android_ndk", result.stdout)

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
        for forbidden in ("platform", "subprocess", "socket", "urllib", "http", "ctypes", "os"):
            self.assertNotIn(forbidden, imported)

    def test_result_does_not_change_when_host_probes_are_poisoned(self):
        import platform
        with mock.patch.object(platform, "machine", side_effect=AssertionError("host probed")), \
                mock.patch.object(platform, "system", side_effect=AssertionError("host probed")), \
                mock.patch.object(platform, "processor", side_effect=AssertionError("host probed")):
            self.assertEqual(self.check(good()).verdict, "pass")
            self.assertEqual(self.check(good(architecture="armv7-android")).verdict, "fail")


if __name__ == "__main__":
    unittest.main()
