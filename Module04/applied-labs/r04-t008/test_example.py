"""
Unit Tests for Microsoft Olive Optimization Ordering & Recovery (R04-T008)
Module 04: Microsoft Olive Optimization Suite
"""

import unittest

try:
    from .example import (
        OliveWorkflowValidator,
        OliveStage,
        OptimizationWorkflowError,
    )
except ImportError:
    from example import (
        OliveWorkflowValidator,
        OliveStage,
        OptimizationWorkflowError,
    )


class TestOliveWorkflowValidator(unittest.TestCase):
    def setUp(self):
        self.validator = OliveWorkflowValidator(
            registered_artifacts=["olive_source_model"]
        )

    def test_valid_olive_pipeline_accepted(self):
        """[export, quantize, benchmark] in order with valid artifacts is accepted."""
        valid_plan = [
            OliveStage("export", "olive_source_model", "onnx_model"),
            OliveStage("quantize", "onnx_model", "quantized_model"),
            OliveStage("benchmark", "quantized_model", "benchmark_report"),
        ]

        result = self.validator.validate_plan(valid_plan)
        self.assertTrue(result["valid"])
        self.assertEqual(
            result["completed_stages"], ["export", "quantize", "benchmark"]
        )
        self.assertEqual(result["final_artifact"], "benchmark_report")

    def test_benchmark_before_quantize_rejected(self):
        """Benchmark before quantize is rejected with an informative error."""
        invalid_plan = [
            OliveStage("export", "olive_source_model", "onnx_model"),
            OliveStage("benchmark", "onnx_model", "premature_metrics"),
            OliveStage("quantize", "premature_metrics", "quantized_model"),
        ]

        with self.assertRaises(OptimizationWorkflowError) as ctx:
            self.validator.validate_plan(invalid_plan)
        self.assertIn("Invalid stage ordering", str(ctx.exception))
        self.assertIn("Benchmark cannot precede quantize", str(ctx.exception))

    def test_unknown_artifact_reference_rejected(self):
        """Referencing an unknown artifact is rejected with an informative error."""
        broken_artifact_plan = [
            OliveStage("export", "non_existent_source", "onnx_model"),
        ]

        with self.assertRaises(OptimizationWorkflowError) as ctx:
            self.validator.validate_plan(broken_artifact_plan)
        self.assertIn("Unknown artifact reference", str(ctx.exception))
        self.assertIn("non_existent_source", str(ctx.exception))

    def test_failure_and_recovery_demonstration(self):
        """Demonstrate handling an invalid/missing-data error and recovering on subsequent valid input."""
        # 1. Faulty execution
        faulty_plan = [
            OliveStage("export", "olive_source_model", "onnx_model"),
            OliveStage("benchmark", "onnx_model", "premature_metrics"),
        ]
        with self.assertRaises(OptimizationWorkflowError):
            self.validator.validate_plan(faulty_plan)

        # 2. Immediate recovery on the same validator instance with valid plan
        valid_plan = [
            OliveStage("export", "olive_source_model", "onnx_model"),
            OliveStage("quantize", "onnx_model", "int8_model"),
            OliveStage("benchmark", "int8_model", "perf_metrics"),
        ]
        recovered_result = self.validator.validate_plan(valid_plan)
        self.assertTrue(recovered_result["valid"])
        self.assertEqual(
            recovered_result["completed_stages"],
            ["export", "quantize", "benchmark"],
        )
        self.assertEqual(recovered_result["final_artifact"], "perf_metrics")


if __name__ == "__main__":
    unittest.main()
