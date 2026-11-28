from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    UNESTABLISHED_REAL_SERVICE_BEHAVIORS,
    CapabilityGateway,
    CapabilityNotNegotiatedError,
    DeterministicLocalAdapter,
)


class TestOfflineServiceAdapter(unittest.TestCase):
    def test_negotiate_and_dispatch_through_callable_adapter(self):
        """Client {tools,resources} + server {tools,prompts} negotiates {tools} and dispatches via adapter."""
        adapter = DeterministicLocalAdapter(server_capabilities={"tools", "prompts"})
        gateway = CapabilityGateway({"tools", "resources"}, adapter)

        self.assertEqual(gateway.negotiate(), {"tools"})
        response = gateway.call_capability("tools", {"task": "summarize"})
        self.assertEqual(response["capability"], "tools")
        self.assertEqual(response["echo_payload"], {"task": "summarize"})
        self.assertEqual(len(adapter.dispatched_calls), 1)
        self.assertEqual(
            response["unestablished_real_behaviors"],
            list(UNESTABLISHED_REAL_SERVICE_BEHAVIORS),
        )

    def test_unnegotiated_capability_rejected_before_adapter_dispatch(self):
        """Calling 'resources' raises before the callable adapter's dispatch branch is ever invoked."""
        adapter = DeterministicLocalAdapter(server_capabilities={"tools", "prompts"})
        gateway = CapabilityGateway({"tools", "resources"}, adapter)

        with self.assertRaises(CapabilityNotNegotiatedError):
            gateway.call_capability("resources", {"uri": "file:///test.txt"})

        self.assertEqual(adapter.dispatched_calls, [])

    def test_custom_callable_stub_proves_interface_decoupling(self):
        """Any callable matching the ServiceBackend interface works without concrete adapter class."""
        calls: list[str] = []

        def fake_callable(operation: str, capability: str | None = None, payload=None):
            if operation == "list_capabilities":
                return {"prompts"}
            calls.append(f"{operation}:{capability}")
            return {"ok": True, "capability": capability}

        gateway = CapabilityGateway({"prompts", "tools"}, fake_callable)
        self.assertEqual(gateway.negotiate(), {"prompts"})
        self.assertEqual(gateway.call_capability("prompts")["ok"], True)
        with self.assertRaises(CapabilityNotNegotiatedError):
            gateway.call_capability("tools")
        self.assertEqual(calls, ["dispatch:prompts"])

    def test_empty_capability_rejected(self):
        adapter = DeterministicLocalAdapter({"tools"})
        gateway = CapabilityGateway({"tools"}, adapter)
        with self.assertRaises(ValueError):
            gateway.call_capability("")


if __name__ == "__main__":
    unittest.main()
