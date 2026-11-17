"""
Unit tests for R04-T018 Typed Tool Dispatch: Failure and Recovery.
"""

import unittest

from example import ToolDispatcher, run_failure_and_recovery_session


class TestFailureAndRecovery(unittest.TestCase):
    def test_documented_failure_and_recovery_sequence(self):
        """Exercises invalid/missing data case, verifies error, and demonstrates recovery on next valid input."""
        dispatcher = ToolDispatcher()

        # 1. Normal valid call
        res1 = dispatcher.dispatch({"tool": "add", "parameters": {"a": 2, "b": 3}})
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["result"], 5)

        # 2. Documented failure: string argument 'a'
        res2 = dispatcher.dispatch({"tool": "add", "parameters": {"a": "2", "b": 3}})
        self.assertEqual(res2["status"], "error")
        self.assertEqual(res2["error"]["code"], "INVALID_ARGUMENTS")
        self.assertIn("must be numeric", res2["error"]["message"])

        # 3. Documented failure: missing parameter 'b'
        res3 = dispatcher.dispatch({"tool": "multiply", "parameters": {"a": 4}})
        self.assertEqual(res3["status"], "error")
        self.assertEqual(res3["error"]["code"], "INVALID_ARGUMENTS")
        self.assertIn("Missing required parameter", res3["error"]["message"])

        # 4. Immediate recovery on next valid call: multiply(2, 3) -> 6
        res4 = dispatcher.dispatch({"tool": "multiply", "parameters": {"a": 2, "b": 3}})
        self.assertEqual(res4["status"], "success")
        self.assertEqual(res4["result"], 6)

    def test_run_failure_and_recovery_summary(self):
        summary = run_failure_and_recovery_session()
        self.assertTrue(summary["step1_success"])
        self.assertEqual(summary["step2_error_code"], "INVALID_ARGUMENTS")
        self.assertEqual(summary["step3_error_code"], "INVALID_ARGUMENTS")
        self.assertTrue(summary["step4_recovered"])


class TestValidationAndIsolation(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ToolDispatcher()

    def test_unknown_tool_fails_with_structured_error(self):
        res = self.dispatcher.dispatch({"tool": "cube", "parameters": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "UNKNOWN_TOOL")

    def test_failed_call_cannot_execute_another_tool(self):
        """Calling unknown tool or failing validation does not execute add or multiply."""
        res = self.dispatcher.dispatch({"tool": "power", "parameters": {"a": 2, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertNotIn("result", res)

    def test_boolean_rejection(self):
        res = self.dispatcher.dispatch({"tool": "add", "parameters": {"a": False, "b": 5}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_stateful_dispatcher_stuck_in_error_fails(self):
        """A dispatcher that locks up or remains poisoned after an error must fail recovery test."""
        class PoisonedDispatcher:
            def __init__(self):
                self.has_error = False

            def dispatch(self, payload):
                if self.has_error:
                    return {"status": "error", "error": {"code": "STUCK_IN_ERROR"}}
                if payload.get("parameters", {}).get("a") == "invalid":
                    self.has_error = True
                    return {"status": "error", "error": {"code": "INVALID_ARGUMENTS"}}
                return {"status": "success", "result": 10}

        d = PoisonedDispatcher()
        d.dispatch({"parameters": {"a": "invalid"}})
        # Recovery call fails on poisoned dispatcher
        recovered = d.dispatch({"parameters": {"a": 1, "b": 2}})
        with self.assertRaises(AssertionError):
            self.assertEqual(recovered["status"], "success")

    def test_flawed_calculation_fails(self):
        flawed_result = 7  # Deliberate bug
        with self.assertRaises(AssertionError):
            self.assertEqual(flawed_result, 6)


if __name__ == "__main__":
    unittest.main()
