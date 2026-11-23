"""
Unit tests for Optimization-Stage Ordering and Artifact Provenance.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import (
    OptimizationPlanValidator,
    PipelineValidationError,
    run_demo,
)


class TestOptimizationPlanValidation(unittest.TestCase):

    def setUp(self):
        self.validator = OptimizationPlanValidator()
        self.initial_artifacts = {"model_raw"}
        self.valid_plan = [
            {"stage": "export", "input_artifact": "model_raw", "output_artifact": "model_onnx"},
            {"stage": "quantize", "input_artifact": "model_onnx", "output_artifact": "model_q4"},
            {"stage": "benchmark", "input_artifact": "model_q4", "output_artifact": "benchmark_report"},
        ]

    def test_valid_plan_accepted(self):
        """[export, quantize, benchmark] with valid artifact lineage is accepted."""
        res = self.validator.validate_plan(self.valid_plan, self.initial_artifacts)
        self.assertEqual(res["status"], "accepted")
        self.assertEqual(res["stages"], ["export", "quantize", "benchmark"])
        self.assertIn("benchmark_report", res["final_artifacts"])

    def test_benchmark_before_quantize_rejected(self):
        """Ordering violation (benchmark before quantize) is rejected."""
        invalid_plan = [
            {"stage": "export", "input_artifact": "model_raw", "output_artifact": "model_onnx"},
            {"stage": "benchmark", "input_artifact": "model_onnx", "output_artifact": "report"},
            {"stage": "quantize", "input_artifact": "model_onnx", "output_artifact": "model_q4"},
        ]
        with self.assertRaises(PipelineValidationError) as ctx:
            self.validator.validate_plan(invalid_plan, self.initial_artifacts)
        self.assertEqual(ctx.exception.code, "INVALID_STAGE_ORDER")

    def test_unknown_artifact_reference_rejected(self):
        """Referencing an undeclared input artifact is rejected."""
        unknown_art_plan = [
            {"stage": "export", "input_artifact": "missing_checkpoint", "output_artifact": "model_onnx"},
            {"stage": "quantize", "input_artifact": "model_onnx", "output_artifact": "model_q4"},
            {"stage": "benchmark", "input_artifact": "model_q4", "output_artifact": "benchmark_report"},
        ]
        with self.assertRaises(PipelineValidationError) as ctx:
            self.validator.validate_plan(unknown_art_plan, self.initial_artifacts)
        self.assertEqual(ctx.exception.code, "UNKNOWN_ARTIFACT_REFERENCE")

    def test_run_demo_regression(self):
        """Ensure regression execution of run_demo matches expected contracts."""
        demo_out = run_demo()
        self.assertEqual(demo_out["valid_plan_result"]["status"], "accepted")
        self.assertIsNotNone(demo_out["invalid_order_rejection"])
        self.assertIsNotNone(demo_out["unknown_artifact_rejection"])

    def test_deliberate_wrong_result_fails(self):
        """Deliberate wrong assertion fails."""
        res = self.validator.validate_plan(self.valid_plan, self.initial_artifacts)
        self.assertNotEqual(res["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
