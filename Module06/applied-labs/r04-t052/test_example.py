#!/usr/bin/env python3
"""
Unit tests for Bounded Conversation Memory (R04-T052)
Module 06: Model Context Protocol (MCP) Integration (03.IntroduceMCP.md)
"""

import unittest
from example import BoundedConversationMemory, explain_mapping


class TestBoundedConversationMemory(unittest.TestCase):
    """Test suite verifying contract compliance of BoundedConversationMemory."""

    def setUp(self) -> None:
        """Initialize standard memory fixture with default capacity of 3."""
        self.memory = BoundedConversationMemory(capacity=3)

    # -----------------------------------------------------------------
    # Primary Contract Verification
    # -----------------------------------------------------------------
    def test_adding_records_a_b_c_d_retains_b_c_d(self) -> None:
        """Adding records A,B,C,D retains B,C,D in arrival order."""
        res_a = self.memory.add_record("A")
        self.assertIsNone(res_a["evicted"])
        self.assertEqual(self.memory.get_records(), ["A"])

        res_b = self.memory.add_record("B")
        self.assertIsNone(res_b["evicted"])
        self.assertEqual(self.memory.get_records(), ["A", "B"])

        res_c = self.memory.add_record("C")
        self.assertIsNone(res_c["evicted"])
        self.assertEqual(self.memory.get_records(), ["A", "B", "C"])

        res_d = self.memory.add_record("D")
        self.assertEqual(res_d["evicted"], "A")
        self.assertTrue(res_d["truncated"])

        records = self.memory.get_records()
        self.assertEqual(records, ["B", "C", "D"])
        self.assertEqual(len(self.memory), 3)

    def test_mutating_returned_list_does_not_alter_stored_memory(self) -> None:
        """Mutating the returned list does not alter stored internal memory."""
        self.memory.add_record("A")
        self.memory.add_record("B")
        self.memory.add_record("C")
        self.memory.add_record("D")

        # Fetch copy
        exposed = self.memory.get_records()
        self.assertEqual(exposed, ["B", "C", "D"])

        # Attempt diverse mutations on the returned list
        exposed.append("MUTATED_EXTRA")
        exposed.pop(0)
        exposed.clear()

        # Verify internal state remains completely untouched
        stored = self.memory.get_records()
        self.assertEqual(stored, ["B", "C", "D"])
        self.assertEqual(len(self.memory), 3)

    # -----------------------------------------------------------------
    # Smallest Valid and Boundary Cases
    # -----------------------------------------------------------------
    def test_smallest_valid_empty_memory(self) -> None:
        """Empty memory returns an empty list and reports zero length."""
        self.assertEqual(len(self.memory), 0)
        self.assertEqual(self.memory.get_records(), [])

    def test_smallest_valid_single_addition(self) -> None:
        """Adding a single record to fresh memory stores only that record."""
        res = self.memory.add_record("A")
        self.assertEqual(self.memory.get_records(), ["A"])
        self.assertIsNone(res["evicted"])
        self.assertEqual(len(self.memory), 1)

    def test_smallest_valid_capacity_one(self) -> None:
        """Memory configured with minimum capacity=1 retains only the most recent entry."""
        mem1 = BoundedConversationMemory(capacity=1)
        mem1.add_record("FIRST")
        self.assertEqual(mem1.get_records(), ["FIRST"])

        res = mem1.add_record("SECOND")
        self.assertEqual(res["evicted"], "FIRST")
        self.assertEqual(mem1.get_records(), ["SECOND"])

    def test_exact_capacity_boundary(self) -> None:
        """Adding exactly 3 records fills capacity without any eviction."""
        self.memory.add_record("A")
        self.memory.add_record("B")
        res = self.memory.add_record("C")
        self.assertIsNone(res["evicted"])
        self.assertFalse(res["truncated"])
        self.assertEqual(self.memory.get_records(), ["A", "B", "C"])
        self.assertEqual(len(self.memory), 3)

    def test_continuous_overflow_eviction(self) -> None:
        """Adding 5 records (A, B, C, D, E) sequentially evicts A then B, retaining C, D, E."""
        for item in ["A", "B", "C", "D", "E"]:
            self.memory.add_record(item)
        self.assertEqual(self.memory.get_records(), ["C", "D", "E"])

    # -----------------------------------------------------------------
    # Invalid Cases and Error Handling
    # -----------------------------------------------------------------
    def test_invalid_capacity_rejected(self) -> None:
        """Zero or negative capacities must raise ValueError."""
        with self.assertRaises(ValueError) as ctx_zero:
            BoundedConversationMemory(capacity=0)
        self.assertIn("positive integer", str(ctx_zero.exception))

        with self.assertRaises(ValueError) as ctx_neg:
            BoundedConversationMemory(capacity=-3)
        self.assertIn("positive integer", str(ctx_neg.exception))

    def test_invalid_records_rejected(self) -> None:
        """Adding None or empty whitespace strings must raise ValueError."""
        with self.assertRaises(ValueError):
            self.memory.add_record(None)

        with self.assertRaises(ValueError):
            self.memory.add_record("")

        with self.assertRaises(ValueError):
            self.memory.add_record("   \t\n  ")

    # -----------------------------------------------------------------
    # Deep Immutability for Complex / Structured Dict Records
    # -----------------------------------------------------------------
    def test_dict_record_deep_isolation(self) -> None:
        """Mutating a dict inside the returned list does not alter internal state."""
        msg1 = {"role": "user", "text": "What is MCP?"}
        msg2 = {"role": "assistant", "text": "MCP is Model Context Protocol."}
        self.memory.add_record(msg1)
        self.memory.add_record(msg2)

        records = self.memory.get_records()
        records[0]["text"] = "CORRUPTED_IN_PLACE"

        # Verify internal copy was not corrupted
        pristine = self.memory.get_records()
        self.assertEqual(pristine[0]["text"], "What is MCP?")

    # -----------------------------------------------------------------
    # Boundary Decision Explanation and Mapping
    # -----------------------------------------------------------------
    def test_boundary_decision_structure(self) -> None:
        """Boundary decision metadata explicitly documents the FIFO sliding window policy."""
        info = self.memory.get_boundary_decision()
        self.assertEqual(info["policy"], "FIFO_SLIDING_WINDOW")
        self.assertEqual(info["capacity"], 3)
        self.assertIn("capacity (3)", info["boundary_rule"])
        self.assertIn("deep copies", info["ownership_rule"])

    def test_concept_mapping_coverage(self) -> None:
        """Ensure all primary memory lifecycle actions map to MCP concepts."""
        mapping = explain_mapping()
        for key in ["capacity", "add_record", "evicted", "retained_count", "get_records", "boundary_decision"]:
            self.assertIn(key, mapping)


if __name__ == "__main__":
    unittest.main()
