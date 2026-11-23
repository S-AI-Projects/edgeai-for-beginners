"""
Unit tests for Refactored Typed Tool Dispatch and Baseline Equivalence.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import (
    baseline_dispatch_single,
    baseline_dispatch_pipeline,
    ModularToolDispatcher,
    SchemaValidator,
)


class TestRefactoredToolDispatch(unittest.TestCase):

    def setUp(self):
        self.dispatcher = ModularToolDispatcher()

    def test_add_and_multiply_contracts(self):
        """Verify add(2,3) -> 5 and multiply(2,3) -> 6."""
        res_add = self.dispatcher.dispatch_single({"tool": "add", "args": {"a": 2, "b": 3}})
        self.assertEqual(res_add["status"], "success")
        self.assertEqual(res_add["result"], 5)

        res_mult = self.dispatcher.dispatch_single({"tool": "multiply", "args": {"a": 2, "b": 3}})
        self.assertEqual(res_mult["status"], "success")
        self.assertEqual(res_mult["result"], 6)

    def test_unknown_tool_and_string_arg_errors(self):
        """Unknown tool and string a produce structured errors."""
        res_unk = self.dispatcher.dispatch_single({"tool": "divide", "args": {"a": 4, "b": 2}})
        self.assertEqual(res_unk["status"], "error")
        self.assertEqual(res_unk["error"]["code"], "UNKNOWN_TOOL")

        res_str = self.dispatcher.dispatch_single({"tool": "add", "args": {"a": "2", "b": 3}})
        self.assertEqual(res_str["status"], "error")
        self.assertEqual(res_str["error"]["code"], "INVALID_ARGUMENT_TYPE")

    def test_pipeline_stops_on_failure(self):
        """Pipeline halts on error so failed call cannot execute another tool."""
        pipeline = [
            {"tool": "add", "args": {"a": 2, "b": 3}},
            {"tool": "add", "args": {"a": "str", "b": 3}},
            {"tool": "multiply", "args": {"a": 2, "b": 3}},
        ]
        results = self.dispatcher.dispatch_pipeline(pipeline)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[1]["status"], "error")

    def test_baseline_and_refactored_equivalence(self):
        """Prove before/after equivalence across positive, negative, and edge fixtures."""
        test_cases = [
            {"tool": "add", "args": {"a": 2, "b": 3}},
            {"tool": "multiply", "args": {"a": 2, "b": 3}},
            {"tool": "unknown_tool", "args": {"a": 1, "b": 2}},
            {"tool": "add", "args": {"a": "2", "b": 3}},
            {"tool": "multiply", "args": {"a": 2, "b": False}},
            {"tool": "add", "args": {"a": 0, "b": -5}},
        ]
        for tc in test_cases:
            base_out = baseline_dispatch_single(tc)
            refac_out = self.dispatcher.dispatch_single(tc)
            self.assertEqual(base_out["status"], refac_out["status"])
            if base_out["status"] == "success":
                self.assertEqual(base_out["result"], refac_out["result"])
            else:
                self.assertEqual(base_out["error"]["code"], refac_out["error"]["code"])

    def test_deliberate_wrong_result_fails(self):
        """Assertion fails when result is intentionally wrong."""
        res = self.dispatcher.dispatch_single({"tool": "add", "args": {"a": 2, "b": 3}})
        self.assertNotEqual(res["result"], 10)


if __name__ == "__main__":
    unittest.main()
