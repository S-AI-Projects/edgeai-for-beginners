"""
Model-Manifest Selection with Invariant and State Trace.

Evaluates entries from a synthetic local model manifest against available
RAM budget and requested context window length.
Maintains an explicit intermediate state trace recording evaluation steps,
failure reasons for excluded models, and invariants linking trace to output.
"""

from typing import Dict, Any, List, Optional
import json


class ManifestSelector:
    """Selects eligible model entries based on RAM and context limits."""

    def __init__(self, manifest: List[Dict[str, Any]]):
        self.manifest = manifest

    def select(self, available_ram_gb: float, requested_context: int) -> Dict[str, Any]:
        """
        Filters models by checking:
        1. required_ram_gb <= available_ram_gb
        2. max_context >= requested_context

        Traces state after evaluating each candidate.
        """
        trace: List[Dict[str, Any]] = []
        eligible: List[Dict[str, Any]] = []
        excluded: List[Dict[str, Any]] = []

        for entry in self.manifest:
            step_state: Dict[str, Any] = {
                "model_id": entry["id"],
                "required_ram_gb": entry["required_ram_gb"],
                "max_context": entry["max_context"],
                "eval_ram": entry["required_ram_gb"] <= available_ram_gb,
                "eval_context": entry["max_context"] >= requested_context,
            }

            reasons = []
            if not step_state["eval_ram"]:
                reasons.append(
                    f"Insufficient RAM: required {entry['required_ram_gb']}GB exceeds budget {available_ram_gb}GB"
                )
            if not step_state["eval_context"]:
                reasons.append(
                    f"Insufficient context window: model supports {entry['max_context']}, requested {requested_context}"
                )

            is_eligible = step_state["eval_ram"] and step_state["eval_context"]
            step_state["eligible"] = is_eligible
            step_state["reasons"] = reasons

            trace.append(step_state)

            if is_eligible:
                eligible.append(entry)
            else:
                excluded.append({
                    "model_id": entry["id"],
                    "reasons": reasons
                })

        return {
            "inputs": {
                "available_ram_gb": available_ram_gb,
                "requested_context": requested_context
            },
            "eligible": eligible,
            "excluded": excluded,
            "trace": trace
        }


def run_demo() -> Dict[str, Any]:
    manifest = [
        {"id": "Fixture-A", "required_ram_gb": 4, "max_context": 2048},
        {"id": "Fixture-B", "required_ram_gb": 8, "max_context": 4096},
    ]
    selector = ManifestSelector(manifest)
    # Budget RAM 6GB and requested context 1024 admits only A
    return selector.select(available_ram_gb=6, requested_context=1024)


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
