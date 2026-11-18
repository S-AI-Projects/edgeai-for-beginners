"""
Unit tests for AI Agent Capability Negotiation & Feature Gating (R04-T059).

Tests:
1. Canonical negotiation: Client {tools, resources} and Server {tools, prompts} negotiates {tools}.
2. Canonical dispatch: Invoking 'tools' succeeds (DISPATCHED).
3. Canonical gating: Invoking 'resources' is strictly rejected before dispatch (REJECTED).
4. Strict mode: Invoking unnegotiated capability raises UnnegotiatedCapabilityError.
5. Disjoint capability sets negotiate empty intersection; all calls rejected.
6. Identical capability sets negotiate complete intersection; all calls permitted.
7. Boundary conditions: Empty capability sets, empty string operations.
8. Contribution focus: Comparison of three controlled configurations across metrics.
9. End-to-end demonstration workflow contract verification.
10. Unestablished behaviors and lesson concept mapping integrity.
"""

import unittest

from example import (
    BenchmarkMetrics,
    CapabilityDispatcher,
    CapabilityNegotiator,
    ConfigurationProfile,
    DispatchResult,
    NegotiationResult,
    UnnegotiatedCapabilityError,
    compare_configurations,
    demonstrate_canonical_contract,
    evaluate_configuration,
    explain_mapping,
    get_standard_configurations,
    identify_unestablished_behaviors,
)


class TestCapabilityNegotiationAndGating(unittest.TestCase):
    def setUp(self):
        self.client_caps = {"tools", "resources"}
        self.server_caps = {"tools", "prompts"}
        self.negotiation = CapabilityNegotiator.negotiate(self.client_caps, self.server_caps)
        self.dispatcher = CapabilityDispatcher(self.negotiation.negotiated_capabilities)

    def test_canonical_negotiation_intersects_to_tools(self):
        """Verify Client {tools, resources} and Server {tools, prompts} negotiates {tools}."""
        self.assertEqual(self.negotiation.negotiated_capabilities, {"tools"})
        self.assertEqual(self.negotiation.client_unmatched, {"resources"})
        self.assertEqual(self.negotiation.server_unmatched, {"prompts"})
        self.assertAlmostEqual(self.negotiation.capability_retention_ratio, 0.5)
        self.assertAlmostEqual(self.negotiation.jaccard_overlap_ratio, 1.0 / 3.0)

    def test_canonical_dispatch_tools_permitted(self):
        """Verify invoking negotiated capability 'tools' is dispatched successfully."""
        res = self.dispatcher.dispatch("tools", "calculator", {"expression": "2+2"})
        self.assertTrue(res.dispatched)
        self.assertEqual(res.status, "DISPATCHED")
        self.assertEqual(res.capability, "tools")
        self.assertEqual(res.operation, "calculator")
        self.assertIsNone(res.reason)
        self.assertIsNotNone(res.output)
        self.assertEqual(res.output["status"], "SUCCESS")

    def test_canonical_dispatch_resources_rejected_before_dispatch(self):
        """Verify invoking unnegotiated capability 'resources' is rejected before dispatch."""
        res = self.dispatcher.dispatch("resources", "read_file", {"path": "/etc/config"})
        self.assertFalse(res.dispatched)
        self.assertEqual(res.status, "REJECTED")
        self.assertEqual(res.capability, "resources")
        self.assertEqual(res.operation, "read_file")
        self.assertIsNone(res.output)
        self.assertIn("rejected before dispatch", res.reason.lower())
        self.assertIn("not negotiated", res.reason.lower())

    def test_strict_mode_raises_unnegotiated_capability_error(self):
        """Verify calling unnegotiated capability in strict mode raises an exception."""
        with self.assertRaises(UnnegotiatedCapabilityError) as ctx:
            self.dispatcher.dispatch("resources", "list_files", strict=True)
        self.assertIn("rejected before dispatch", str(ctx.exception).lower())

    def test_disjoint_capabilities_negotiate_empty_set(self):
        """Verify completely disjoint capabilities negotiate empty set and reject all dispatches."""
        disjoint_neg = CapabilityNegotiator.negotiate({"tools"}, {"prompts"})
        self.assertEqual(disjoint_neg.negotiated_capabilities, set())
        self.assertEqual(disjoint_neg.capability_retention_ratio, 0.0)

        disp = CapabilityDispatcher(disjoint_neg.negotiated_capabilities)
        res1 = disp.dispatch("tools", "calc")
        res2 = disp.dispatch("prompts", "fetch")
        self.assertFalse(res1.dispatched)
        self.assertFalse(res2.dispatched)

    def test_identical_capabilities_negotiate_complete_set(self):
        """Verify identical capabilities negotiate 100% retention ratio."""
        caps = {"tools", "resources", "sampling"}
        ident_neg = CapabilityNegotiator.negotiate(caps, caps)
        self.assertEqual(ident_neg.negotiated_capabilities, caps)
        self.assertEqual(ident_neg.capability_retention_ratio, 1.0)
        self.assertEqual(ident_neg.jaccard_overlap_ratio, 1.0)

        disp = CapabilityDispatcher(ident_neg.negotiated_capabilities)
        for cap in caps:
            self.assertTrue(disp.dispatch(cap, "dummy_op").dispatched)

    def test_empty_capability_sets_boundary(self):
        """Verify empty sets handle negotiation without crashing."""
        empty_neg = CapabilityNegotiator.negotiate(set(), set())
        self.assertEqual(empty_neg.negotiated_capabilities, set())
        self.assertEqual(empty_neg.capability_retention_ratio, 0.0)
        self.assertEqual(empty_neg.jaccard_overlap_ratio, 0.0)

    def test_three_configurations_comparison_and_trade_offs(self):
        """Verify comparison across three controlled configurations and trade-off metrics."""
        comparison = compare_configurations()
        configs = comparison["configurations"]

        # Ensure all three configurations are present
        self.assertIn("Config-Small (Canonical)", configs)
        self.assertIn("Config-Medium (Multi-Feature)", configs)
        self.assertIn("Config-Large (Expanded)", configs)

        # Invariant: Correctness must be 100% across all configs (zero unauthorized dispatches)
        for name, data in configs.items():
            metrics = data["metrics"]
            self.assertEqual(metrics["correctness_rate"], 1.0)
            self.assertEqual(metrics["unauthorized_dispatches"], 0)
            self.assertEqual(
                metrics["permitted_dispatches"] + metrics["rejected_dispatches"],
                metrics["total_calls"],
            )

        # Config Small: 5 calls -> 2 permitted, 3 rejected
        small_metrics = configs["Config-Small (Canonical)"]["metrics"]
        self.assertEqual(small_metrics["permitted_dispatches"], 2)
        self.assertEqual(small_metrics["rejected_dispatches"], 3)

        # Trade-off analysis checks
        trade_offs = comparison["trade_off_analysis"]
        self.assertIn("security_vs_flexibility", trade_offs)
        self.assertIn("pre_dispatch_gating_guarantee", trade_offs)
        self.assertIn("pedagogical_boundary_notice", trade_offs)

    def test_demonstrate_canonical_contract_workflow(self):
        """Verify end-to-end demonstration of the canonical contract."""
        res = demonstrate_canonical_contract()
        self.assertTrue(res["canonical_contract_satisfied"])
        self.assertEqual(res["negotiated_capabilities"], ["tools"])
        self.assertTrue(res["call_tools_result"]["dispatched"])
        self.assertFalse(res["call_resources_result"]["dispatched"])

    def test_unestablished_behaviors_documented(self):
        """Verify explicit declarations preventing unsupported hardware/model claims."""
        unestablished = identify_unestablished_behaviors()
        self.assertGreaterEqual(len(unestablished), 5)
        combined = " ".join(unestablished).lower()
        self.assertIn("network", combined)
        self.assertIn("gpu", combined)
        self.assertIn("model weights", combined)
        self.assertIn("model accuracy", combined)

    def test_concept_mapping_integrity(self):
        """Verify conceptual mapping aligns with Module06/01.IntroduceAgent.md."""
        mappings = explain_mapping()
        self.assertGreaterEqual(len(mappings), 5)
        for item in mappings:
            self.assertIn("component", item)
            self.assertIn("lesson_concept", item)
            self.assertIn("pedagogical_purpose", item)


if __name__ == "__main__":
    unittest.main()
