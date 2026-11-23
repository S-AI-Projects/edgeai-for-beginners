"""
Capability Negotiation and Feature Gating.

Demonstrates negotiation between client and server capability sets.
Ensures invocation of any capability not agreed upon during negotiation
is rejected prior to dispatch.
"""

from typing import Set, Dict, Any, Callable, Optional


class CapabilityNegotiationError(Exception):
    """Raised when an operation requests an unnegotiated capability."""
    pass


class CapabilitySession:
    """
    Manages client-server capability negotiation and gated invocation dispatch.
    """

    def __init__(self, client_capabilities: Set[str], server_capabilities: Set[str]):
        self.client_capabilities: Set[str] = set(client_capabilities)
        self.server_capabilities: Set[str] = set(server_capabilities)
        # Negotiated capabilities are the strict intersection of client and server capabilities
        self.negotiated_capabilities: Set[str] = self.client_capabilities.intersection(self.server_capabilities)
        self._dispatch_table: Dict[str, Callable[..., Any]] = {}

    def register_handler(self, capability: str, handler: Callable[..., Any]) -> None:
        """Register an execution handler for a capability."""
        self._dispatch_table[capability] = handler

    def is_supported(self, capability: str) -> bool:
        """Check whether a capability was negotiated and is active."""
        return capability in self.negotiated_capabilities

    def dispatch(self, capability: str, *args: Any, **kwargs: Any) -> Any:
        """
        Dispatch an execution request for a given capability.

        Rejects invocation before dispatch if the capability was not negotiated.
        """
        if capability not in self.negotiated_capabilities:
            raise CapabilityNegotiationError(
                f"Invocation rejected: capability '{capability}' was not negotiated. "
                f"Active capabilities: {sorted(list(self.negotiated_capabilities))}"
            )

        handler = self._dispatch_table.get(capability)
        if handler is None:
            raise NotImplementedError(f"No handler registered for capability '{capability}'.")

        return handler(*args, **kwargs)


def run_demo() -> Dict[str, Any]:
    """
    Runs the canonical example:
    Client: {tools, resources}
    Server: {tools, prompts}
    Negotiates: {tools}
    Calling 'resources' or 'prompts' is rejected before dispatch.
    """
    client_caps = {"tools", "resources"}
    server_caps = {"tools", "prompts"}

    session = CapabilitySession(client_caps, server_caps)
    session.register_handler("tools", lambda query: f"Processed tool invocation: {query}")

    results: Dict[str, Any] = {
        "client_capabilities": sorted(list(client_caps)),
        "server_capabilities": sorted(list(server_caps)),
        "negotiated_capabilities": sorted(list(session.negotiated_capabilities)),
        "tool_call_result": session.dispatch("tools", "search_docs"),
        "rejected_unnegotiated": None,
    }

    try:
        # Attempt to call 'resources' (supported by client, but not server)
        session.dispatch("resources", "fetch_uri")
    except CapabilityNegotiationError as e:
        results["rejected_unnegotiated"] = str(e)

    return results


if __name__ == "__main__":
    out = run_demo()
    print("Capability Negotiation Demo Output:")
    for k, v in out.items():
        print(f"  {k}: {v}")
