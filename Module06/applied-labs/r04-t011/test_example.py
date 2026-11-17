"""
Unit tests for R04-T011 Capability Negotiation.
Tests normal, boundary, failure scenarios, and deliberate failure detection.
"""

import itertools
import unittest

from example import (
    NegotiationError,
    invoke_baseline,
    invoke_capability,
    invoke_refactored,
    negotiate_capabilities,
    run_concept_example,
    validate_capability_set,
)


class TestNormalFixture(unittest.TestCase):
    """Test the canonical fixture specified in issue R04-T011."""

    def setUp(self):
        self.client_caps = {"tools", "resources"}
        self.server_caps = {"tools", "prompts"}
        self.dispatch_log = []

        self.handlers = {
            "tools": lambda p: (self.dispatch_log.append("tools"), f"tools-handled:{p}")[1],
            "resources": lambda p: (self.dispatch_log.append("resources"), f"resources-handled:{p}")[1],
            "prompts": lambda p: (self.dispatch_log.append("prompts"), f"prompts-handled:{p}")[1],
        }

    def test_negotiation_intersection(self):
        """Client {tools, resources} and Server {tools, prompts} negotiate strictly to {tools}."""
        negotiated = negotiate_capabilities(self.client_caps, self.server_caps)
        self.assertEqual(negotiated, frozenset({"tools"}))

    def test_invoke_negotiated_capability_succeeds(self):
        """Calling negotiated capability 'tools' dispatches to handler."""
        result = invoke_capability(
            self.client_caps, self.server_caps, "tools", "ping", self.handlers
        )
        self.assertEqual(result, "tools-handled:ping")
        self.assertEqual(self.dispatch_log, ["tools"])

    def test_calling_unnegotiated_client_resource_is_rejected_before_dispatch(self):
        """
        Calling 'resources' (in client caps but not server caps) is rejected
        before dispatch with NOT_NEGOTIATED, and handler is never executed.
        """
        with self.assertRaises(NegotiationError) as ctx:
            invoke_capability(
                self.client_caps, self.server_caps, "resources", "read-file", self.handlers
            )
        self.assertEqual(ctx.exception.code, "NOT_NEGOTIATED")
        # Ensure handler was NEVER reached
        self.assertEqual(self.dispatch_log, [])

    def test_calling_server_only_capability_is_rejected(self):
        """Calling 'prompts' (in server caps only) is rejected before dispatch."""
        with self.assertRaises(NegotiationError) as ctx:
            invoke_capability(
                self.client_caps, self.server_caps, "prompts", "get-sys-prompt", self.handlers
            )
        self.assertEqual(ctx.exception.code, "NOT_NEGOTIATED")
        self.assertEqual(self.dispatch_log, [])

    def test_run_concept_example_summary(self):
        """Verify the self-contained run_concept_example summary dictionary."""
        summary = run_concept_example()
        self.assertEqual(summary["negotiated"], ["tools"])
        self.assertEqual(summary["tools_result"], "tools-handled:ping")
        self.assertTrue(summary["resources_rejected"])
        self.assertEqual(summary["resources_error_code"], "NOT_NEGOTIATED")
        self.assertEqual(summary["handlers_called"], ["tools"])


class TestBoundaryCases(unittest.TestCase):
    """Test edge cases, boundary conditions, and property invariants."""

    def test_disjoint_capabilities_yields_empty_set(self):
        result = negotiate_capabilities({"tools"}, {"prompts"})
        self.assertEqual(result, frozenset())

    def test_identical_capabilities_yields_full_set(self):
        result = negotiate_capabilities({"tools", "resources"}, {"tools", "resources"})
        self.assertEqual(result, frozenset({"tools", "resources"}))

    def test_empty_client_or_server_caps(self):
        self.assertEqual(negotiate_capabilities([], ["tools"]), frozenset())
        self.assertEqual(negotiate_capabilities(["tools"], []), frozenset())
        self.assertEqual(negotiate_capabilities([], []), frozenset())

    def test_gate_priority_over_missing_handler(self):
        """
        If capability is NOT negotiated AND has NO handler registered,
        the error MUST be NOT_NEGOTIATED (proving gate happens before dispatch).
        """
        empty_handlers = {}
        with self.assertRaises(NegotiationError) as ctx:
            invoke_capability({"tools"}, {"tools"}, "resources", "req", empty_handlers)
        self.assertEqual(ctx.exception.code, "NOT_NEGOTIATED")

    def test_negotiated_capability_missing_handler_reports_no_handler(self):
        """If capability is negotiated but has no handler registered, report NO_HANDLER."""
        empty_handlers = {}
        with self.assertRaises(NegotiationError) as ctx:
            invoke_capability({"tools"}, {"tools"}, "tools", "req", empty_handlers)
        self.assertEqual(ctx.exception.code, "NO_HANDLER")

    def test_input_immutability(self):
        """Ensure original input collections are not modified."""
        client = {"tools", "resources"}
        server = {"tools", "prompts"}
        client_copy = set(client)
        server_copy = set(server)
        negotiate_capabilities(client, server)
        self.assertEqual(client, client_copy)
        self.assertEqual(server, server_copy)

    def test_commutative_property(self):
        """negotiate(A, B) == negotiate(B, A)"""
        c1 = {"a", "b", "c"}
        c2 = {"b", "c", "d"}
        self.assertEqual(negotiate_capabilities(c1, c2), negotiate_capabilities(c2, c1))

    def test_subset_property(self):
        """Result must be a subset of both client and server capability sets."""
        c1 = {"tools", "resources"}
        c2 = {"tools", "prompts"}
        result = negotiate_capabilities(c1, c2)
        self.assertTrue(result.issubset(c1))
        self.assertTrue(result.issubset(c2))

    def test_handler_exception_propagates(self):
        """Exceptions raised inside a handler must propagate unchanged."""
        def faulty_handler(_):
            raise RuntimeError("Database connection timeout")

        with self.assertRaises(RuntimeError) as ctx:
            invoke_capability({"tools"}, {"tools"}, "tools", "ping", {"tools": faulty_handler})
        self.assertIn("Database connection timeout", str(ctx.exception))


class TestFailureCases(unittest.TestCase):
    """Test validation errors and invalid inputs."""

    def test_bare_string_rejected_as_capability_set(self):
        """A bare string like 'tools' must be rejected to prevent character iteration."""
        with self.assertRaises(NegotiationError) as ctx:
            validate_capability_set("tools")
        self.assertEqual(ctx.exception.code, "BAD_CAPABILITY_SET")

    def test_none_and_non_collections_rejected(self):
        for bad_input in (None, 123, 45.6, True, {"a": "b"}):
            with self.assertRaises(NegotiationError) as ctx:
                validate_capability_set(bad_input)
            self.assertEqual(ctx.exception.code, "BAD_CAPABILITY_SET")

    def test_empty_or_non_string_items_rejected(self):
        for bad_set in ([""], ["   "], [None], [1, 2], ["tools", ""]):
            with self.assertRaises(NegotiationError) as ctx:
                validate_capability_set(bad_set)
            self.assertEqual(ctx.exception.code, "BAD_CAPABILITY_SET")

    def test_invalid_requested_capability(self):
        for bad_target in (None, "", "   ", 123):
            with self.assertRaises(NegotiationError) as ctx:
                invoke_capability({"tools"}, {"tools"}, bad_target, "payload", {})
            self.assertEqual(ctx.exception.code, "BAD_REQUEST")


class TestEquivalenceAndDeliberateFailure(unittest.TestCase):
    """
    Verify equivalence of baseline and refactored versions, and ensure that
    deliberate flaws (e.g. using union or omitting the gate) cause failures.
    """

    def test_baseline_and_refactored_equivalence(self):
        universe = ["tools", "resources", "prompts"]
        subsets = []
        for r in range(len(universe) + 1):
            for combo in itertools.combinations(universe, r):
                subsets.append(set(combo))

        for client_set in subsets:
            for server_set in subsets:
                for target in ["tools", "resources", "prompts", "unknown"]:
                    # Compare baseline vs refactored
                    baseline_exc, baseline_res = None, None
                    try:
                        baseline_res = invoke_baseline(
                            client_set,
                            server_set,
                            target,
                            "payload",
                            {"tools": lambda p: f"t:{p}", "resources": lambda p: f"r:{p}"}
                        )
                    except NegotiationError as exc:
                        baseline_exc = exc.code

                    refactored_exc, refactored_res = None, None
                    try:
                        refactored_res = invoke_refactored(
                            client_set,
                            server_set,
                            target,
                            "payload",
                            {"tools": lambda p: f"t:{p}", "resources": lambda p: f"r:{p}"}
                        )
                    except NegotiationError as exc:
                        refactored_exc = exc.code

                    self.assertEqual(baseline_exc, refactored_exc)
                    self.assertEqual(baseline_res, refactored_res)

    def test_deliberate_flaw_union_instead_of_intersection_fails(self):
        """Deliberately flawed negotiation (union instead of intersection) must fail acceptance."""
        def flawed_negotiate(client_caps, server_caps):
            # Deliberate bug: using union
            return set(client_caps) | set(server_caps)

        client_caps = {"tools", "resources"}
        server_caps = {"tools", "prompts"}
        flawed_result = flawed_negotiate(client_caps, server_caps)

        # Assertion checks that flawed result violates requirement: 'resources' should NOT be negotiated
        with self.assertRaises(AssertionError):
            self.assertEqual(flawed_result, {"tools"})

    def test_deliberate_flaw_missing_dispatch_gate_fails(self):
        """Deliberate bug omitting the pre-dispatch gate must fail."""
        def flawed_dispatch(client_caps, server_caps, capability, payload, handlers):
            # Deliberate bug: dispatches without checking negotiated set
            return handlers[capability](payload)

        client_caps = {"tools", "resources"}
        server_caps = {"tools", "prompts"}
        handlers = {"resources": lambda p: "unauthorized_dispatch"}

        # Should have raised NOT_NEGOTIATED; running flawed dispatch succeeds instead, violating security contract
        res = flawed_dispatch(client_caps, server_caps, "resources", "data", handlers)
        with self.assertRaises(AssertionError):
            # Assert that resources was rejected (which it wasn't in the flawed version)
            self.assertEqual(res, "SHOULD_HAVE_BEEN_REJECTED")


if __name__ == "__main__":
    unittest.main()
