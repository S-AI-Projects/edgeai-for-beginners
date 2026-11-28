"""
Capability Negotiation — Offline Service Adapter (Deterministic Mock)

NOTE: This module isolates an external chat/model service dependency behind a
callable interface and supplies a deterministic local in-memory mock adapter.
It does NOT talk to a live Chainlit UI, Foundry Local server, or OpenAI SDK endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


UNESTABLISHED_REAL_SERVICE_BEHAVIORS: tuple[str, ...] = (
    "Network transport latency, connection drops, timeouts, and retry backoff",
    "HTTP/WebSocket serialization and Chainlit UI event streaming backpressure",
    "Authentication token expiration, TLS verification, and server-side RBAC enforcement",
    "Runtime server capability drift or mid-session feature revocation",
)


class CapabilityNotNegotiatedError(PermissionError):
    """Raised before dispatch when a requested capability is absent from negotiated set."""


class ServiceBackend(Protocol):
    """Callable service interface hiding the external backend dependency."""

    def __call__(self, operation: str, capability: str | None = None, payload: dict[str, Any] | None = None) -> Any:
        ...


@dataclass
class DeterministicLocalAdapter:
    """Deterministic local mock adapter implementing the callable ServiceBackend interface."""

    server_capabilities: set[str]
    dispatched_calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def __call__(
        self,
        operation: str,
        capability: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if operation == "list_capabilities":
            return set(self.server_capabilities)
        if operation == "dispatch":
            if capability is None:
                raise ValueError("capability is required for dispatch.")
            body = dict(payload or {})
            self.dispatched_calls.append((capability, body))
            return {
                "adapter": "DeterministicLocalAdapter (mock)",
                "capability": capability,
                "echo_payload": body,
                "unestablished_real_behaviors": list(UNESTABLISHED_REAL_SERVICE_BEHAVIORS),
            }
        raise ValueError(f"Unsupported adapter operation: {operation!r}")


class CapabilityGateway:
    """Negotiates capabilities against a callable backend and gates calls before dispatch."""

    def __init__(self, client_capabilities: set[str], service_callable: Callable[..., Any]) -> None:
        self._client_capabilities = set(client_capabilities)
        self._service = service_callable
        self._negotiated: set[str] | None = None

    def negotiate(self) -> set[str]:
        server_caps = set(self._service("list_capabilities"))
        self._negotiated = self._client_capabilities & server_caps
        return set(self._negotiated)

    def call_capability(self, capability: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError("capability must be a non-empty string.")
        if self._negotiated is None:
            self.negotiate()
        assert self._negotiated is not None

        if capability not in self._negotiated:
            raise CapabilityNotNegotiatedError(
                f"Capability {capability!r} not in negotiated set {sorted(self._negotiated)}; "
                "rejected before calling service adapter."
            )
        return self._service("dispatch", capability=capability, payload=payload or {})


if __name__ == "__main__":
    print("=== R04-T025 Capability Negotiation — Offline Service Adapter (Mock) ===")
    adapter = DeterministicLocalAdapter(server_capabilities={"tools", "prompts"})
    gateway = CapabilityGateway(
        client_capabilities={"tools", "resources"},
        service_callable=adapter,
    )
    negotiated = gateway.negotiate()
    print("Negotiated capabilities:", sorted(negotiated))

    dispatched = gateway.call_capability("tools", {"prompt": "hello"})
    print("Dispatched 'tools':", dispatched["adapter"], "| payload:", dispatched["echo_payload"])

    try:
        gateway.call_capability("resources", {"uri": "local://doc"})
    except CapabilityNotNegotiatedError as exc:
        print("Rejected 'resources' before dispatch:", exc)
        print("Adapter dispatch count after rejection:", len(adapter.dispatched_calls))
