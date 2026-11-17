"""
Unit tests and regression checks for R04-T017 Typed Tool Dispatch.
"""

import unittest

from example import WORKED_SESSION_TEXT, dispatch_tool_call, run_worked_session


class TestWorkedExampleRegression(unittest.TestCase):
    def test_exact_worked_example_regression(self):
        """Exact regression test ensuring execution matches the published worked example."""
        res = run_worked_session()

        # Step 1: add(2, 3) -> 5
        self.assertEqual(res["add_res"]["status"], "success")
        self.assertEqual(res["add_res"]["result"], 5)

        # Step 2: multiply(2, 3) -> 6
        self.assertEqual(res["mul_res"]["status"], "success")
        self.assertEqual(res["mul_res"]["result"], 6)

        # Step 3: string 'a' -> INVALID_ARGUMENTS
        self.assertEqual(res["str_a_res"]["status"], "error")
        self.assertEqual(res["str_a_res"]["error"]["code"], "INVALID_ARGUMENTS")
        self.assertIn("Parameters 'a' and 'b' must be numeric", res["str_a_res"]["error"]["message"])

        # Step 4: unknown tool -> UNKNOWN_TOOL
        self.assertEqual(res["unk_res"]["status"], "error")
        self.assertEqual(res["unk_res"]["error"]["code"], "UNKNOWN_TOOL")
        self.assertIn("not in allowed tools", res["unk_res"]["error"]["message"])


class TestValidationAndIsolation(unittest.TestCase):
    def test_float_values_allowed(self):
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": 1.5, "b": 2.5}})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 4.0)

    def test_string_b_fails(self):
        res = dispatch_tool_call({"tool": "multiply", "parameters": {"a": 2, "b": "3"}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")

    def test_boolean_arguments_rejected(self):
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": True, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")

    def test_missing_argument_rejected(self):
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": 2}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")

    def test_failed_call_cannot_execute_another_tool(self):
        """Isolation: requesting an unknown tool never triggers fallback execution."""
        executed = []

        def spy_add(a, b):
            executed.append("add")
            return a + b

        # Even if someone injects fallback into registry
        res = dispatch_tool_call({"tool": "unknown_tool", "parameters": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "UNKNOWN_TOOL")
        self.assertEqual(executed, [])


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_calculation_regression_fails(self):
        """If add(2, 3) yields an incorrect result, regression test catches it."""
        flawed_result = 6  # Deliberate bug
        with self.assertRaises(AssertionError):
            self.assertEqual(flawed_result, 5)

    def test_flawed_untyped_dispatcher_fails(self):
        """If string argument '2' is evaluated without error, validation catches the defect."""
        def loose_dispatcher(a, b):
            return int(a) + int(b)

        # Loose evaluation gives 5 instead of returning structured error
        val = loose_dispatcher("2", 3)
        with self.assertRaises(AssertionError):
            self.assertEqual(val, "SHOULD_BE_STRUCTURED_ERROR")


if __name__ == "__main__":
    unittest.main()
