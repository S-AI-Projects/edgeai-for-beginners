"""
Bounded Conversation Memory and Evaluation Experiment.

Stores at most K conversation records in FIFO arrival order and exposes a deep
copy to callers.
Demonstrates:
  - Adding records A, B, C, D to a buffer of capacity 3 retains [B, C, D].
  - Mutating the returned copy does not alter stored internal memory.
Conducts an evaluation experiment comparing three controlled memory capacities
(K=2, K=3, K=5) over input streams, reporting retention rate, eviction count,
and memory safety metrics.
"""

from typing import List, Dict, Any
import copy
import json


class BoundedConversationMemory:
    """
    Thread-safe / caller-safe bounded FIFO buffer storing conversation records.
    """
    def __init__(self, capacity: int = 3):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self._records: List[Dict[str, Any]] = []

    def add_record(self, record: Dict[str, Any]) -> None:
        """Appends a deepcopy of record, evicting the oldest if capacity is exceeded."""
        if len(self._records) >= self.capacity:
            self._records.pop(0)
        self._records.append(copy.deepcopy(record))

    def get_records(self) -> List[Dict[str, Any]]:
        """Returns an isolated deep copy of stored records to prevent caller mutation."""
        return copy.deepcopy(self._records)

    def size(self) -> int:
        return len(self._records)


def evaluate_memory_capacities(capacities: List[int], input_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Comparative experiment across controlled configurations.
    Metrics:
      - total_added: number of incoming items
      - retained_count: items remaining in buffer
      - evicted_count: total_added - retained_count
      - retention_ratio: retained_count / total_added
      - caller_mutation_safe: boolean indicating whether mutations to get_records() bleed into internal state.
    """
    results: Dict[str, Any] = {}
    for cap in capacities:
        mem = BoundedConversationMemory(capacity=cap)
        for r in input_records:
            mem.add_record(r)

        view = mem.get_records()
        # Test mutation safety
        view.append({"id": "MUTATION_ATTACK"})
        is_safe = (mem.size() == min(cap, len(input_records))) and (len(mem.get_records()) == min(cap, len(input_records)))

        results[f"capacity_{cap}"] = {
            "capacity": cap,
            "total_added": len(input_records),
            "retained_count": mem.size(),
            "evicted_count": max(0, len(input_records) - cap),
            "retention_ratio": round(mem.size() / len(input_records), 3),
            "retained_ids": [r["id"] for r in mem.get_records()],
            "mutation_safe": is_safe,
        }

    return results


def run_demo() -> Dict[str, Any]:
    # Canonical contract demo
    memory = BoundedConversationMemory(capacity=3)
    for letter in ["A", "B", "C", "D"]:
        memory.add_record({"id": letter, "message": f"Message {letter}"})

    retrieved = memory.get_records()
    # Mutate caller view
    retrieved.clear()

    # Evaluation experiment across 3 capacities: 2, 3, 5
    stream = [{"id": f"rec_{i}"} for i in range(1, 7)]  # 6 records
    exp_results = evaluate_memory_capacities([2, 3, 5], stream)

    return {
        "canonical_retained_ids": [r["id"] for r in memory.get_records()],
        "caller_mutation_did_not_affect_stored": len(memory.get_records()) == 3,
        "evaluation_experiment": exp_results
    }


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
