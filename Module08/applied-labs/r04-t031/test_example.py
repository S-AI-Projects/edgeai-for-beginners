"""
Unit tests for Capability Negotiation and Gated Dispatch.
"""

import unittest
import sys
import os

# Ensure the module directory is in sys.path for direct running or discovery
sys.path.insert(0, os.path.dirname(__file__))

from example import CapabilitySession, CapabilityNegotiationError, run_demo


class TestCapabilityNegotiation(unittest.TestCase):

    def test_intersection_and_gated_dispatch(self):
        """
        Verify:
        Client {tools, resources}, Server {tools, prompts} -> Negotiated {tools}
        Calling tools succeeds.
        Calling resources is rejected before dispatch.
        """
        client_caps = {"tools", "resources"}
        server_caps = {"tools", "prompts"}
        session = CapabilitySession(client_caps, server_caps)

        # Ensure negotiated capability set is strictly the intersection
        self.assertEqual(session.negotiated_capabilities, {"tools"})
        self.assertTrue(session.is_supported("tools"))
        self.assertFalse(session.is_supported("resources"))
        self.assertFalse(session.is_supported("prompts"))

        session.register_handler("tools", lambda arg: f"tool:{arg}")

        # Dispatch on negotiated capability succeeds
        res = session.dispatch("tools", "calc")
        self.assertEqual(res, "tool:calc")

        # Invocation of client-only capability is rejected before dispatch
        with self.assertRaises(CapabilityNegotiationError):
            session.dispatch("resources", "file:///test")

        # Invocation of server-only capability is rejected before dispatch
        with self.assertRaises(CapabilityNegotiationError):
            session.dispatch("prompts", "tpl_default")

    def test_run_demo(self):
        """Verify the canonical demo execution returns expected structure."""
        demo_res = run_demo()
        self.assertEqual(demo_res["negotiated_capabilities"], ["tools"])
        self.assertEqual(demo_res["tool_call_result"], "Processed tool invocation: search_docs")
        self.assertIn("rejected_unnegotiated", demo_res)
        self.assertIn("resources", demo_res["rejected_unnegotiated"])

    def test_empty_negotiation(self):
        """Verify behavior when client and server have disjoint capability sets."""
        session = CapabilitySession({"audio"}, {"vision"})
        self.assertEqual(session.negotiated_capabilities, set())
        with self.assertRaises(CapabilityNegotiationError):
            session.dispatch("audio", "stream")

    def test_deliberate_failure_check(self):
        """
        Demonstrate that unnegotiated capability cannot be dispatched even if handler is present.
        """
        session = CapabilitySession({"tools"}, {"tools", "resources"})
        session.register_handler("resources", lambda: "bypassed")
        with self.assertRaises(CapabilityNegotiationError):
            session.dispatch("resources")


if __name__ == "__main__":
    unittest.main()
