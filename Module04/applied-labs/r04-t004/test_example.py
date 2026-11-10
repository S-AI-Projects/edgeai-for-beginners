"""
Unit Tests for Optimization-Stage Ordering (R04-T004)
Module 04: Edge AI Development Workflow Synthesis
"""

import unittest

try:
    from .example import OptimizationWorkflowValidator, StagePlan
except ImportError:
    from example import OptimizationWorkflowValidator, StagePlan


class TestOptimizationWorkflowValidator(unittest.TestCase):
    def setUp(self):
        self.validator = OptimizationWorkflowValidator(
            initial_artifact_ids=["source_model_v1"]
        )

    def test_valid_optimization_pipeline_accepted(self):
        """[export, quantize, benchmark] in order with matching artifacts is accepted."""
        plan = [
            StagePlan("export", "source_model_v1", "exported_ir"),
            StagePlan("quantize", "exported_ir", "quantized_model"),
            StagePlan("benchmark", "quantized_model", "benchmark_report"),
        ]

        result = self.validator.validate_plan(plan)
        self.assertTrue(result["valid"])
        self.assertEqual(
            result["completed_stages"], ["export", "quantize", "benchmark"]
        )
        self.assertEqual(result["final_artifact"], "benchmark_report")
        self.assertTrue(result["provenance_invariant_holds"])

    def test_benchmark_before_quantize_rejected(self):
        """Benchmark executed before quantize is rejected."""
        plan = [
            StagePlan("export", "source_model_v1", "exported_ir"),
            StagePlan("benchmark", "exported_ir", "premature_benchmark"),
            StagePlan("quantize", "premature_benchmark", "quantized_model"),
        ]

        with self.assertRaises(ValueError) as ctx:
            self.validator.validate_plan(plan)
        self.assertIn("Invalid stage order", str(ctx.exception))
        self.assertIn("benchmark", str(ctx.exception))

    def test_unknown_artifact_reference_rejected(self):
        """Referencing an undeclared or non-existent input artifact is rejected."""
        plan = [
            StagePlan("export", "completely_unknown_artifact", "exported_ir"),
            StagePlan("quantize", "exported_ir", "quantized_model"),
            StagePlan("benchmark", "quantized_model", "benchmark_report"),
        ]

        with self.assertRaises(ValueError) as ctx:
            self.validator.validate_plan(plan)
        self.assertIn("Unknown artifact reference", str(ctx.exception))
        self.assertIn("completely_unknown_artifact", str(ctx.exception))

    def test_state_trace_and_provenance_invariant(self):
        """State trace records intermediate steps and links initial source to final output."""
        plan = [
            StagePlan("export", "source_model_v1", "exported_ir"),
            StagePlan("quantize", "exported_ir", "quantized_model"),
            StagePlan("benchmark", "quantized_model", "benchmark_report"),
        ]

        result = self.validator.validate_plan(plan)
        trace = result["state_trace"]

        # Step 0 is INIT
        self.assertEqual(trace[0]["action"], "INIT")
        self.assertEqual(trace[0]["available_artifacts"], ["source_model_v1"])

        # Steps 1 to 3
        self.assertEqual(len(trace), 4)
        self.assertEqual(trace[1]["action"], "EXEC_EXPORT")
        self.assertIn("exported_ir", trace[1]["available_artifacts"])

        self.assertEqual(trace[2]["action"], "EXEC_QUANTIZE")
        self.assertIn("quantized_model", trace[2]["available_artifacts"])

        self.assertEqual(trace[3]["action"], "EXEC_BENCHMARK")
        self.assertIn("benchmark_report", trace[3]["available_artifacts"])

        # Monotonically increasing artifacts count
        counts = [len(step["available_artifacts"]) for step in trace]
        self.assertEqual(counts, [1, 2, 3, 4])
        self.assertTrue(result["provenance_invariant_holds"])


if __name__ == "__main__":
    unittest.main()
