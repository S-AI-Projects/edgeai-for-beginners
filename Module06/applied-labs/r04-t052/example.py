#!/usr/bin/env python3
"""
Bounded Conversation Memory - Boundary-Case Lesson Extension (R04-T052)
Module 06: Model Context Protocol (MCP) Integration (03.IntroduceMCP.md)

Concept:
In Model Context Protocol (MCP) host-client architectures, AI agents exchange
conversational turns, tool calls, and external resource states. On resource-constrained
edge devices, an unbounded conversation history quickly saturates the SLM context
window (e.g., Phi-4-mini's context limit) and consumes excessive runtime memory.
A bounded conversation memory enforces an explicit retention policy (FIFO sliding window)
and returns isolated defensive copies so external callers cannot inadvertently mutate
the agent's internal state.

Focus:
Implement a deterministic local fixture storing at most three conversation records in
arrival order, expose copies to callers, and emphasize smallest valid, boundary, and
invalid cases with explicit boundary decision rationales.

Pedagogical Notice:
This local fixture demonstrates bounded memory retention and ownership isolation.
It does not require external MCP servers, network transports (STDIO/HTTP), or physical
hardware/SLM weights.
"""

import copy
from typing import Any, Dict, List, Optional


class BoundedConversationMemory:
    """Stores a bounded number of conversation records in arrival order with defensive copying."""

    DEFAULT_CAPACITY: int = 3

    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        """Initialize the bounded memory with a maximum record capacity.

        Args:
            capacity: Maximum number of conversation records to retain (default: 3).

        Raises:
            ValueError: If capacity is less than 1.
        """
        if capacity < 1:
            raise ValueError(f"Capacity must be a positive integer >= 1, got: {capacity}")
        self._capacity: int = capacity
        self._records: List[Any] = []

    @property
    def capacity(self) -> int:
        """Maximum record capacity."""
        return self._capacity

    def __len__(self) -> int:
        """Return the current number of stored records."""
        return len(self._records)

    def add_record(self, record: Any) -> Dict[str, Any]:
        """Add a conversation record to the buffer in arrival order.

        If the buffer is full (reaches capacity), the oldest record is evicted (FIFO).

        Args:
            record: The conversation record to store (cannot be None or empty string).

        Returns:
            Dictionary detailing the admission operation and eviction telemetry.

        Raises:
            ValueError: If record is None or empty.
        """
        if record is None:
            raise ValueError("Record cannot be None")
        if isinstance(record, str) and not record.strip():
            raise ValueError("Record cannot be empty or whitespace-only string")

        evicted: Optional[Any] = None
        if len(self._records) >= self._capacity:
            evicted = self._records.pop(0)

        # Store deepcopy internally to protect against external pre-mutation
        self._records.append(copy.deepcopy(record))

        return {
            "record": record,
            "evicted": evicted,
            "retained_count": len(self._records),
            "capacity": self._capacity,
            "truncated": evicted is not None,
        }

    def add(self, record: Any) -> Dict[str, Any]:
        """Alias for add_record."""
        return self.add_record(record)

    def get_records(self) -> List[Any]:
        """Expose a copy of the stored conversation records in arrival order.

        Callers receive an isolated deep copy; mutating the returned list or
        its contents will not modify the internal state of this memory buffer.

        Returns:
            List of conversation records in arrival order (oldest to newest).
        """
        return copy.deepcopy(self._records)

    def get_boundary_decision(self) -> Dict[str, Any]:
        """Explain the exact boundary decision policy and ownership guarantees."""
        return {
            "policy": "FIFO_SLIDING_WINDOW",
            "capacity": self._capacity,
            "boundary_rule": (
                f"When stored record count reaches capacity ({self._capacity}), "
                "adding a new record evicts the oldest entry (index 0). "
                "This guarantees at most 3 items in arrival order with deterministic O(1) buffer bounds."
            ),
            "ownership_rule": (
                "Callers receive deep copies from get_records(). Mutating the returned list "
                "(append, pop, clear, or item reassignment) has zero effect on stored memory."
            ),
            "lesson_concept": "MCP session context governance for memory-constrained SLMs",
        }


def explain_mapping() -> Dict[str, str]:
    """Map public memory inputs and outputs to MCP integration lesson concepts."""
    return {
        "capacity": "Configured context turn budget preventing SLM context overflow in MCP sessions",
        "add_record": "Admission of new user prompt, agent turn, or MCP tool response",
        "evicted": "Oldest conversational turn pruned under FIFO retention policy",
        "retained_count": "Current conversational depth maintained in working memory",
        "get_records": "Context history supplied to MCP prompts/tools, isolated via defensive copying",
        "boundary_decision": "Deterministic policy defining exact retention when capacity is reached",
    }


def main() -> None:
    """Run CLI demonstration of bounded conversation memory."""
    print("=" * 70)
    print("Bounded Conversation Memory - MCP Integration (R04-T052)")
    print("=" * 70)

    memory = BoundedConversationMemory(capacity=3)

    print("\n1. Sequential Additions (A, B, C, D):")
    for item in ["A", "B", "C", "D"]:
        res = memory.add_record(item)
        print(f"   Added {item!r} -> Stored: {memory.get_records()} (Evicted: {res['evicted']!r})")

    print("\n2. Verification of Immutability / Defensive Copy:")
    records = memory.get_records()
    print(f"   Exposed records: {records}")
    print("   Mutating returned list: records.append('TAMPERED'), records.pop(0)...")
    records.append("TAMPERED")
    records.pop(0)
    print(f"   Mutated local list:   {records}")
    print(f"   Internal memory state: {memory.get_records()} (UNCHANGED)")

    print("\n3. Boundary Decision Details:")
    for k, v in memory.get_boundary_decision().items():
        print(f"   {k}: {v}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
