import unittest

from example import STARTING_ARTIFACTS, PlanError, Stage, good_plan, validate_plan


class NormalCases(unittest.TestCase):
    def test_export_quantize_benchmark_is_accepted(self):
        self.assertEqual(
            validate_plan(good_plan(), STARTING_ARTIFACTS),
            ["export", "quantize", "benchmark"],
        )


class RejectedPlans(unittest.TestCase):
    def assertRejected(self, plan, code):
        with self.assertRaises(PlanError) as ctx:
            validate_plan(plan, STARTING_ARTIFACTS)
        self.assertEqual(ctx.exception.code, code)

    def test_benchmark_before_quantize_is_rejected(self):
        plan = [
            Stage("export", ["source_model"], ["ov_ir"]),
            Stage("benchmark", ["ov_ir"], ["bench_report"]),
            Stage("quantize", ["ov_ir"], ["ov_int8"]),
        ]
        self.assertRejected(plan, "OUT_OF_ORDER")

    def test_quantize_before_export_is_rejected(self):
        plan = [
            Stage("quantize", ["source_model"], ["ov_int8"]),
            Stage("export", ["source_model"], ["ov_ir"]),
        ]
        self.assertRejected(plan, "OUT_OF_ORDER")

    def test_unknown_artifact_reference_is_rejected(self):
        plan = [
            Stage("export", ["source_model"], ["ov_ir"]),
            Stage("quantize", ["does_not_exist"], ["ov_int8"]),
        ]
        self.assertRejected(plan, "UNKNOWN_ARTIFACT")

    def test_artifact_from_a_later_stage_is_unknown(self):
        # provenance: reading an artifact before the stage that produces it
        plan = [
            Stage("export", ["ov_int8"], ["ov_ir"]),
            Stage("quantize", ["ov_ir"], ["ov_int8"]),
        ]
        self.assertRejected(plan, "UNKNOWN_ARTIFACT")


class BoundaryCases(unittest.TestCase):
    def test_single_export_stage_is_accepted(self):
        plan = [Stage("export", ["source_model"], ["ov_ir"])]
        self.assertEqual(validate_plan(plan, STARTING_ARTIFACTS), ["export"])

    def test_empty_plan_is_rejected(self):
        with self.assertRaises(PlanError) as ctx:
            validate_plan([], STARTING_ARTIFACTS)
        self.assertEqual(ctx.exception.code, "EMPTY_PLAN")

    def test_unknown_stage_name_is_rejected(self):
        with self.assertRaises(PlanError) as ctx:
            validate_plan([Stage("compress", ["source_model"], ["x"])], STARTING_ARTIFACTS)
        self.assertEqual(ctx.exception.code, "UNKNOWN_STAGE")

    def test_duplicate_stage_is_rejected(self):
        plan = [
            Stage("export", ["source_model"], ["ov_ir"]),
            Stage("export", ["source_model"], ["ov_ir2"]),
        ]
        with self.assertRaises(PlanError) as ctx:
            validate_plan(plan, STARTING_ARTIFACTS)
        self.assertEqual(ctx.exception.code, "DUPLICATE_STAGE")

    def test_duplicate_output_artifact_is_rejected(self):
        plan = [
            Stage("export", ["source_model"], ["ov_ir"]),
            Stage("quantize", ["ov_ir"], ["ov_ir"]),
        ]
        with self.assertRaises(PlanError) as ctx:
            validate_plan(plan, STARTING_ARTIFACTS)
        self.assertEqual(ctx.exception.code, "DUPLICATE_ARTIFACT")


if __name__ == "__main__":
    unittest.main()
