"""
Unit tests for Typed Tool Dispatch.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import dispatch_single_call, dispatch_tool_pipeline, TOOL_ALLOWLIST


class TestTypedToolDispatch(unittest.TestCase):

    def test_valid_invocations(self):
        """Test add(2,3) -> 5 and multiply(2,3) -> 6."""
        res_add = dispatch_single_call({"tool": "add", "args": {"a": 2, "b": 3}})
        self.assertEqual(res_add["status"], "success")
        self.assertEqual(res_add["result"], 5)

        res_mult = dispatch_single_call({"tool": "multiply", "args": {"a": 2, "b": 3}})
        self.assertEqual(res_mult["status"], "success")
        self.assertEqual(res_mult["result"], 6)

    def test_smallest_valid_and_boundary_cases(self):
        """Boundary values: zeros, negative numbers, floats."""
        zero_res = dispatch_single_call({"tool": "add", "args": {"a": 0, "b": 0}})
        self.assertEqual(zero_res["result"], 0)

        float_res = dispatch_single_call({"tool": "multiply", "args": {"a": 0.5, "b": 4.0}})
        self.assertEqual(float_res["result"], 2.0)

    def test_structured_error_unknown_tool(self):
        """Rejection of un-allowlisted tool produces structured error."""
        res = dispatch_single_call({"tool": "divide", "args": {"a": 10, "b": 2}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "UNKNOWN_TOOL")
        self.assertEqual(res["error"]["tool"], "divide")

    def test_structured_error_string_argument(self):
        """Non-numeric string parameter produces structured error."""
        res = dispatch_single_call({"tool": "add", "args": {"a": "2", "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT_TYPE")
        self.assertEqual(res["error"]["details"]["parameter"], "a")
        self.assertEqual(res["error"]["details"]["received_type"], "str")

    def test_boolean_argument_rejection(self):
        """Booleans should not pass as numbers despite being int subclasses."""
        res = dispatch_single_call({"tool": "add", "args": {"a": True, "b": 3}})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT_TYPE")

    def test_pipeline_halt_on_error(self):
        """A failed call halts execution and prevents subsequent tools from executing."""
        calls = [
            {"tool": "add", "args": {"a": 2, "b": 3}},
            {"tool": "add", "args": {"a": "invalid", "b": 3}},
            {"tool": "multiply", "args": {"a": 2, "b": 3}},  # Must not run
        ]
        results = dispatch_tool_pipeline(calls)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["result"], 5)
        self.assertEqual(results[1]["status"], "error")
        # Ensure the 3rd tool was not dispatched
        self.assertTrue(all(r.get("tool") != "multiply" for r in results))

    def test_deliberate_wrong_result_fails(self):
        """Verification that wrong calculation or bypass will fail assertions."""
        res = dispatch_single_call({"tool": "add", "args": {"a": 2, "b": 3}})
        self.assertNotEqual(res["result"], 999)


if __name__ == "__main__":
    unittest.main()
