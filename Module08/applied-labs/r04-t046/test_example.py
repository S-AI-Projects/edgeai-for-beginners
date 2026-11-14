import contextlib
import copy
import io
import os
import socket
import subprocess
import unittest
from unittest import mock

from example import (BROKEN_CONFIG, BROKEN_PATH, COMPLETE_CONFIG, COMPLETE_PATH, DEMO_KEY, SPEC,
                     ConfigRequirement, ExecutableRequirement, FakeProbe, Spec, SpecError,
                     SystemProbe, check_environment, is_secret, main, render_report,
                     render_worked_examples, worked_example_a, worked_example_b)

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as handle:
        return handle.read()


def run(path=COMPLETE_PATH, config=COMPLETE_CONFIG, spec=SPEC):
    return check_environment(spec, FakeProbe(path), config)


class NormalCases(unittest.TestCase):
    def test_complete_fixture_passes(self):
        report = run()
        self.assertTrue(report.passed)
        self.assertEqual(report.failures, ())
        self.assertEqual(len(report.checks), 6)
        self.assertIn("RESULT: PASSED - 6 of 6 checks ok", render_report(report))

    def test_non_secret_values_are_shown_and_secret_values_are_not(self):
        text = render_report(run())
        self.assertIn("MODEL: set (value: phi-4-mini)", text)
        self.assertIn("API_KEY: set (value hidden)", text)

    def test_checks_follow_the_listed_order(self):
        names = [(c.kind, c.name) for c in run().checks]
        self.assertEqual(names, [("executable", "foundry"), ("executable", "python"),
                                 ("executable", "pip"), ("config", "MODEL"),
                                 ("config", "BASE_URL"), ("config", "API_KEY")])

    def test_output_is_deterministic(self):
        self.assertEqual(render_worked_examples(), render_worked_examples())


class SeparateActionableFailures(unittest.TestCase):
    def test_missing_executable_is_one_separate_failure(self):
        report = run(path=("foundry", "python"))
        self.assertEqual([(c.name, c.status) for c in report.failures], [("pip", "MISSING_EXECUTABLE")])
        self.assertIn("install pip for your Python, then re-run", report.failures[0].message)

    def test_absent_config_field_is_one_separate_failure(self):
        config = {k: v for k, v in COMPLETE_CONFIG.items() if k != "BASE_URL"}
        report = run(config=config)
        self.assertEqual([(c.name, c.status) for c in report.failures], [("BASE_URL", "ABSENT_CONFIG")])
        self.assertIn("set BASE_URL to your Foundry Local address", report.failures[0].message)

    def test_both_problems_are_reported_separately_with_different_statuses(self):
        report = run(path=BROKEN_PATH, config=BROKEN_CONFIG)
        statuses = {c.name: c.status for c in report.failures}
        self.assertEqual(statuses, {"pip": "MISSING_EXECUTABLE", "BASE_URL": "ABSENT_CONFIG"})
        self.assertIn("RESULT: FAILED - 2 of 6 checks need attention", render_report(report))

    def test_every_missing_executable_gets_its_own_line(self):
        report = run(path=())
        self.assertEqual([c.name for c in report.failures], ["foundry", "python", "pip"])

    def test_none_counts_as_absent(self):
        report = run(config={**COMPLETE_CONFIG, "MODEL": None})
        self.assertEqual([(c.name, c.status) for c in report.failures], [("MODEL", "ABSENT_CONFIG")])

    def test_blank_values_are_a_distinct_failure(self):
        for blank in ("", "   "):
            with self.subTest(blank=repr(blank)):
                report = run(config={**COMPLETE_CONFIG, "BASE_URL": blank})
                self.assertEqual([(c.name, c.status) for c in report.failures], [("BASE_URL", "EMPTY_CONFIG")])
                self.assertIn("set but empty", report.failures[0].message)


class SecretsAreNeverPrinted(unittest.TestCase):
    def test_secret_value_is_absent_from_every_output_form(self):
        for label, path, config in (("complete", COMPLETE_PATH, COMPLETE_CONFIG),
                                    ("broken", BROKEN_PATH, BROKEN_CONFIG)):
            with self.subTest(case=label):
                report = run(path, config)
                everything = render_report(report) + repr(report) + " ".join(c.message for c in report.checks)
                self.assertNotIn(DEMO_KEY, everything)

    def test_worked_examples_never_print_the_key(self):
        self.assertNotIn(DEMO_KEY, render_worked_examples())

    def test_secret_is_hidden_even_when_other_checks_fail(self):
        text = render_report(run(path=(), config={"API_KEY": "sk-LEAK-ME", "MODEL": "m"}))
        self.assertNotIn("sk-LEAK-ME", text)

    def test_unflagged_names_with_key_token_secret_or_password_are_hidden_too(self):
        for name in ("API_KEY", "access_token", "CLIENT_SECRET", "DbPassword"):
            with self.subTest(name=name):
                spec = Spec(config=(ConfigRequirement(name, "set it"),))
                self.assertTrue(is_secret(spec.config[0]))
                text = render_report(check_environment(spec, FakeProbe(()), {name: "TOP-SECRET-VALUE"}))
                self.assertNotIn("TOP-SECRET-VALUE", text)
                self.assertIn("(value hidden)", text)

    def test_ordinary_names_are_not_treated_as_secret(self):
        self.assertFalse(is_secret(ConfigRequirement("MODEL", "x")))
        self.assertFalse(is_secret(ConfigRequirement("BASE_URL", "x")))


class ReadOnlyAndOffline(unittest.TestCase):
    def test_inputs_are_not_modified(self):
        config, path = copy.deepcopy(BROKEN_CONFIG), list(BROKEN_PATH)
        check_environment(SPEC, FakeProbe(path), config)
        self.assertEqual((config, path), (BROKEN_CONFIG, list(BROKEN_PATH)))

    def test_no_network_and_no_subprocess_are_used(self):
        boom = AssertionError("the preflight must not touch the network or start processes")
        with mock.patch.object(socket, "socket", side_effect=boom), \
             mock.patch.object(subprocess, "Popen", side_effect=boom), \
             mock.patch.object(os, "system", side_effect=boom):
            self.assertTrue(worked_example_a())
            self.assertTrue(worked_example_b())

    def test_system_probe_only_looks_up_the_path(self):
        self.assertFalse(SystemProbe().which("definitely-not-installed-r04-t046"))


class SpecAndConfigValidation(unittest.TestCase):
    def assertSpecError(self, code, **kwargs):
        with self.assertRaises(SpecError) as ctx:
            check_environment(kwargs.get("spec", SPEC), FakeProbe(()), kwargs.get("config", {}))
        self.assertEqual(ctx.exception.code, code)

    def test_empty_spec_is_rejected(self):
        self.assertSpecError("EMPTY_SPEC", spec=Spec())

    def test_duplicate_requirement_is_rejected(self):
        spec = Spec(executables=(ExecutableRequirement("pip", "a"), ExecutableRequirement("pip", "b")))
        self.assertSpecError("DUPLICATE_REQUIREMENT", spec=spec)

    def test_blank_requirement_name_is_rejected(self):
        self.assertSpecError("BAD_REQUIREMENT", spec=Spec(config=(ConfigRequirement("  ", "x"),)))

    def test_config_must_be_a_mapping_of_text(self):
        self.assertSpecError("BAD_CONFIG", config=["MODEL"])
        self.assertSpecError("BAD_CONFIG", config={"MODEL": 5})

    def test_same_name_may_be_both_an_executable_and_a_config_field(self):
        spec = Spec(executables=(ExecutableRequirement("python", "x"),),
                    config=(ConfigRequirement("python", "x"),))
        self.assertEqual(len(check_environment(spec, FakeProbe(("python",)), {"python": "3"}).checks), 2)


class RegressionOfTheWorkedExamples(unittest.TestCase):
    """The exact published example is executed: code, worked_example.txt and README must agree."""

    def test_output_equals_worked_example_file(self):
        self.assertEqual(render_worked_examples(), read("worked_example.txt"))

    def test_readme_contains_both_exact_outputs(self):
        readme = read("README.md")
        self.assertIn("```\n" + worked_example_a() + "\n```", readme)
        self.assertIn("```\n" + worked_example_b() + "\n```", readme)

    def test_demo_prints_exactly_the_worked_examples(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            main()
        self.assertEqual(buffer.getvalue(), read("worked_example.txt"))

    def test_the_two_published_examples_have_the_stated_results(self):
        self.assertIn("RESULT: PASSED - 6 of 6 checks ok", worked_example_a())
        self.assertIn("[FAIL] executable pip: not found on PATH -> install pip for your Python, then re-run",
                      worked_example_b())
        self.assertIn("[FAIL] config BASE_URL: not set -> set BASE_URL to your Foundry Local address",
                      worked_example_b())
        self.assertIn("RESULT: FAILED - 2 of 6 checks need attention", worked_example_b())


if __name__ == "__main__":
    unittest.main()
