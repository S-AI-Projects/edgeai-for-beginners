"""
R04-T011: Capability Negotiation - Runnable Concept Example
Companion applied lab for Module06/01.IntroduceAgent.md.

Demonstrates local/edge capability negotiation:
A client and a server each declare their supported capabilities.
Only the intersection of the two sets is negotiated for activation.
Any invocation of a capability that was not negotiated is rejected BEFORE dispatch.

Prerequisites: Python 3 standard library only.
"""

from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple


class NegotiationError(Exception):
    """Raised when capability validation, negotiation, or gated dispatch fails."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def validate_capability_set(caps: Any, param_name: str = "capability set") -> frozenset:
    """
    Validate that an input is a valid collection of capability identifiers.
    Rejects strings, mappings, non-iterables, None, and empty/non-string items.
    """
    if caps is None:
        raise NegotiationError("BAD_CAPABILITY_SET", f"{param_name} cannot be None.")
    if isinstance(caps, (str, bytes)):
        raise NegotiationError(
            "BAD_CAPABILITY_SET",
            f"{param_name} must be a collection of strings, not a bare string/bytes."
        )
    if isinstance(caps, dict):
        raise NegotiationError(
            "BAD_CAPABILITY_SET",
            f"{param_name} must be a set or list, not a dictionary."
        )
    if not isinstance(caps, (set, frozenset, list, tuple)):
        raise NegotiationError(
            "BAD_CAPABILITY_SET",
            f"{param_name} must be a set, frozenset, list, or tuple."
        )

    validated = set()
    for item in caps:
        if not isinstance(item, str) or not item.strip():
            raise NegotiationError(
                "BAD_CAPABILITY_SET",
                f"Capability identifier must be a non-empty string, got: {item!r}"
            )
        validated.add(item.strip())

    return frozenset(validated)


def negotiate_capabilities(client_caps: Any, server_caps: Any) -> frozenset:
    """
    Pure negotiation function:
    Validates client and server capability sets and returns their strict intersection.
    Does not mutate input collections.
    """
    client_set = validate_capability_set(client_caps, "client_caps")
    server_set = validate_capability_set(server_caps, "server_caps")
    return client_set & server_set


def invoke_baseline(
    client_caps: Any,
    server_caps: Any,
    capability: Any,
    payload: Any = None,
    handlers: Optional[Dict[str, Callable[[Any], Any]]] = None
) -> Any:
    """
    Baseline monolithic implementation:
    Performs validation, negotiation, pre-dispatch feature gating, and dispatch inline.
    """
    if not isinstance(capability, str) or not capability.strip():
        raise NegotiationError("BAD_REQUEST", f"Requested capability must be a non-empty string, got: {capability!r}")
    target_cap = capability.strip()

    client_set = validate_capability_set(client_caps, "client_caps")
    server_set = validate_capability_set(server_caps, "server_caps")
    negotiated = client_set & server_set

    # Pre-dispatch feature gate: must reject unnegotiated capabilities before handler dispatch
    if target_cap not in negotiated:
        raise NegotiationError("NOT_NEGOTIATED", f"Capability '{target_cap}' was not negotiated.")

    handlers_map = handlers or {}
    handler = handlers_map.get(target_cap)
    if handler is None:
        raise NegotiationError("NO_HANDLER", f"No handler registered for negotiated capability '{target_cap}'.")

    return handler(payload)


def invoke_refactored(
    client_caps: Any,
    server_caps: Any,
    capability: Any,
    payload: Any = None,
    handlers: Optional[Dict[str, Callable[[Any], Any]]] = None
) -> Any:
    """
    Refactored implementation:
    Delegates to the extracted pure negotiate_capabilities() function,
    enforcing pre-dispatch feature gating.
    """
    if not isinstance(capability, str) or not capability.strip():
        raise NegotiationError("BAD_REQUEST", f"Requested capability must be a non-empty string, got: {capability!r}")
    target_cap = capability.strip()

    negotiated = negotiate_capabilities(client_caps, server_caps)

    # Pre-dispatch gate
    if target_cap not in negotiated:
        raise NegotiationError("NOT_NEGOTIATED", f"Capability '{target_cap}' was not negotiated.")

    handlers_map = handlers or {}
    handler = handlers_map.get(target_cap)
    if handler is None:
        raise NegotiationError("NO_HANDLER", f"No handler registered for negotiated capability '{target_cap}'.")

    return handler(payload)


# Default canonical entry point alias
invoke_capability = invoke_refactored


def run_concept_example() -> Dict[str, Any]:
    """
    Executes the canonical task fixture:
      client: {tools, resources}
      server: {tools, prompts}
      negotiated: {tools}
    """
    client_caps = {"tools", "resources"}
    server_caps = {"tools", "prompts"}

    called_handlers = []

    def handle_tools(payload: Any) -> str:
        called_handlers.append("tools")
        return f"tools-handled:{payload}"

    def handle_resources(payload: Any) -> str:
        called_handlers.append("resources")
        return f"resources-handled:{payload}"

    handlers = {
        "tools": handle_tools,
        "resources": handle_resources,
    }

    negotiated = sorted(list(negotiate_capabilities(client_caps, server_caps)))

    # 1. Invoke negotiated capability 'tools'
    tools_result = invoke_capability(client_caps, server_caps, "tools", "ping", handlers)

    # 2. Attempt to invoke unnegotiated capability 'resources'
    resources_rejected = False
    resources_error_code = None
    try:
        invoke_capability(client_caps, server_caps, "resources", "read-config", handlers)
    except NegotiationError as exc:
        resources_rejected = True
        resources_error_code = exc.code

    return {
        "client_capabilities": sorted(list(client_caps)),
        "server_capabilities": sorted(list(server_caps)),
        "negotiated": negotiated,
        "tools_result": tools_result,
        "resources_rejected": resources_rejected,
        "resources_error_code": resources_error_code,
        "handlers_called": called_handlers,
    }


if __name__ == "__main__":
    result = run_concept_example()
    print("=== Capability Negotiation Example ===")
    print(f"Client capabilities: {result['client_capabilities']}")
    print(f"Server capabilities: {result['server_capabilities']}")
    print(f"Negotiated (active) capabilities: {result['negotiated']}")
    print(f"Invocation of 'tools': OK -> {result['tools_result']}")
    print(
        f"Invocation of 'resources': REJECTED -> code: {result['resources_error_code']}, "
        f"pre-dispatch rejection verified (handlers called: {result['handlers_called']})"
    )
