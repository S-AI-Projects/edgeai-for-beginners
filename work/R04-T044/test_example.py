import unittest

from example import (NOT_ESTABLISHED, STARTING_ARTIFACTS, AdapterError, FlakyAdapter,
                     LocalOfflineAdapter, PlanError, Stage, execute_plan, good_plan,
                     out_of_order_plan, unknown_artifact_plan, validate_plan)


class SpyRunner:
    """A different callable than the local adapter: proves the interface is just a callable."""

    def __init__(self):
        self.calls = []

    def __call__(self, stage, inputs):
        self.calls.append((stage.name, dict(inputs)))
        return {out: f"spy-{stage.name}" for out in stage.outputs}


class AcceptedPlans(unittest.TestCase):
    def test_export_quantize_benchmark_is_accepted(self):
        self.assertEqual(validate_plan(good_plan(), STARTING_ARTIFACTS),
                         ["export", "quantize", "benchmark"])

    def test_export_then_quantize_only_is_accepted(self):
        plan = good_plan()[:2]
        self.assertEqual(validate_plan(plan, STARTING_ARTIFACTS), ["export", "quantize"])

    def test_single_export_stage_is_accepted(self):
        self.assertEqual(validate_plan(good_plan()[:1], STARTING_ARTIFACTS), ["export"])


class RejectedPlans(unittest.TestCase):
    def assertRejected(self, plan, code):
        spy = SpyRunner()
        with self.assertRaises(PlanError) as ctx:
            execute_plan(plan, STARTING_ARTIFACTS, spy)
        self.assertEqual(ctx.exception.code, code)
        self.assertEqual(spy.calls, [], "the adapter must never be called for a rejected plan")

    def test_benchmark_before_quantize_is_rejected(self):
        self.assertRejected(out_of_order_plan(), "OUT_OF_ORDER")

    def test_quantize_before_export_is_rejected(self):
        plan = [Stage("quantize", ("source_model",), ("ov_int8",)),
                Stage("export", ("source_model",), ("ov_ir",))]
        self.assertRejected(plan, "OUT_OF_ORDER")

    def test_unknown_artifact_reference_is_rejected(self):
        self.assertRejected(unknown_artifact_plan(), "UNKNOWN_ARTIFACT")

    def test_artifact_from_a_later_stage_is_unknown(self):
        plan = [Stage("export", ("ov_int8",), ("ov_ir",)),
                Stage("quantize", ("ov_ir",), ("ov_int8",))]
        self.assertRejected(plan, "UNKNOWN_ARTIFACT")

    def test_empty_plan_is_rejected(self):
        self.assertRejected([], "EMPTY_PLAN")

    def test_unknown_stage_is_rejected(self):
        self.assertRejected([Stage("compress", ("source_model",), ("x",))], "UNKNOWN_STAGE")

    def test_duplicate_stage_is_rejected(self):
        plan = [Stage("export", ("source_model",), ("ov_ir",)),
                Stage("export", ("source_model",), ("ov_ir2",))]
        self.assertRejected(plan, "DUPLICATE_STAGE")

    def test_stage_without_inputs_or_outputs_is_rejected(self):
        self.assertRejected([Stage("export", (), ("ov_ir",))], "MISSING_INPUT")
        self.assertRejected([Stage("export", ("source_model",), ())], "MISSING_OUTPUT")

    def test_recreating_an_existing_artifact_is_rejected(self):
        plan = [Stage("export", ("source_model",), ("ov_ir",)),
                Stage("quantize", ("ov_ir",), ("ov_ir",))]
        self.assertRejected(plan, "DUPLICATE_ARTIFACT")


class CallableInterface(unittest.TestCase):
    def test_local_adapter_runs_the_plan_in_order(self):
        adapter = LocalOfflineAdapter()
        record = execute_plan(good_plan(), STARTING_ARTIFACTS, adapter)
        self.assertEqual(adapter.calls, ["export", "quantize", "benchmark"])
        self.assertEqual([s.name for s in record.stages], ["export", "quantize", "benchmark"])
        self.assertIn("bench_report", record.artifacts)

    def test_each_stage_records_its_input_and_output_ids(self):
        record = execute_plan(good_plan(), STARTING_ARTIFACTS, LocalOfflineAdapter())
        self.assertEqual(record.stages[0].inputs, ("source_model",))
        self.assertEqual(list(record.stages[0].outputs), ["ov_ir"])
        self.assertEqual(record.stages[1].inputs, ("ov_ir",))
        self.assertEqual(list(record.stages[2].outputs), ["bench_report"])

    def test_any_callable_can_stand_in_for_the_service(self):
        spy = SpyRunner()
        record = execute_plan(good_plan(), STARTING_ARTIFACTS, spy)
        self.assertEqual([name for name, _ in spy.calls], ["export", "quantize", "benchmark"])
        self.assertEqual(record.artifacts["ov_int8"], "spy-quantize")

    def test_plain_function_works_too(self):
        def runner(stage, inputs):
            return {out: "x" for out in stage.outputs}
        self.assertEqual(len(execute_plan(good_plan(), STARTING_ARTIFACTS, runner).stages), 3)

    def test_adapter_receives_only_the_declared_inputs(self):
        spy = SpyRunner()
        execute_plan(good_plan(), STARTING_ARTIFACTS, spy)
        self.assertEqual(spy.calls[1][1].keys(), {"ov_ir"})

    def test_local_adapter_is_deterministic(self):
        a = execute_plan(good_plan(), STARTING_ARTIFACTS, LocalOfflineAdapter())
        b = execute_plan(good_plan(), STARTING_ARTIFACTS, LocalOfflineAdapter())
        self.assertEqual(a, b)

    def test_different_inputs_give_different_descriptors(self):
        base = execute_plan(good_plan(), STARTING_ARTIFACTS, LocalOfflineAdapter())
        other_plan = [Stage("export", ("other_model",), ("ov_ir",))]
        other = execute_plan(other_plan, ["other_model"], LocalOfflineAdapter())
        self.assertNotEqual(base.artifacts["ov_ir"], other.artifacts["ov_ir"])

    def test_descriptors_are_labelled_as_simulated(self):
        record = execute_plan(good_plan(), STARTING_ARTIFACTS, LocalOfflineAdapter())
        for stage in record.stages:
            for descriptor in stage.outputs.values():
                self.assertTrue(descriptor.startswith("sim-"))


class AdapterContractFailures(unittest.TestCase):
    def test_wrong_output_ids_are_rejected_and_progress_is_kept(self):
        def runner(stage, inputs):
            return {"wrong_id": "x"} if stage.name == "quantize" else {o: "x" for o in stage.outputs}
        with self.assertRaises(AdapterError) as ctx:
            execute_plan(good_plan(), STARTING_ARTIFACTS, runner)
        self.assertEqual(ctx.exception.code, "BAD_OUTPUTS")
        self.assertEqual([r.name for r in ctx.exception.completed], ["export"])

    def test_non_mapping_or_empty_descriptor_is_rejected(self):
        for bad in (lambda s, i: ["ov_ir"], lambda s, i: {o: "" for o in s.outputs}):
            with self.subTest():
                with self.assertRaises(AdapterError) as ctx:
                    execute_plan(good_plan()[:1], STARTING_ARTIFACTS, bad)
                self.assertEqual(ctx.exception.code, "BAD_OUTPUTS")

    def test_adapter_failure_stops_later_stages(self):
        inner = LocalOfflineAdapter()
        with self.assertRaises(AdapterError) as ctx:
            execute_plan(good_plan(), STARTING_ARTIFACTS, FlakyAdapter(inner, "quantize"))
        self.assertEqual(ctx.exception.code, "ADAPTER_FAILED")
        self.assertEqual([r.name for r in ctx.exception.completed], ["export"])
        self.assertEqual(inner.calls, ["export"])  # benchmark never ran


class MockLimits(unittest.TestCase):
    def test_the_mock_lists_what_it_does_not_establish(self):
        self.assertGreaterEqual(len(NOT_ESTABLISHED), 4)
        text = " ".join(NOT_ESTABLISHED)
        for topic in ("OpenVINO", "latency", "timeouts", "device"):
            self.assertIn(topic, text)


if __name__ == "__main__":
    unittest.main()
