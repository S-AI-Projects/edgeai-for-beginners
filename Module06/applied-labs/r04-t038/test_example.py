"""
Unit tests for Bounded Conversation Memory and Evaluation Experiment.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import BoundedConversationMemory, evaluate_memory_capacities, run_demo


class TestBoundedConversationMemory(unittest.TestCase):

    def test_adding_abcd_retains_bcd(self):
        """Adding records A,B,C,D retains B,C,D in arrival order."""
        mem = BoundedConversationMemory(capacity=3)
        for letter in ["A", "B", "C", "D"]:
            mem.add_record({"id": letter})

        records = mem.get_records()
        self.assertEqual(len(records), 3)
        self.assertEqual([r["id"] for r in records], ["B", "C", "D"])

    def test_caller_mutation_isolation(self):
        """Mutating the returned list does not alter stored memory."""
        mem = BoundedConversationMemory(capacity=3)
        mem.add_record({"id": "A"})
        mem.add_record({"id": "B"})

        exposed = mem.get_records()
        exposed.append({"id": "INJECTED"})
        exposed[0]["id"] = "CORRUPTED"

        # Stored memory must remain untainted
        fresh = mem.get_records()
        self.assertEqual(len(fresh), 2)
        self.assertEqual([r["id"] for r in fresh], ["A", "B"])

    def test_evaluation_experiment_metrics(self):
        """Compare 3 controlled configurations (cap 2, 3, 5) on a 6-item stream."""
        stream = [{"id": f"item_{i}"} for i in range(6)]
        eval_res = evaluate_memory_capacities([2, 3, 5], stream)

        self.assertEqual(eval_res["capacity_2"]["retained_count"], 2)
        self.assertEqual(eval_res["capacity_2"]["evicted_count"], 4)
        self.assertTrue(eval_res["capacity_2"]["mutation_safe"])

        self.assertEqual(eval_res["capacity_3"]["retained_count"], 3)
        self.assertEqual(eval_res["capacity_3"]["evicted_count"], 3)

        self.assertEqual(eval_res["capacity_5"]["retained_count"], 5)
        self.assertEqual(eval_res["capacity_5"]["evicted_count"], 1)

    def test_deliberate_wrong_result_fails(self):
        """Deliberate wrong assertion fails."""
        mem = BoundedConversationMemory(capacity=3)
        for letter in ["A", "B", "C", "D"]:
            mem.add_record({"id": letter})
        self.assertNotEqual([r["id"] for r in mem.get_records()], ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
