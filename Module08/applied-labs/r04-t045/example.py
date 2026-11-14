"""R04-T045 - Capability negotiation: refactor the teaching example
(Module08/04.CuttingEdgeModels.md, "Session 4: Building Production Chat Applications with Chainlit").

Contract (small and local):
  * A client and a server each declare a set of capability names.
  * NEGOTIATE = the intersection of the two sets.
  * Invoking a capability that was NOT negotiated is rejected BEFORE dispatch: the server
    handler is never called.
  * Fixture from the task: client {tools, resources}, server {tools, prompts}
    negotiates {tools}; calling `resources` (or `prompts`) is rejected.

Focus - refactor with the same contract:
  * invoke_baseline()   - a correct baseline: validate, negotiate, gate and dispatch all
                          inline in one function.
  * invoke_refactored() - the same behaviour, with ONE named responsibility extracted:
                          negotiate_capabilities() (validate both sets, return the intersection).
  * equivalence_report() proves before/after equivalence: it runs both versions on the task
    fixture and on every combination of a small capability universe and compares the outcome
    AND which handlers were called.

SIMULATION ONLY: the capability names are labels taken from the task fixture. There is no
network, handshake, protocol version or real client/server here, and nothing claims what any
real Chainlit, Foundry Local or WebGPU setup supports. Standard library only (Python 3).
"""

from itertools import combinations
from typing import Callable, Iterable, List, Mapping, Sequence, Tuple

CAPABILITIES = ("tools", "resources", "prompts")


class NegotiationError(Exception):
    """Raised when input or a request is rejected. `code` names the rule."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


Handler = Callable[[object], object]


# --- 1. the correct baseline: everything inline ---------------------------------
def invoke_baseline(client_caps, server_caps, capability, payload,
                    handlers: Mapping[str, Handler]):
    for name, caps in (("client", client_caps), ("server", server_caps)):
        if isinstance(caps, (str, bytes)) or not isinstance(caps, (set, frozenset, list, tuple)):
            raise NegotiationError(
                "BAD_CAPABILITY_SET", f"{name} capabilities must be a set, list or tuple of names"
            )
        if any(not isinstance(c, str) or not c for c in caps):
            raise NegotiationError(
                "BAD_CAPABILITY_SET", f"{name} capabilities must all be non-empty strings"
            )
    if not isinstance(capability, str) or not capability:
        raise NegotiationError("BAD_REQUEST", "the requested capability must be a non-empty string")

    negotiated = set(client_caps) & set(server_caps)

    if capability not in negotiated:  # gate: reject before any handler is looked up or called
        raise NegotiationError("NOT_NEGOTIATED", f"'{capability}' was not negotiated")

    handler = handlers.get(capability)
    if handler is None:
        raise NegotiationError("NO_HANDLER", f"no handler registered for '{capability}'")
    return handler(payload)


# --- 2. the refactor: one named responsibility extracted ------------------------
def negotiate_capabilities(client_caps, server_caps) -> frozenset:
    """Validate both capability sets and return what they have in common."""
    for name, caps in (("client", client_caps), ("server", server_caps)):
        if isinstance(caps, (str, bytes)) or not isinstance(caps, (set, frozenset, list, tuple)):
            raise NegotiationError(
                "BAD_CAPABILITY_SET", f"{name} capabilities must be a set, list or tuple of names"
            )
        if any(not isinstance(c, str) or not c for c in caps):
            raise NegotiationError(
                "BAD_CAPABILITY_SET", f"{name} capabilities must all be non-empty strings"
            )
    return frozenset(client_caps) & frozenset(server_caps)


def invoke_refactored(client_caps, server_caps, capability, payload,
                      handlers: Mapping[str, Handler]):
    negotiated = negotiate_capabilities(client_caps, server_caps)
    if not isinstance(capability, str) or not capability:
        raise NegotiationError("BAD_REQUEST", "the requested capability must be a non-empty string")
    if capability not in negotiated:
        raise NegotiationError("NOT_NEGOTIATED", f"'{capability}' was not negotiated")
    handler = handlers.get(capability)
    if handler is None:
        raise NegotiationError("NO_HANDLER", f"no handler registered for '{capability}'")
    return handler(payload)


# --- 3. proving before/after equivalence ----------------------------------------
def make_handlers(names: Iterable[str], log: List[str]) -> dict:
    """Handlers that record that they were called, so 'rejected before dispatch' is checkable."""
    def make(name: str) -> Handler:
        def handler(payload):
            log.append(name)
            return f"{name}-handled:{payload}"
        return handler
    return {name: make(name) for name in names}


def run_case(impl, client, server, capability, handler_names, payload="ping") -> Tuple:
    """Return (kind, value, handler_calls): the outcome plus which handlers actually ran."""
    log: List[str] = []
    handlers = make_handlers(handler_names, log)
    try:
        result = impl(client, server, capability, payload, handlers)
        return ("ok", result, tuple(log))
    except NegotiationError as err:
        return ("error", err.code, tuple(log))


def _subsets(items: Sequence[str]):
    for size in range(len(items) + 1):
        for combo in combinations(items, size):
            yield set(combo)


def equivalence_report(impl_a=invoke_baseline, impl_b=invoke_refactored) -> Tuple[int, List[Tuple]]:
    """Run both implementations on every generated case. Return (cases checked, mismatches)."""
    checked, mismatches = 0, []
    requests = CAPABILITIES + ("unknown",)
    for client in _subsets(CAPABILITIES):
        for server in _subsets(CAPABILITIES):
            for capability in requests:
                for handler_names in (CAPABILITIES, ("tools",)):
                    a = run_case(impl_a, client, server, capability, handler_names)
                    b = run_case(impl_b, client, server, capability, handler_names)
                    checked += 1
                    if a != b:
                        mismatches.append((sorted(client), sorted(server), capability, a, b))
    return checked, mismatches


# --- demo fixture (also used by the tests) --------------------------------------
CLIENT_CAPS = {"tools", "resources"}
SERVER_CAPS = {"tools", "prompts"}


def main() -> None:
    print("client capabilities:", sorted(CLIENT_CAPS))
    print("server capabilities:", sorted(SERVER_CAPS))
    print("negotiated:", sorted(negotiate_capabilities(CLIENT_CAPS, SERVER_CAPS)))
    same = True
    for capability in ("tools", "resources", "prompts"):
        before = run_case(invoke_baseline, CLIENT_CAPS, SERVER_CAPS, capability, CAPABILITIES)
        after = run_case(invoke_refactored, CLIENT_CAPS, SERVER_CAPS, capability, CAPABILITIES)
        same = same and before == after
        kind, value, calls = after
        shown = f"OK {value!r}" if kind == "ok" else f"REJECTED {value}"
        print(f"  invoke {capability}: {shown} (handler calls: {list(calls)})")
    print("baseline vs refactored on the fixture:", "identical outcomes" if same else "DIFFERENT")
    checked, mismatches = equivalence_report()
    print(f"baseline vs refactored on all {checked} generated cases: {len(mismatches)} mismatches")
    print("note: capability names are labels; this is a simulation, not a real client/server.")


if __name__ == "__main__":
    main()
