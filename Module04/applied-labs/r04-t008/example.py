#!/usr/bin/env python3
"""
Optimization-Stage Ordering - Failure and Recovery Example (R04-T008)
Module 04: Microsoft Olive Optimization Suite

Concept:
Microsoft Olive automates model optimization via configurable passes:
[export -> quantize -> benchmark]. In automated MLOps pipelines, submitting
invalid configurations (such as benchmark before quantize, or missing input
artifacts) must halt the pipeline safely with detailed diagnostic errors,
allowing immediate remediation and recovery without corrupting runtime state.

Focus:
Exercises a documented invalid/missing-data case, explains the diagnostic error,
and demonstrates complete recovery on the next valid plan.
"""

from typing import List, Dict, Any, Optional

VALID_STAGE_ORDER = ["export", "quantize", "benchmark"]


class OptimizationWorkflowError(Exception):
    """Custom error raised when optimization plan validation fails."""
    pass


class OliveStage:
    def __init__(self, name: str, input_artifact_id: str, output_artifact_id: str):
        self.name = name.lower().strip()
        self.input_artifact_id = input_artifact_id
        self.output_artifact_id = output_artifact_id


class OliveWorkflowValidator:
    """
    Validates Microsoft Olive optimization plans with explicit failure reporting
    and robust session recovery.
    """

    def __init__(self, registered_artifacts: Optional[List[str]] = None):
        self.base_artifacts = set(registered_artifacts or ["olive_source_model"])

    def validate_plan(self, stages: List[OliveStage]) -> Dict[str, Any]:
        """
        Validates the sequence of Olive optimization passes.
        Raises OptimizationWorkflowError on order violations or unknown artifacts.
        """
        if not stages:
            raise OptimizationWorkflowError("Optimization plan cannot be empty.")

        available = set(self.base_artifacts)
        executed_stages: List[str] = []

        for idx, stage in enumerate(stages, start=1):
            # 1. Enforce stage sequence [export -> quantize -> benchmark]
            if stage.name not in VALID_STAGE_ORDER:
                raise OptimizationWorkflowError(
                    f"Unknown stage '{stage.name}'. Allowed passes: {VALID_STAGE_ORDER}."
                )

            expected_idx = len(executed_stages)
            if expected_idx < len(VALID_STAGE_ORDER) and stage.name != VALID_STAGE_ORDER[expected_idx]:
                raise OptimizationWorkflowError(
                    f"Invalid stage ordering at step {idx}: Cannot execute '{stage.name}'. "
                    f"Expected '{VALID_STAGE_ORDER[expected_idx]}'. (Benchmark cannot precede quantize)."
                )

            # 2. Check input artifact provenance
            if stage.input_artifact_id not in available:
                raise OptimizationWorkflowError(
                    f"Unknown artifact reference '{stage.input_artifact_id}' in pass '{stage.name}'. "
                    f"Available artifacts: {sorted(list(available))}."
                )

            # 3. Register output artifact
            available.add(stage.output_artifact_id)
            executed_stages.append(stage.name)

        return {
            "valid": True,
            "completed_stages": executed_stages,
            "final_artifact": stages[-1].output_artifact_id,
            "all_available_artifacts": sorted(list(available)),
            "simulation_note": "Mock validation of Olive configuration graph; no actual model conversion performed.",
        }


def run_failure_and_recovery_demo() -> None:
    print("=== Module 04: Microsoft Olive Pipeline Failure & Recovery Demo ===")
    validator = OliveWorkflowValidator(registered_artifacts=["phi_base_model"])

    # 1. Faulty Plan: Attempt benchmark before quantize
    faulty_plan = [
        OliveStage("export", "phi_base_model", "phi_onnx"),
        OliveStage("benchmark", "phi_onnx", "premature_metrics"),
        OliveStage("quantize", "phi_onnx", "phi_int4"),
    ]

    print("\n[Step 1] Executing faulty plan (benchmark before quantize)...")
    try:
        validator.validate_plan(faulty_plan)
        print("UNEXPECTED: Faulty plan succeeded.")
    except OptimizationWorkflowError as err:
        print(f"EXPECTED FAILURE CAUGHT: {err}")
        print("DIAGNOSIS: The benchmark pass was requested before model quantization was complete.")

    # 2. Recovered Plan: Corrected order [export, quantize, benchmark]
    recovered_plan = [
        OliveStage("export", "phi_base_model", "phi_onnx"),
        OliveStage("quantize", "phi_onnx", "phi_int4"),
        OliveStage("benchmark", "phi_int4", "validated_metrics"),
    ]

    print("\n[Step 2] Executing corrected plan on the same validator instance...")
    result = validator.validate_plan(recovered_plan)
    print(f"RECOVERY SUCCESS: Valid = {result['valid']}")
    print(f"Completed Stages: {result['completed_stages']}")
    print(f"Final Artifact: {result['final_artifact']}")


if __name__ == "__main__":
    run_failure_and_recovery_demo()
