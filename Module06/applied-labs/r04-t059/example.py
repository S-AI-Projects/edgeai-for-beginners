"""
AI Agent Capability Negotiation and Feature Gating Example (R04-T059).
Module 06: AI Agents and Small Language Models (01.IntroduceAgent.md)

Concept:
In AI agent architectures (including Model Context Protocol and multi-agent platforms),
clients and servers must dynamically discover and negotiate supported capabilities
(e.g., tools, resources, prompts, sampling, roots) prior to operation dispatch.
To enforce security, privacy, and architectural invariants, any invocation of an
unnegotiated capability must be rejected *before* dispatch, preventing unauthorized
execution, malformed payloads, and runtime exceptions.

Core Contract:
1. Client {tools, resources} and Server {tools, prompts} negotiate capability set {tools}.
2. Calling an unnegotiated capability (e.g. 'resources') is strictly rejected before dispatch
   with an actionable diagnostic message.
3. Contribution Focus: Compare three small controlled configurations using metrics appropriate
   to this contract (correctness, capability retention ratio, gating overhead), and report
   the observed trade-offs without claiming real-world model accuracy.
"""

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Dict, List, Optional, Set, Tuple


class UnnegotiatedCapabilityError(Exception):
    """Raised when an unnegotiated capability is invoked in strict mode."""
    pass


@dataclass
class NegotiationResult:
    """Result of intersecting client and server capability sets."""
    client_capabilities: Set[str]
    server_capabilities: Set[str]
    negotiated_capabilities: Set[str]
    client_unmatched: Set[str]
    server_unmatched: Set[str]
    capability_retention_ratio: float  # |C ∩ S| / |C|
    jaccard_overlap_ratio: float       # |C ∩ S| / |C ∪ S|

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_capabilities": sorted(list(self.client_capabilities)),
            "server_capabilities": sorted(list(self.server_capabilities)),
            "negotiated_capabilities": sorted(list(self.negotiated_capabilities)),
            "client_unmatched": sorted(list(self.client_unmatched)),
            "server_unmatched": sorted(list(self.server_unmatched)),
            "capability_retention_ratio": round(self.capability_retention_ratio, 4),
            "jaccard_overlap_ratio": round(self.jaccard_overlap_ratio, 4),
        }


@dataclass
class DispatchResult:
    """Outcome of attempting to dispatch an operation under a capability."""
    status: str  # "DISPATCHED" or "REJECTED"
    dispatched: bool
    capability: str
    operation: str
    reason: Optional[str] = None
    output: Optional[Any] = None
    payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CapabilityNegotiator:
    """Performs read-only capability intersection between client and server."""

    @staticmethod
    def negotiate(
        client_capabilities: Set[str], server_capabilities: Set[str]
    ) -> NegotiationResult:
        """
        Intersect client and server capability sets.
        
        Args:
            client_capabilities: Capabilities supported/requested by client.
            server_capabilities: Capabilities exposed by server.
            
        Returns:
            NegotiationResult containing the intersection and telemetry.
        """
        c_set = set(client_capabilities)
        s_set = set(server_capabilities)
        negotiated = c_set.intersection(s_set)
        client_unmatched = c_set.difference(s_set)
        server_unmatched = s_set.difference(c_set)
        union = c_set.union(s_set)

        retention = len(negotiated) / len(c_set) if c_set else 0.0
        jaccard = len(negotiated) / len(union) if union else 0.0

        return NegotiationResult(
            client_capabilities=c_set,
            server_capabilities=s_set,
            negotiated_capabilities=negotiated,
            client_unmatched=client_unmatched,
            server_unmatched=server_unmatched,
            capability_retention_ratio=retention,
            jaccard_overlap_ratio=jaccard,
        )


class CapabilityDispatcher:
    """
    Enforces pre-dispatch gating based on negotiated capabilities.
    Rejects invocation of any unnegotiated capability before dispatch occurs.
    """

    def __init__(
        self,
        negotiated_capabilities: Set[str],
        lesson_source: str = "Module06/01.IntroduceAgent.md",
    ):
        self.negotiated_capabilities: Set[str] = set(negotiated_capabilities)
        self.lesson_source: str = lesson_source
        self.dispatch_history: List[DispatchResult] = []

    def can_dispatch(self, capability: str) -> bool:
        """Check if capability is negotiated."""
        return capability in self.negotiated_capabilities

    def dispatch(
        self,
        capability: str,
        operation: str,
        payload: Optional[Dict[str, Any]] = None,
        strict: bool = False,
    ) -> DispatchResult:
        """
        Dispatch an operation under the specified capability.
        
        If capability is not negotiated, the operation is REJECTED before dispatch.
        
        Args:
            capability: Target capability (e.g., 'tools', 'resources', 'prompts').
            operation: Name of operation to invoke.
            payload: Optional payload/parameters.
            strict: If True, raises UnnegotiatedCapabilityError on rejection.
            
        Returns:
            DispatchResult detailing whether dispatch occurred or why it was rejected.
        """
        if not self.can_dispatch(capability):
            reason = (
                f"Invocation of capability '{capability}' rejected before dispatch: "
                f"capability was not negotiated. Negotiated capabilities: "
                f"{sorted(list(self.negotiated_capabilities))}."
            )
            result = DispatchResult(
                status="REJECTED",
                dispatched=False,
                capability=capability,
                operation=operation,
                reason=reason,
                output=None,
                payload=payload,
            )
            self.dispatch_history.append(result)
            if strict:
                raise UnnegotiatedCapabilityError(reason)
            return result

        # Simulating successful local dispatch
        output = {
            "executed_operation": operation,
            "capability": capability,
            "status": "SUCCESS",
            "payload_received": payload,
        }
        result = DispatchResult(
            status="DISPATCHED",
            dispatched=True,
            capability=capability,
            operation=operation,
            reason=None,
            output=output,
            payload=payload,
        )
        self.dispatch_history.append(result)
        return result


# =============================================================================
# Benchmarking & Configuration Comparison (Contribution Focus)
# =============================================================================

@dataclass
class ConfigurationProfile:
    """Specification of a test configuration."""
    name: str
    description: str
    client_capabilities: Set[str]
    server_capabilities: Set[str]
    workload: List[Tuple[str, str]]  # list of (capability, operation)


@dataclass
class BenchmarkMetrics:
    """Metrics evaluated for each configuration."""
    total_calls: int
    permitted_dispatches: int
    rejected_dispatches: int
    correctness_rate: float            # 1.0 = 100% accurate enforcement
    capability_retention_ratio: float  # |C ∩ S| / |C|
    jaccard_overlap_ratio: float       # |C ∩ S| / |C ∪ S|
    gating_checks_performed: int
    unauthorized_dispatches: int       # Must be 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_standard_configurations() -> List[ConfigurationProfile]:
    """Define three small controlled configurations with varying capability sizes."""
    return [
        # Configuration 1: Canonical Minimal (2 client caps, 2 server caps)
        ConfigurationProfile(
            name="Config-Small (Canonical)",
            description="Minimal baseline: Client {tools, resources}, Server {tools, prompts}",
            client_capabilities={"tools", "resources"},
            server_capabilities={"tools", "prompts"},
            workload=[
                ("tools", "execute_calculator"),
                ("resources", "read_file"),
                ("tools", "search_index"),
                ("resources", "list_files"),
                ("prompts", "get_system_prompt"),
            ],
        ),
        # Configuration 2: Medium (4 client caps, 4 server caps)
        ConfigurationProfile(
            name="Config-Medium (Multi-Feature)",
            description="Intermediate: Client {tools, resources, sampling, roots}, Server {tools, prompts, sampling, logging}",
            client_capabilities={"tools", "resources", "sampling", "roots"},
            server_capabilities={"tools", "prompts", "sampling", "logging"},
            workload=[
                ("tools", "execute_query"),
                ("sampling", "sample_tokens"),
                ("resources", "fetch_document"),
                ("roots", "get_workspace_root"),
                ("tools", "run_linter"),
                ("sampling", "generate_completion"),
                ("prompts", "fetch_template"),
                ("logging", "emit_trace"),
            ],
        ),
        # Configuration 3: Large (8 client caps, 8 server caps)
        ConfigurationProfile(
            name="Config-Large (Expanded)",
            description="Expanded: 8 client caps, 8 server caps, 4 negotiated",
            client_capabilities={
                "tools", "resources", "sampling", "roots",
                "vision", "audio", "telemetry", "streaming"
            },
            server_capabilities={
                "tools", "prompts", "sampling", "logging",
                "vision", "database", "telemetry", "cache"
            },
            workload=[
                ("tools", "op_tool_1"),
                ("sampling", "op_sample_1"),
                ("vision", "op_vision_1"),
                ("telemetry", "op_telemetry_1"),
                ("resources", "op_resource_1"),
                ("audio", "op_audio_1"),
                ("roots", "op_roots_1"),
                ("streaming", "op_stream_1"),
                ("prompts", "op_prompt_1"),
                ("database", "op_db_1"),
                ("tools", "op_tool_2"),
                ("telemetry", "op_telemetry_2"),
            ],
        ),
    ]


def evaluate_configuration(config: ConfigurationProfile) -> Tuple[NegotiationResult, BenchmarkMetrics, List[DispatchResult]]:
    """Evaluate capability negotiation and dispatch gating for a configuration."""
    negotiation = CapabilityNegotiator.negotiate(
        config.client_capabilities, config.server_capabilities
    )
    dispatcher = CapabilityDispatcher(negotiation.negotiated_capabilities)

    dispatches: List[DispatchResult] = []
    unauthorized_dispatches = 0
    correct_decisions = 0

    for cap, op in config.workload:
        res = dispatcher.dispatch(cap, op)
        dispatches.append(res)

        expected_allowed = cap in negotiation.negotiated_capabilities
        if res.dispatched:
            if not expected_allowed:
                unauthorized_dispatches += 1
            else:
                correct_decisions += 1
        else:
            if expected_allowed:
                pass  # False negative
            else:
                correct_decisions += 1  # Correct rejection before dispatch

    total_calls = len(config.workload)
    correctness = correct_decisions / total_calls if total_calls else 1.0

    metrics = BenchmarkMetrics(
        total_calls=total_calls,
        permitted_dispatches=sum(1 for d in dispatches if d.dispatched),
        rejected_dispatches=sum(1 for d in dispatches if not d.dispatched),
        correctness_rate=correctness,
        capability_retention_ratio=negotiation.capability_retention_ratio,
        jaccard_overlap_ratio=negotiation.jaccard_overlap_ratio,
        gating_checks_performed=total_calls,
        unauthorized_dispatches=unauthorized_dispatches,
    )

    return negotiation, metrics, dispatches


def compare_configurations() -> Dict[str, Any]:
    """
    Execute benchmark comparison across the three controlled configurations.
    Returns structured results, metrics, and trade-off analysis.
    """
    configs = get_standard_configurations()
    results = {}

    for cfg in configs:
        neg, metrics, _ = evaluate_configuration(cfg)
        results[cfg.name] = {
            "description": cfg.description,
            "negotiation": neg.to_dict(),
            "metrics": metrics.to_dict(),
        }

    trade_off_analysis = {
        "security_vs_flexibility": (
            "Small capability configurations (Config-Small) minimize attack surface by negotiating "
            "only essential capabilities (retention 50%, overlap 33.3%), but reject unnegotiated calls (60% rejection). "
            "Expanded configurations (Config-Large) enable richer multi-modal workflows (4 negotiated capabilities) "
            "while maintaining 100% pre-dispatch rejection correctness."
        ),
        "pre_dispatch_gating_guarantee": (
            "Across all configurations, unnegotiated capabilities are rejected before dispatch (unauthorized_dispatches=0). "
            "This eliminates downstream serialization overhead, unnecessary RPC round-trips, and server-side state corruption."
        ),
        "pedagogical_boundary_notice": (
            "This metric measures capability negotiation correctness and pre-dispatch feature gating. "
            "It makes no claim about real-world LLM accuracy, inference token generation speed, or physical hardware benchmarks."
        ),
    }

    return {
        "configurations": results,
        "trade_off_analysis": trade_off_analysis,
    }


def demonstrate_canonical_contract() -> Dict[str, Any]:
    """
    Demonstrate the exact canonical contract specified in the task:
    Client {tools, resources}, Server {tools, prompts} negotiates {tools};
    calling resources is rejected before dispatch.
    """
    client_caps = {"tools", "resources"}
    server_caps = {"tools", "prompts"}

    # 1. Negotiate
    neg = CapabilityNegotiator.negotiate(client_caps, server_caps)

    # 2. Setup Dispatcher
    dispatcher = CapabilityDispatcher(neg.negotiated_capabilities)

    # 3. Call 'tools' -> Permitted
    res_tools = dispatcher.dispatch("tools", "execute_function", {"query": "weather"})

    # 4. Call 'resources' -> Rejected before dispatch
    res_resources = dispatcher.dispatch("resources", "read_file", {"uri": "file:///data.txt"})

    return {
        "client_capabilities": sorted(list(client_caps)),
        "server_capabilities": sorted(list(server_caps)),
        "negotiated_capabilities": sorted(list(neg.negotiated_capabilities)),
        "call_tools_result": res_tools.to_dict(),
        "call_resources_result": res_resources.to_dict(),
        "canonical_contract_satisfied": (
            neg.negotiated_capabilities == {"tools"}
            and res_tools.dispatched is True
            and res_resources.dispatched is False
            and "rejected before dispatch" in (res_resources.reason or "").lower()
        ),
    }


def identify_unestablished_behaviors() -> List[str]:
    """Identify behaviors that this offline educational validator does not establish."""
    return [
        "Does not establish network reachability, socket handshakes, or live MCP daemon processes.",
        "Does not query physical GPU / NPU hardware registers or measure VRAM allocation.",
        "Does not download model weights, evaluate token generation throughput, or measure model accuracy.",
        "Does not inspect OS-level kernel process tables or invoke package managers.",
        "Does not invoke external cloud provider endpoints or paid API services.",
    ]


def explain_mapping() -> List[Dict[str, str]]:
    """Map components to Module06/01.IntroduceAgent.md concepts."""
    return [
        {
            "component": "CapabilityNegotiator.negotiate()",
            "lesson_concept": "Agent Discovery & Tool/Capability Negotiation",
            "pedagogical_purpose": "Demonstrates set-theoretic capability intersection between heterogeneous client and server agents.",
        },
        {
            "component": "CapabilityDispatcher.dispatch() gating check",
            "lesson_concept": "Agent Operational Boundaries & Safe Tool Execution",
            "pedagogical_purpose": "Proves that unnegotiated operations are blocked prior to dispatch, preventing state corruption.",
        },
        {
            "component": "Separate actionable rejection diagnostics",
            "lesson_concept": "Troubleshooting & Agent Error Handling Strategies",
            "pedagogical_purpose": "Provides distinct reasons for unnegotiated capability calls with actionable remediation.",
        },
        {
            "component": "Three-configuration benchmark comparison",
            "lesson_concept": "SLM Resource Constraints & Performance Optimization",
            "pedagogical_purpose": "Evaluates feature-set retention vs security surface trade-offs across controlled input sizes.",
        },
        {
            "component": "Offline read-only test fixtures",
            "lesson_concept": "Privacy-First Edge Deployments",
            "pedagogical_purpose": "Enforces safe, zero-side-effect assessment without external network dependencies.",
        },
    ]


def main() -> None:
    """CLI demonstration of capability negotiation, feature gating, and configuration comparison."""
    print("=" * 75)
    print("AI Agent Capability Negotiation & Feature Gating (Module06 R04-T059)")
    print("=" * 75)

    print("\n--- 1. Canonical Contract Demonstration ---")
    demo = demonstrate_canonical_contract()
    print("Client Capabilities:", demo["client_capabilities"])
    print("Server Capabilities:", demo["server_capabilities"])
    print("Negotiated Capabilities:", demo["negotiated_capabilities"])
    print("\nDispatching 'tools':")
    print(f"  Status: {demo['call_tools_result']['status']}")
    print(f"  Dispatched: {demo['call_tools_result']['dispatched']}")
    print("\nDispatching 'resources':")
    print(f"  Status: {demo['call_resources_result']['status']}")
    print(f"  Dispatched: {demo['call_resources_result']['dispatched']}")
    print(f"  Reason: {demo['call_resources_result']['reason']}")
    print("\nCanonical Contract Satisfied:", demo["canonical_contract_satisfied"])

    print("\n--- 2. Comparing Three Controlled Configurations ---")
    comparison = compare_configurations()
    for name, data in comparison["configurations"].items():
        print(f"\nConfiguration: {name}")
        print(f"  Description: {data['description']}")
        print(f"  Negotiated: {data['negotiation']['negotiated_capabilities']}")
        print(f"  Retention Ratio: {data['metrics']['capability_retention_ratio'] * 100:.1f}%")
        print(f"  Correctness Rate: {data['metrics']['correctness_rate'] * 100:.1f}%")
        print(f"  Permitted: {data['metrics']['permitted_dispatches']}/{data['metrics']['total_calls']}")
        print(f"  Rejected: {data['metrics']['rejected_dispatches']}/{data['metrics']['total_calls']}")

    print("\n--- 3. Trade-off Analysis ---")
    print("Security vs Flexibility:", comparison["trade_off_analysis"]["security_vs_flexibility"])
    print("Pre-Dispatch Gating Guarantee:", comparison["trade_off_analysis"]["pre_dispatch_gating_guarantee"])

    print("\n--- 4. Unestablished Real-Service Behaviors ---")
    for unest in identify_unestablished_behaviors():
        print(f"  * {unest}")


if __name__ == "__main__":
    main()
