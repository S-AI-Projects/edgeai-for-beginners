from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    CapabilityNotNegotiatedError,
    CapabilityTraceSession,
    SIMULATION_NOTE,
    verify_trace_invariants,
)


class TestCapabilityNegotiationStateTrace(unittest.TestCase):
    def test_intersect_and_dispatch_negotiated_capability(self):
        """Client {tools,resources} and server {tools,prompts} negotiate {tools} and allow dispatch."""
        session = CapabilityTraceSession({"tools", "resources"}, {"tools", "prompts"})
        result = session.invoke("tools", {"action": "list"})
        self.assertEqual(result["negotiated_capabilities"], ["tools"])
        self.assertEqual(result["status"], "dispatched")
        self.assertEqual(result["dispatch_count"], 1)
        self.assertEqual(result["simulation_note"], SIMULATION_NOTE)
        verify_trace_invariants(result["trace"], result)

    def test_unnegotiated_capability_rejected_before_dispatch(self):
        """Calling 'resources' fails pre-dispatch gate without incrementing dispatch_log."""
        session = CapabilityTraceSession({"tools", "resources"}, {"tools", "prompts"})
        with self.assertRaises(CapabilityNotNegotiatedError) as ctx:
            session.invoke("resources")

        self.assertEqual(ctx.exception.negotiated, ["tools"])
        self.assertEqual(session.dispatch_log, [])
        step_names = [entry["name"] for entry in ctx.exception.trace]
        self.assertEqual(
            step_names,
            [
                "discover_client",
                "discover_server",
                "intersect_capabilities",
                "pre_dispatch_gate",
                "rejected_before_dispatch",
            ],
        )
        verify_trace_invariants(
            ctx.exception.trace,
            {"status": "rejected", "dispatch_count": len(session.dispatch_log)},
        )

    def test_disjoint_sets_negotiate_empty_and_reject_all(self):
        """Disjoint capability sets negotiate empty set and reject every capability."""
        session = CapabilityTraceSession({"resources"}, {"prompts"})
        negotiated = session.negotiate()
        self.assertEqual(negotiated, set())
        with self.assertRaises(CapabilityNotNegotiatedError):
            session.invoke("prompts")
        self.assertEqual(session.dispatch_log, [])

    def test_invariant_checker_fails_on_deliberate_wrong_state(self):
        """A deliberate invariant violation (claiming dispatch when unnegotiated) must fail."""
        session = CapabilityTraceSession({"tools", "resources"}, {"tools", "prompts"})
        with self.assertRaises(CapabilityNotNegotiatedError) as ctx:
            session.invoke("resources")

        corrupted_output = {"status": "dispatched", "dispatch_count": 1}
        with self.assertRaises(AssertionError):
            verify_trace_invariants(ctx.exception.trace, corrupted_output)

    def test_empty_capability_name_rejected(self):
        session = CapabilityTraceSession({"tools"}, {"tools"})
        with self.assertRaises(ValueError):
            session.invoke("   ")


if __name__ == "__main__":
    unittest.main()
