#!/usr/bin/env python3
"""
Optimization-Stage Ordering - Invariant and State Trace (R04-T004)
Module 04: Edge AI Development Workflow Synthesis

Concept:
In edge AI optimization workflows, models transition through discrete, ordered
stages: [export -> quantize -> benchmark]. Each stage consumes an upstream
artifact and produces a new artifact with a traceable ID. Out-of-order execution
(e.g., benchmarking before quantization) or referencing unknown/unregistered
artifacts must be rejected before triggering compute workloads.

Focus:
Records intermediate states after every step and verifies the provenance
invariant linking initial source artifacts to final benchmark outputs.
"""

from typing import List, Dict, Any, Optional

ALLOWED_ORDER = ["export", "quantize", "benchmark"]


class StagePlan:
    def __init__(self, name: str, input_artifact_id: str, output_artifact_id: str):
        self.name = name.lower().strip()
        self.input_artifact_id = input_artifact_id
        self.output_artifact_id = output_artifact_id

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "input_artifact_id": self.input_artifact_id,
            "output_artifact_id": self.output_artifact_id,
        }


class OptimizationWorkflowValidator:
    """
    Validates stage ordering and artifact lineage in an edge model optimization plan.
    """

    def __init__(self, initial_artifact_ids: Optional[List[str]] = None):
        self.initial_artifact_ids = set(initial_artifact_ids or ["source_model_v1"])

    def validate_plan(self, stages: List[StagePlan]) -> Dict[str, Any]:
        """
        Validates pipeline stage order and artifact dependencies step-by-step.
        Records intermediate state after each transition.
        """
        if not stages:
            raise ValueError("Optimization plan cannot be empty")

        available_artifacts = set(self.initial_artifact_ids)
        seen_stages: List[str] = []
        state_trace: List[Dict[str, Any]] = []

        # Record initial baseline state
        state_trace.append({
            "step": 0,
            "action": "INIT",
            "stage": None,
            "input_artifact": None,
            "output_artifact": None,
            "available_artifacts": sorted(list(available_artifacts)),
        })

        for idx, stage in enumerate(stages, start=1):
            stage_name = stage.name

            # 1. Enforce strict stage ordering
            if stage_name not in ALLOWED_ORDER:
                raise ValueError(f"Unknown optimization stage '{stage_name}'. Allowed: {ALLOWED_ORDER}")

            expected_idx = len(seen_stages)
            if expected_idx < len(ALLOWED_ORDER) and stage_name != ALLOWED_ORDER[expected_idx]:
                raise ValueError(
                    f"Invalid stage order: Cannot run '{stage_name}' at step {idx}. "
                    f"Expected '{ALLOWED_ORDER[expected_idx]}'."
                )

            # 2. Check artifact provenance (input must be known)
            if stage.input_artifact_id not in available_artifacts:
                raise ValueError(
                    f"Unknown artifact reference '{stage.input_artifact_id}' in stage '{stage_name}'. "
                    f"Available artifacts: {sorted(list(available_artifacts))}"
                )

            # 3. Register produced artifact
            available_artifacts.add(stage.output_artifact_id)
            seen_stages.append(stage_name)

            # 4. Record intermediate state snapshot
            state_trace.append({
                "step": idx,
                "action": f"EXEC_{stage_name.upper()}",
                "stage": stage_name,
                "input_artifact": stage.input_artifact_id,
                "output_artifact": stage.output_artifact_id,
                "available_artifacts": sorted(list(available_artifacts)),
            })

        # 5. Verify invariant: provenance chain connectivity
        is_connected = self._verify_provenance_invariant(stages)

        return {
            "valid": True,
            "completed_stages": seen_stages,
            "final_artifact": stages[-1].output_artifact_id,
            "state_trace": state_trace,
            "provenance_invariant_holds": is_connected,
            "simulation_note": "Local mock plan validator, does not invoke real compiler binaries or GPU kernels",
        }

    def _verify_provenance_invariant(self, stages: List[StagePlan]) -> bool:
        """
        Verifies that every stage's output connects to the subsequent stage's input,
        starting from an initial registered artifact.
        """
        if not stages:
            return False

        if stages[0].input_artifact_id not in self.initial_artifact_ids:
            return False

        for i in range(len(stages) - 1):
            if stages[i].output_artifact_id != stages[i + 1].input_artifact_id:
                return False

        return True


def run_demo() -> None:
    print("=== Module 04: Edge AI Optimization Stage Ordering Demo ===")
    validator = OptimizationWorkflowValidator(initial_artifact_ids=["onnx_fp32_base"])

    valid_plan = [
        StagePlan("export", "onnx_fp32_base", "exported_graph"),
        StagePlan("quantize", "exported_graph", "quantized_int8"),
        StagePlan("benchmark", "quantized_int8", "benchmark_metrics"),
    ]

    result = validator.validate_plan(valid_plan)
    print("Optimization plan accepted:", result["valid"])
    print(f"Final Artifact: {result['final_artifact']}")
    print("State Trace Progression:")
    for step in result["state_trace"]:
        print(f"  Step {step['step']} ({step['action']}): artifacts = {step['available_artifacts']}")


if __name__ == "__main__":
    run_demo()
