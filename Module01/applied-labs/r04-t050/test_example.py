import contextlib
import copy
import io
import json
import os
import platform
import unittest
from unittest import mock

from example import (CASES, CHANGED_ARCHITECTURE, JUST_BELOW, MISSING_NPU, NAN_NPU, SMALLEST_VALID,
                     TEXT_NPU, ZERO_NPU, ManifestError, ObservationError, PlatformChecker, fmt,
                     load_manifest, main, render_report, run_session, validate_manifest)

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = load_manifest(os.path.join(HERE, "manifest.json"))


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as handle:
        return handle.read()


def check(observed=SMALLEST_VALID, manifest=MANIFEST):
    return PlatformChecker(manifest).check(observed)


def status(report):
    return {r.rule_id: r.status for r in report.results}


def with_tops(value):
    return {**SMALLEST_VALID, "npu_tops": value}


class RecordedLessonRequirements(unittest.TestCase):
    def test_manifest_records_the_lesson_file_and_pinned_commit(self):
        self.assertEqual(MANIFEST["lesson"]["file"], "Module01/04.EdgeDeployment.md")
        self.assertEqual(MANIFEST["lesson"]["commit"], "e88f123a4bb5796594919db3a13257c429d1288c")

    def test_the_exact_requirement_values_from_the_lesson(self):
        rules = {r["id"]: r for r in MANIFEST["rules"]}
        self.assertEqual(rules["os_name"]["expected"], "Windows")
        self.assertEqual((rules["architecture"]["field"], rules["architecture"]["expected"]),
                         ("cpu_family", "Qualcomm Oryon"))
        self.assertEqual((rules["npu_tops"]["minimum"], rules["npu_tops"]["lesson_figure"]), (45, "45+"))
        self.assertEqual(rules["backend"]["expected"], "DirectML")

    def test_every_rule_records_where_in_the_lesson_it_comes_from(self):
        for rule in MANIFEST["rules"]:
            self.assertTrue(rule["lesson_section"] and rule["lesson_says"], rule["id"])

    def test_the_boundary_decision_is_recorded_and_explained(self):
        rule = next(r for r in MANIFEST["rules"] if r["id"] == "npu_tops")
        self.assertIs(rule["inclusive"], True)
        for part in ("45+", "45 or more", "inclusive", "no rounding"):
            self.assertIn(part, rule["boundary_note"])

    def test_explicit_unknowns_are_listed(self):
        text = " ".join(MANIFEST["unknowns"])
        for part in ("Windows version", "instruction-set", "45 TOPS"):
            self.assertIn(part, text)


class SmallestValidCase(unittest.TestCase):
    def test_only_the_four_required_fields_pass(self):
        self.assertEqual(set(SMALLEST_VALID), {"os_name", "cpu_family", "npu_tops", "backend"})
        report = check()
        self.assertTrue(report.passed)
        self.assertIn("RESULT: PASSED - 4 of 4 checks ok", render_report(report))

    def test_extra_fields_are_ignored(self):
        self.assertTrue(check({**SMALLEST_VALID, "ram_gb": 16, "note": "anything"}).passed)

    def test_the_boundary_pass_says_so(self):
        message = next(r for r in check().results if r.rule_id == "npu_tops").message
        self.assertIn("exactly on the boundary, which passes", message)

    def test_above_the_boundary_has_no_boundary_note(self):
        message = next(r for r in check(with_tops(46)).results if r.rule_id == "npu_tops").message
        self.assertNotIn("boundary", message)


class BoundaryCases(unittest.TestCase):
    def test_the_npu_boundary_matrix(self):
        for value, expected in ((45, "OK"), (45.0, "OK"), (45.0000001, "OK"), (46, "OK"), (1e9, "OK"),
                                (44.9999999, "MISMATCH"), (44.99999999999999, "MISMATCH"),
                                (44.9, "MISMATCH"), (1, "MISMATCH"), (0, "MISMATCH"), (-0.0, "MISMATCH")):
            with self.subTest(npu_tops=value):
                self.assertEqual(status(check(with_tops(value)))["npu_tops"], expected)

    def test_zero_is_a_valid_observation_not_invalid_input(self):
        report = check(ZERO_NPU)
        self.assertEqual([(r.rule_id, r.status) for r in report.failures], [("npu_tops", "MISMATCH")])

    def test_int_and_float_forms_of_45_agree(self):
        self.assertEqual(check(with_tops(45)), check(with_tops(45.0)))
        self.assertTrue(check(with_tops(45)).passed)

    def test_the_failure_explains_the_exact_boundary_decision(self):
        message = check(JUST_BELOW).failures[0].message
        for part in ("'npu_tops'", "observed 44.9", "required >= 45", "45 or more (inclusive)",
                     "exactly 45 passes", "no rounding or tolerance"):
            self.assertIn(part, message)

    def test_a_near_miss_is_shown_exactly_not_rounded_to_45(self):
        message = check(with_tops(44.99999999999999)).failures[0].message
        self.assertIn("observed 44.99999999999999", message)
        self.assertEqual((fmt(45.0), fmt(45), fmt(44.9)), ("45", "45", "44.9"))

    def test_the_boundary_decision_lives_in_the_manifest_flip_it_and_45_fails(self):
        manifest = copy.deepcopy(MANIFEST)
        next(r for r in manifest["rules"] if r["id"] == "npu_tops")["inclusive"] = False
        self.assertEqual(status(check(with_tops(45), manifest))["npu_tops"], "MISMATCH")
        self.assertIn("required > 45", check(with_tops(45), manifest).failures[0].message)
        self.assertEqual(status(check(with_tops(45.01), manifest))["npu_tops"], "OK")

    def test_text_fields_are_compared_exactly(self):
        for field, value in (("os_name", "windows"), ("os_name", " Windows "), ("backend", "directml"),
                             ("backend", "DirectML 1.0"), ("cpu_family", "qualcomm oryon")):
            with self.subTest(field=field, value=value):
                self.assertEqual(len(check({**SMALLEST_VALID, field: value}).failures), 1)

    def test_blank_text_counts_as_missing_not_as_a_mismatch(self):
        for blank in ("", "   "):
            with self.subTest(blank=repr(blank)):
                report = check({**SMALLEST_VALID, "backend": blank})
                self.assertEqual([(r.rule_id, r.status) for r in report.failures], [("backend", "MISSING_DATA")])


class ChangedArchitecture(unittest.TestCase):
    def test_changed_architecture_fails_and_names_the_mismatched_field(self):
        report = check(CHANGED_ARCHITECTURE)
        self.assertEqual([(r.rule_id, r.field, r.status) for r in report.failures],
                         [("architecture", "cpu_family", "MISMATCH")])
        message = report.failures[0].message
        for part in ("'cpu_family'", "'Intel Core Ultra'", "'Qualcomm Oryon'", "separate platforms"):
            self.assertIn(part, message)

    def test_the_other_windows_ai_pc_platforms_are_also_a_changed_architecture(self):
        for family in ("Intel Core Ultra", "AMD Ryzen AI", "Apple M3"):
            with self.subTest(cpu_family=family):
                self.assertEqual(status(check({**SMALLEST_VALID, "cpu_family": family}))["architecture"], "MISMATCH")

    def test_a_wrong_os_or_backend_fails_only_that_rule(self):
        self.assertEqual({r.rule_id for r in check({**SMALLEST_VALID, "os_name": "Linux"}).failures}, {"os_name"})
        self.assertEqual({r.rule_id for r in check({**SMALLEST_VALID, "backend": "TensorRT"}).failures}, {"backend"})


class MissingCapabilityIsReportedNotGuessed(unittest.TestCase):
    def test_missing_npu_is_missing_data_not_ok(self):
        report = check(MISSING_NPU)
        self.assertFalse(report.passed)
        self.assertEqual([(r.rule_id, r.status) for r in report.failures], [("npu_tops", "MISSING_DATA")])
        self.assertIn("not guessing", report.failures[0].message)

    def test_each_field_can_be_missing_on_its_own(self):
        for field, rule_id in (("os_name", "os_name"), ("cpu_family", "architecture"),
                               ("npu_tops", "npu_tops"), ("backend", "backend")):
            with self.subTest(missing=field):
                observed = {k: v for k, v in SMALLEST_VALID.items() if k != field}
                self.assertEqual([(r.rule_id, r.status) for r in check(observed).failures],
                                 [(rule_id, "MISSING_DATA")])

    def test_none_counts_as_missing(self):
        self.assertEqual(status(check(with_tops(None)))["npu_tops"], "MISSING_DATA")

    def test_an_empty_observation_reports_everything_as_missing(self):
        report = check({})
        self.assertEqual({r.status for r in report.results}, {"MISSING_DATA"})
        self.assertEqual(len(report.failures), 4)


class InvalidInputIsRejectedWithAnExplanation(unittest.TestCase):
    def assertInvalid(self, observed, code):
        with self.assertRaises(ObservationError) as ctx:
            check(observed)
        self.assertEqual(ctx.exception.code, code)
        self.assertTrue(ctx.exception.message)

    def test_not_a_mapping(self):
        for bad in (None, [], "Windows", 45):
            with self.subTest(bad=bad):
                self.assertInvalid(bad, "NOT_A_MAPPING")

    def test_text_numbers_are_never_converted(self):
        self.assertInvalid(TEXT_NPU, "BAD_TYPE")
        self.assertInvalid(with_tops("45.0"), "BAD_TYPE")

    def test_booleans_are_not_numbers(self):
        self.assertInvalid(with_tops(True), "BAD_TYPE")
        self.assertInvalid(with_tops(False), "BAD_TYPE")

    def test_nan_infinity_and_negatives_are_invalid(self):
        for bad in (float("nan"), float("inf"), float("-inf"), -1, -0.5):
            with self.subTest(bad=bad):
                self.assertInvalid(with_tops(bad), "BAD_VALUE")
        self.assertInvalid(NAN_NPU, "BAD_VALUE")

    def test_non_text_for_a_text_field(self):
        self.assertInvalid({**SMALLEST_VALID, "os_name": 11}, "BAD_TYPE")
        self.assertInvalid({**SMALLEST_VALID, "backend": ["DirectML"]}, "BAD_TYPE")

    def test_invalid_input_gives_no_partial_report(self):
        with self.assertRaises(ObservationError):
            check({**SMALLEST_VALID, "npu_tops": "45", "cpu_family": "Intel Core Ultra"})

    def test_the_checker_is_not_left_in_a_bad_state(self):
        checker = PlatformChecker(MANIFEST)
        fresh = checker.check(SMALLEST_VALID)
        for bad in (TEXT_NPU, NAN_NPU, None):
            with self.assertRaises(ObservationError):
                checker.check(bad)
        self.assertEqual(checker.check(SMALLEST_VALID), fresh)


class IndependentOfTheRealHardware(unittest.TestCase):
    def test_the_platform_module_is_never_consulted(self):
        boom = AssertionError("the checker must not read the real machine")
        names = ("system", "machine", "processor", "win32_ver", "mac_ver", "python_version", "uname", "platform", "release")
        with contextlib.ExitStack() as stack:
            for name in names:
                if hasattr(platform, name):
                    stack.enter_context(mock.patch.object(platform, name, side_effect=boom))
            self.assertTrue(run_session(PlatformChecker(MANIFEST), CASES))

    def test_inputs_and_manifest_are_not_modified(self):
        observed, manifest = copy.deepcopy(JUST_BELOW), copy.deepcopy(MANIFEST)
        PlatformChecker(manifest).check(observed)
        self.assertEqual((observed, manifest), (JUST_BELOW, MANIFEST))

    def test_same_input_gives_the_same_output(self):
        self.assertEqual(run_session(PlatformChecker(MANIFEST), CASES), run_session(PlatformChecker(MANIFEST), CASES))


class ManifestValidation(unittest.TestCase):
    def assertManifestError(self, mutate, code):
        manifest = copy.deepcopy(MANIFEST)
        mutate(manifest)
        with self.assertRaises(ManifestError) as ctx:
            validate_manifest(manifest)
        self.assertEqual(ctx.exception.code, code)

    def npu(self, manifest):
        return next(r for r in manifest["rules"] if r["id"] == "npu_tops")

    def test_empty_rules(self):
        self.assertManifestError(lambda m: m.update(rules=[]), "EMPTY_RULES")

    def test_unknown_kind(self):
        self.assertManifestError(lambda m: m["rules"][0].update(kind="telepathy"), "UNKNOWN_KIND")

    def test_duplicate_rule_id(self):
        self.assertManifestError(lambda m: m["rules"][1].update(id="os_name"), "DUPLICATE_RULE")

    def test_missing_expected_or_minimum(self):
        self.assertManifestError(lambda m: m["rules"][0].pop("expected"), "MISSING_KEY")
        self.assertManifestError(lambda m: self.npu(m).pop("minimum"), "MISSING_KEY")

    def test_the_boundary_decision_must_be_explicit_and_explained(self):
        self.assertManifestError(lambda m: self.npu(m).pop("inclusive"), "BAD_BOUNDARY")
        self.assertManifestError(lambda m: self.npu(m).update(inclusive="yes"), "BAD_BOUNDARY")
        self.assertManifestError(lambda m: self.npu(m).pop("boundary_note"), "BAD_BOUNDARY")

    def test_missing_lesson_commit(self):
        self.assertManifestError(lambda m: m["lesson"].pop("commit"), "MISSING_KEY")

    def test_manifest_file_is_plain_json(self):
        self.assertEqual(json.loads(read("manifest.json")), MANIFEST)


class RegressionOfTheWorkedExample(unittest.TestCase):
    """The exact published session is executed: code, worked_example.txt and README must agree."""

    def test_session_output_equals_worked_example_file(self):
        self.assertEqual(run_session(PlatformChecker(MANIFEST), CASES), read("worked_example.txt"))

    def test_readme_contains_the_exact_session_output(self):
        self.assertIn("```\n" + read("worked_example.txt").rstrip("\n") + "\n```", read("README.md"))

    def test_demo_prints_exactly_the_worked_example(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            main()
        self.assertEqual(buffer.getvalue(), read("worked_example.txt"))

    def test_the_seven_cases_have_the_stated_outcomes(self):
        blocks = read("worked_example.txt").strip().split("\n\n")
        outcomes = ["PASSED" if "RESULT: PASSED" in b else "INVALID" if "INVALID INPUT" in b else "FAILED" for b in blocks]
        self.assertEqual(outcomes, ["PASSED", "FAILED", "FAILED", "FAILED", "FAILED", "INVALID", "INVALID"])

    def test_the_published_boundary_and_invalid_lines(self):
        text = read("worked_example.txt")
        self.assertIn("npu_tops: 45 (required: >= 45) - exactly on the boundary, which passes", text)
        self.assertIn("observed 44.9, required >= 45", text)
        self.assertIn("MISSING_DATA: field 'npu_tops' was not reported; not guessing", text)
        self.assertIn("INVALID INPUT (BAD_TYPE): 'npu_tops' must be a number, got str", text)


if __name__ == "__main__":
    unittest.main()
