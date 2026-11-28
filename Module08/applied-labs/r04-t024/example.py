"""
Capability Negotiation — Invariant and State Trace (Local Simulation)

NOTE: This module simulates client/server capability discovery, intersection,
and pre-dispatch gating entirely in memory using deterministic sets. It does
NOT connect to Azure AI Foundry, Foundry Local, or any external SDK/service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SIMULATION_NOTE = (
    "Local deterministic simulation only; no Azure AI Foundry or Foundry Local service call is made."
)


class CapabilityNotNegotiatedError(PermissionError):
    """Raised before dispatch when a requested capability was not negotiated."""

    def __init__(self, capability: str, negotiated: set[str], trace: list[dict[str, Any]]) -> None:
        self.capability = capability
        self.negotiated = sorted(negotiated)
        self.trace = trace
        super().__init__(
            f"Capability {capability!r} rejected before dispatch; "
            f"negotiated capabilities={self.negotiated}."
        )


@dataclass
class CapabilityTraceSession:
    """Tracks step-by-step intermediate state during capability negotiation and invocation."""

    client_capabilities: set[str]
    server_capabilities: set[str]
    trace: list[dict[str, Any]] = field(default_factory=list)
    dispatch_log: list[str] = field(default_factory=list)
    negotiated_capabilities: set[str] = field(default_factory=set)

    def negotiate(self) -> set[str]:
        """Execute discovery and intersection steps, recording intermediate state after each."""
        client_caps = set(self.client_capabilities)
        self.trace.append(
            {
                "step": 1,
                "name": "discover_client",
                "client_capabilities": sorted(client_caps),
            }
        )

        server_caps = set(self.server_capabilities)
        self.trace.append(
            {
                "step": 2,
                "name": "discover_server",
                "server_capabilities": sorted(server_caps),
            }
        )

        self.negotiated_capabilities = client_caps & server_caps
        self.trace.append(
            {
                "step": 3,
                "name": "intersect_capabilities",
                "negotiated_capabilities": sorted(self.negotiated_capabilities),
            }
        )
        return set(self.negotiated_capabilities)

    def invoke(self, capability: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Gate and dispatch a capability invocation, recording gate & dispatch states."""
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError("capability must be a non-empty string.")
        if not self.trace:
            self.negotiate()

        allowed = capability in self.negotiated_capabilities
        self.trace.append(
            {
                "step": len(self.trace) + 1,
                "name": "pre_dispatch_gate",
                "requested_capability": capability,
                "allowed": allowed,
                "dispatch_count_before": len(self.dispatch_log),
            }
        )

        if not allowed:
            self.trace.append(
                {
                    "step": len(self.trace) + 1,
                    "name": "rejected_before_dispatch",
                    "requested_capability": capability,
                    "dispatched": False,
                    "dispatch_count_after": len(self.dispatch_log),
                }
            )
            raise CapabilityNotNegotiatedError(
                capability=capability,
                negotiated=self.negotiated_capabilities,
                trace=list(self.trace),
            )

        self.dispatch_log.append(capability)
        result = {
            "status": "dispatched",
            "capability": capability,
            "payload": payload or {},
            "negotiated_capabilities": sorted(self.negotiated_capabilities),
            "dispatch_count": len(self.dispatch_log),
            "trace": list(self.trace),
            "simulation_note": SIMULATION_NOTE,
        }
        self.trace.append(
            {
                "step": len(self.trace) + 1,
                "name": "dispatched",
                "requested_capability": capability,
                "dispatched": True,
                "dispatch_count_after": len(self.dispatch_log),
            }
        )
        result["trace"] = list(self.trace)
        return result


def verify_trace_invariants(
    trace: list[dict[str, Any]],
    final_output: dict[str, Any],
) -> None:
    """Assert invariants linking intermediate trace states to the final output."""
    by_name = {entry["name"]: entry for entry in trace}
    client_set = set(by_name["discover_client"]["client_capabilities"])
    server_set = set(by_name["discover_server"]["server_capabilities"])
    intersected = set(by_name["intersect_capabilities"]["negotiated_capabilities"])

    if intersected != (client_set & server_set):
        raise AssertionError("Invariant violated: negotiated != client & server.")

    gate = by_name["pre_dispatch_gate"]
    requested = gate["requested_capability"]
    expected_allowed = requested in intersected
    if gate["allowed"] != expected_allowed:
        raise AssertionError("Invariant violated: gate decision disagrees with intersection.")

    if final_output["status"] == "dispatched":
        if not expected_allowed:
            raise AssertionError("Invariant violated: unnegotiated capability was dispatched.")
        if final_output["dispatch_count"] != gate["dispatch_count_before"] + 1:
            raise AssertionError("Invariant violated: dispatch_count did not increment by 1.")
    elif final_output["status"] == "rejected":
        if expected_allowed:
            raise AssertionError("Invariant violated: negotiated capability was rejected.")
        if final_output["dispatch_count"] != gate["dispatch_count_before"]:
            raise AssertionError("Invariant violated: dispatch occurred on rejected call.")
    else:
        raise AssertionError(f"Unexpected final status: {final_output['status']!r}")


if __name__ == "__main__":
    print("=== R04-T024 Capability Negotiation & State Trace (Simulation) ===")
    session = CapabilityTraceSession(
        client_capabilities={"tools", "resources"},
        server_capabilities={"tools", "prompts"},
    )
    ok_result = session.invoke("tools", {"query": "ping"})
    verify_trace_invariants(ok_result["trace"], ok_result)
    print(f"Allowed call 'tools': status={ok_result['status']}, negotiated={ok_result['negotiated_capabilities']}")

    try:
        session.invoke("resources")
    except CapabilityNotNegotiatedError as exc:
        rejected_summary = {
            "status": "rejected",
            "capability": exc.capability,
            "dispatch_count": len(session.dispatch_log),
        }
        verify_trace_invariants(exc.trace, rejected_summary)
        print(f"Blocked call 'resources': {exc} (dispatch_count={len(session.dispatch_log)})")
