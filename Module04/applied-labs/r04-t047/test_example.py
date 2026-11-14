"""Tests for R04-T047. Run from the repository root:

    python3 -m unittest discover -s Module04/applied-labs/r04-t047 -p "test_*.py"
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
GOOD = json.loads((HERE / "fixtures" / "ok_macos14_arm_mlx.json").read_text())


def good(**changes):
    data = copy.deepcopy(GOOD)
    for key, value in changes.items():
        if value is example.UNKNOWN:  # sentinel: drop the key
            data.pop(key, None)
        else:
            data[key] = value
    return data


def run_cli(*args):
    """Fresh process, so nothing is shared with the test runner."""
    return subprocess.run([sys.executable, str(EXAMPLE_PY)] + [str(a) for a in args],
                          capture_output=True, text=True, cwd=str(HERE))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = example.load_manifest(example.DEFAULT_MANIFEST)

    def test_manifest_covers_os_architecture_backend_with_quotes(self):
        fields = [r["field"] for r in self.manifest["requirements"]]
        for needed in ("os_name", "os_version", "architecture", "backend"):
            self.assertIn(needed, fields)
        for req in self.manifest["requirements"]:
            self.assertTrue(req["lesson_quotes"], req["field"])

    def test_invalid_manifests_are_rejected_with_a_reason(self):
        bad = {"requirements": [{"field": "x", "kind": "bogus", "expected": "a", "lesson_quotes": ["q"]}]}
        with self.assertRaisesRegex(example.ManifestError, "unknown kind"):
            example.validate_manifest(bad)
        bad = {"requirements": [{"field": "x", "kind": "equals", "expected": "a", "lesson_quotes": []}]}
        with self.assertRaisesRegex(example.ManifestError, "lesson_quotes"):
            example.validate_manifest(bad)
        with self.assertRaisesRegex(example.ManifestError, "non-empty"):
            example.validate_manifest({"requirements": []})

    def test_quotes_found_in_synthetic_lesson_even_with_bold_markers(self):
        lesson = "- **macOS 13.0+** (for Apple Silicon optimization)\n" + "\n".join(
            q for q in example.all_quotes(self.manifest) if not q.startswith("macOS"))
        self.assertEqual(example.missing_quotes(self.manifest, lesson), [])

    def test_lesson_drift_is_detected(self):
        lesson = "- macOS 14.0+ (for Apple Silicon optimization)"
        missing = example.missing_quotes(self.manifest, lesson)
        self.assertIn("macOS 13.0+ (for Apple Silicon optimization)", missing)

    def test_lesson_drift_raises_from_lesson_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            lesson = Path(tmp) / "lesson.md"
            lesson.write_text("nothing relevant", encoding="utf-8")
            with self.assertRaisesRegex(example.ManifestError, "out of date"):
                example.lesson_status(self.manifest, lesson)

    def test_missing_lesson_file_is_reported_as_unverified(self):
        message = example.lesson_status(self.manifest, HERE / "no-such-lesson.md")
        self.assertIn("NOT verified", message)

    @unittest.skipUnless(example.DEFAULT_LESSON.is_file(), "lesson not present in this checkout")
    def test_manifest_quotes_exist_in_the_real_lesson(self):
        text = example.DEFAULT_LESSON.read_text(encoding="utf-8")
        self.assertEqual(example.missing_quotes(self.manifest, text), [])


class PassTests(unittest.TestCase):
    def setUp(self):
        self.manifest = example.load_manifest(example.DEFAULT_MANIFEST)

    def check(self, data):
        return example.check_platform(data, self.manifest)

    def test_matching_fixture_passes(self):
        report = self.check(good())
        self.assertEqual(report.verdict, "pass")
        self.assertEqual(report.mismatched_fields(), [])
        self.assertEqual(report.unknown_fields(), [])
        self.assertEqual(report.warnings, [])

    def test_exact_minimums_pass_with_ram_advisory(self):
        data = json.loads((HERE / "fixtures" / "ok_boundary_minimums.json").read_text())
        report = self.check(data)
        self.assertEqual(report.verdict, "pass")
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("recommended 16", report.warnings[0])

    def test_versions_compare_numerically_not_as_text(self):
        self.assertEqual(self.check(good(python_version="3.10")).verdict, "pass")  # "3.10" < "3.8" as text
        self.assertEqual(self.check(good(os_version="13")).verdict, "pass")        # 13 == 13.0
        self.assertEqual(self.check(good(os_version="26.1.2")).verdict, "pass")

    def test_extra_fields_are_ignored(self):
        self.assertEqual(self.check(good(chip="M3")).verdict, "pass")


class FailTests(unittest.TestCase):
    def setUp(self):
        self.manifest = example.load_manifest(example.DEFAULT_MANIFEST)

    def check(self, data):
        return example.check_platform(data, self.manifest)

    def test_changed_architecture_fails_and_names_the_field(self):
        data = json.loads((HERE / "fixtures" / "rosetta_architecture_i386.json").read_text())
        report = self.check(data)
        self.assertEqual(report.verdict, "fail")
        self.assertEqual(report.mismatched_fields(), ["architecture"])
        arch = [r for r in report.results if r.field == "architecture"][0]
        self.assertEqual((arch.expected, arch.actual), ("arm", "i386"))
        self.assertIn("expected 'arm', got 'i386'", arch.detail)

    def test_each_mismatch_is_reported_on_its_own_field(self):
        cases = [
            ({"os_name": "Linux"}, "os_name"),
            ({"os_version": "12.7"}, "os_version"),
            ({"python_version": "3.7"}, "python_version"),
            ({"backend": "cuda"}, "backend"),
            ({"ram_gb": 7.5}, "ram_gb"),
        ]
        for change, field_name in cases:
            with self.subTest(field=field_name):
                report = self.check(good(**change))
                self.assertEqual(report.verdict, "fail")
                self.assertEqual(report.mismatched_fields(), [field_name])

    def test_several_mismatches_are_all_listed(self):
        report = self.check(good(architecture="i386", os_version="12.0"))
        self.assertEqual(report.mismatched_fields(), ["os_version", "architecture"])


class MissingCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.manifest = example.load_manifest(example.DEFAULT_MANIFEST)

    def test_missing_backend_is_reported_not_guessed(self):
        data = json.loads((HERE / "fixtures" / "missing_backend.json").read_text())
        report = example.check_platform(data, self.manifest)
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(report.unknown_fields(), ["backend"])
        self.assertEqual(report.mismatched_fields(), [])
        backend = [r for r in report.results if r.field == "backend"][0]
        self.assertEqual(backend.status, example.UNKNOWN)
        self.assertIsNone(backend.actual)

    def test_null_counts_as_not_reported(self):
        report = example.check_platform(good(backend=None), self.manifest)
        self.assertEqual(report.unknown_fields(), ["backend"])

    def test_a_mismatch_still_wins_over_unknown_but_both_are_listed(self):
        report = example.check_platform(good(architecture="i386", backend=example.UNKNOWN), self.manifest)
        self.assertEqual(report.verdict, "fail")
        self.assertEqual(report.mismatched_fields(), ["architecture"])
        self.assertEqual(report.unknown_fields(), ["backend"])

    def test_empty_fixture_is_all_unknown(self):
        report = example.check_platform({}, self.manifest)
        self.assertEqual(report.verdict, "incomplete")
        self.assertEqual(len(report.unknown_fields()), len(self.manifest["requirements"]))


class InvalidInputTests(unittest.TestCase):
    def setUp(self):
        self.manifest = example.load_manifest(example.DEFAULT_MANIFEST)

    def test_non_numeric_ram_is_rejected_with_an_explanation(self):
        with self.assertRaisesRegex(example.FixtureError, r"ram_gb must be a non-negative number.*'lots'"):
            example.check_platform(good(ram_gb="lots"), self.manifest)

    def test_boolean_and_negative_ram_are_rejected(self):
        for bad in (True, -4):
            with self.subTest(value=bad):
                with self.assertRaises(example.FixtureError):
                    example.check_platform(good(ram_gb=bad), self.manifest)

    def test_numeric_version_is_rejected_because_3_10_would_become_3_1(self):
        with self.assertRaisesRegex(example.FixtureError, "version string"):
            example.check_platform(good(python_version=3.10), self.manifest)

    def test_malformed_version_text_is_rejected(self):
        with self.assertRaisesRegex(example.FixtureError, "digits separated by dots"):
            example.check_platform(good(os_version="13.x"), self.manifest)

    def test_non_object_fixture_is_rejected(self):
        with self.assertRaisesRegex(example.FixtureError, "JSON object"):
            example.check_platform(["macOS"], self.manifest)

    def test_broken_json_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(example.FixtureError, "not valid JSON"):
                example.load_fixture(path)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = example.load_manifest(example.DEFAULT_MANIFEST)

    def test_batch_continues_after_an_invalid_input_and_recovers(self):
        outcomes = example.run_batch(
            [("first", good()), ("bad", good(ram_gb="lots")), ("next", good())], self.manifest)
        self.assertEqual([o[0] for o in outcomes], ["first", "bad", "next"])
        self.assertEqual(outcomes[0][1].verdict, "pass")
        self.assertIsNone(outcomes[1][1])
        self.assertIn("ram_gb", outcomes[1][2])
        self.assertEqual(outcomes[2][1].verdict, "pass")

    def test_checker_keeps_no_state_between_inputs(self):
        before = example.check_platform(good(), self.manifest)
        with self.assertRaises(example.FixtureError):
            example.check_platform(good(ram_gb="lots"), self.manifest)
        after = example.check_platform(good(), self.manifest)
        self.assertEqual(before, after)

    def test_demo_sequence_ends_in_a_pass_after_an_invalid_input(self):
        result = run_cli("--demo")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("INVALID INPUT: ram_gb must be", result.stdout)
        self.assertIn("summary: pass=2 fail=1 incomplete=1 invalid=1", result.stdout)
        self.assertIn("recovery: last input passed after the invalid one", result.stdout)


class CliExitCodeTests(unittest.TestCase):
    """Each scenario runs in a fresh process and must exit non-zero when it should."""

    def run_fixture(self, name):
        return run_cli(HERE / "fixtures" / name)

    def test_exit_codes(self):
        expected = {
            "ok_macos14_arm_mlx.json": 0,
            "ok_boundary_minimums.json": 0,
            "rosetta_architecture_i386.json": 1,
            "missing_backend.json": 2,
            "invalid_ram_gb.json": 3,
        }
        for name, code in expected.items():
            with self.subTest(fixture=name):
                result = self.run_fixture(name)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def test_failure_output_names_field_and_lesson_requirement(self):
        result = self.run_fixture("rosetta_architecture_i386.json")
        self.assertIn("[FAIL] architecture: expected 'arm', actual 'i386'", result.stdout)
        self.assertIn("Native ARM environment (not running under Rosetta)", result.stdout)
        self.assertIn("mismatched: architecture", result.stdout)

    def test_missing_fixture_file_is_invalid_input(self):
        result = run_cli(HERE / "fixtures" / "nope.json")
        self.assertEqual(result.returncode, 3)
        self.assertIn("fixture file not found", result.stderr)

    def test_no_arguments_is_invalid_input(self):
        self.assertEqual(run_cli().returncode, 3)


class HardwareIndependenceTests(unittest.TestCase):
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
        manifest = example.load_manifest(example.DEFAULT_MANIFEST)
        import platform
        with mock.patch.object(platform, "machine", side_effect=AssertionError("host probed")), \
                mock.patch.object(platform, "system", side_effect=AssertionError("host probed")), \
                mock.patch.object(platform, "processor", side_effect=AssertionError("host probed")):
            self.assertEqual(example.check_platform(good(), manifest).verdict, "pass")
            self.assertEqual(example.check_platform(good(architecture="i386"), manifest).verdict, "fail")


if __name__ == "__main__":
    unittest.main()
