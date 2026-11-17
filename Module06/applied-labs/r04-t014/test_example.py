"""
Unit tests for R04-T014 Typed Tool Dispatch.
Tests normal dispatch, structured errors, state trace invariants, and deliberate bug detection.
"""

import unittest

from example import DispatchTracer, dispatch_tool_call, run_concept_example


class TestTypedToolDispatchNormal(unittest.TestCase):
    def test_add_two_and_three_yields_five(self):
        """add(2,3) -> 5"""
        call = {"tool": "add", "parameters": {"a": 2, "b": 3}}
        res = dispatch_tool_call(call)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 5)

    def test_multiply_two_and_three_yields_six(self):
        """multiply(2,3) -> 6"""
        call = {"tool": "multiply", "parameters": {"a": 2, "b": 3}}
        res = dispatch_tool_call(call)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 6)

    def test_json_string_input(self):
        json_call = '{"tool": "add", "parameters": {"a": 10, "b": 20}}'
        res = dispatch_tool_call(json_call)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 30)

    def test_run_concept_example_summary(self):
        summary = run_concept_example()
        self.assertEqual(summary["add_result"], 5)
        self.assertEqual(summary["mul_result"], 6)
        self.assertEqual(summary["str_a_code"], "INVALID_ARGUMENTS")
        self.assertEqual(summary["unk_tool_code"], "UNKNOWN_TOOL")


class TestStructuredErrorsAndIsolation(unittest.TestCase):
    def test_unknown_tool_returns_structured_error(self):
        res = dispatch_tool_call({"tool": "subtract", "parameters": {"a": 5, "b": 2}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "UNKNOWN_TOOL")

    def test_string_a_argument_returns_structured_error(self):
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": "2", "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")

    def test_string_b_argument_returns_structured_error(self):
        res = dispatch_tool_call({"tool": "multiply", "parameters": {"a": 2, "b": "3"}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")

    def test_boolean_argument_returns_structured_error(self):
        """Booleans should not be quietly coerced to integers."""
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": True, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")

    def test_missing_argument_returns_structured_error(self):
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": 2}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENTS")

    def test_malformed_json_returns_structured_error(self):
        res = dispatch_tool_call("{not valid json}")
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_JSON")


class TestStateTraceInvariants(unittest.TestCase):
    def test_successful_state_trace_invariant(self):
        """Invariant: successful call contains the complete ordered trace."""
        tracer = DispatchTracer()
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": 2, "b": 3}}, tracer)
        self.assertEqual(res["status"], "success")

        steps = tracer.get_steps()
        self.assertIn("INPUT_RECEIVED", steps)
        self.assertIn("PARSE_JSON", steps)
        self.assertIn("ALLOWLIST_CHECK", steps)
        self.assertIn("ARGUMENT_VALIDATION", steps)
        self.assertIn("DISPATCH_EXECUTION", steps)

        # Final step must be successful execution
        last_step = tracer.trace[-1]
        self.assertEqual(last_step["step"], "DISPATCH_EXECUTION")
        self.assertEqual(last_step["status"], "SUCCESS")
        self.assertEqual(last_step["context"]["result"], 5)

    def test_failed_call_halts_and_never_executes_tool(self):
        """Invariant: failed validation must halt before dispatch; no tool is executed."""
        tracer = DispatchTracer()
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": "2", "b": 3}}, tracer)
        self.assertEqual(res["status"], "error")

        steps = tracer.get_steps()
        # Execution must NEVER reach DISPATCH_EXECUTION
        self.assertNotIn("DISPATCH_EXECUTION", steps)
        last_step = tracer.trace[-1]
        self.assertEqual(last_step["step"], "ARGUMENT_VALIDATION")
        self.assertEqual(last_step["status"], "FAILED")


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_string_coercion_fails(self):
        """A dispatcher that coerces string '2' to integer 2 violates contract and fails test."""
        def flawed_dispatch_with_coercion(a, b):
            # Deliberate bug: silent type casting
            return int(a) + int(b)

        # Our strict contract rejects string '2'
        res = dispatch_tool_call({"tool": "add", "parameters": {"a": "2", "b": 3}})
        with self.assertRaises(AssertionError):
            # Expecting status success would fail
            self.assertEqual(res["status"], "success")

    def test_flawed_fallback_tool_execution_fails(self):
        """A dispatcher that falls back to another tool on unknown tool request fails isolation test."""
        def flawed_dispatch_with_fallback(tool_name, a, b):
            # Deliberate bug: falls back to add when tool is unknown
            if tool_name not in ["add", "multiply"]:
                return {"status": "success", "tool": "add", "result": a + b}
            return {"status": "success", "tool": tool_name}

        res = flawed_dispatch_with_fallback("unknown_calc", 2, 3)
        # Verify that such behavior would violate our contract
        with self.assertRaises(AssertionError):
            self.assertEqual(res["status"], "error")


if __name__ == "__main__":
    unittest.main()
