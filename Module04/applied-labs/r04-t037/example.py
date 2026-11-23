"""
Optimization-Stage Ordering and Artifact Provenance Validation.

Validates an Edge AI model optimization pipeline plan.
Enforces stage ordering constraints:
  - 'export' must precede 'quantize'
  - 'quantize' must precede 'benchmark'
Enforces artifact provenance:
  - Each stage specifies input and output artifact IDs.
  - Initial input artifact must be present in the initial environment.
  - Subsequent stages must reference artifact IDs produced by prior stages.
Rejects invalid orders (e.g. benchmark before quantize) and unknown artifact references.
"""

from typing import Dict, Any, List, Set, Tuple
import json


class PipelineValidationError(Exception):
    """Raised when an optimization plan violates stage ordering or artifact provenance."""
    def __init__(self, code: str, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "rejected",
            "error": {
                "code": "PIPELINE_VALIDATION_ERROR",
                "validation_code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


STAGE_ORDER_INDEX = {
    "export": 0,
    "quantize": 1,
    "benchmark": 2,
}


class OptimizationPlanValidator:
    """Validates optimization stage ordering and artifact lineage."""

    @staticmethod
    def validate_plan(plan: List[Dict[str, Any]], initial_artifacts: Set[str]) -> Dict[str, Any]:
        """
        Validates pipeline plan structure, stage order, and artifact lineage.
        Returns accepted summary or raises PipelineValidationError.
        """
        if not isinstance(plan, list) or len(plan) == 0:
            raise PipelineValidationError("EMPTY_PLAN", "Plan must be a non-empty list of stages")

        # 1. Stage ordering check
        stage_names = [s.get("stage") for s in plan]
        last_index = -1
        for stage in stage_names:
            if stage not in STAGE_ORDER_INDEX:
                raise PipelineValidationError(
                    "UNKNOWN_STAGE",
                    f"Unknown stage '{stage}'",
                    {"allowed_stages": list(STAGE_ORDER_INDEX.keys())}
                )
            current_index = STAGE_ORDER_INDEX[stage]
            if current_index <= last_index:
                raise PipelineValidationError(
                    "INVALID_STAGE_ORDER",
                    f"Invalid stage ordering: stage '{stage}' cannot follow prior stages in order {stage_names}",
                    {"stage": stage, "stage_sequence": stage_names}
                )
            last_index = current_index

        # 2. Artifact provenance check
        available_artifacts = set(initial_artifacts)
        lineage_trace: List[Dict[str, Any]] = []

        for stage_entry in plan:
            stage = stage_entry["stage"]
            input_art = stage_entry.get("input_artifact")
            output_art = stage_entry.get("output_artifact")

            if not input_art or not output_art:
                raise PipelineValidationError(
                    "MISSING_ARTIFACT_SPEC",
                    f"Stage '{stage}' must declare both 'input_artifact' and 'output_artifact'",
                    {"stage": stage}
                )

            if input_art not in available_artifacts:
                raise PipelineValidationError(
                    "UNKNOWN_ARTIFACT_REFERENCE",
                    f"Stage '{stage}' references unknown input artifact '{input_art}'. Available: {sorted(list(available_artifacts))}",
                    {"stage": stage, "missing_artifact": input_art, "available": sorted(list(available_artifacts))}
                )

            available_artifacts.add(output_art)
            lineage_trace.append({
                "stage": stage,
                "consumed": input_art,
                "produced": output_art,
            })

        return {
            "status": "accepted",
            "stages": stage_names,
            "lineage": lineage_trace,
            "final_artifacts": sorted(list(available_artifacts)),
        }


def run_demo() -> Dict[str, Any]:
    initial = {"model_raw"}

    # Canonical valid plan: export -> quantize -> benchmark
    valid_plan = [
        {"stage": "export", "input_artifact": "model_raw", "output_artifact": "model_onnx"},
        {"stage": "quantize", "input_artifact": "model_onnx", "output_artifact": "model_q4"},
        {"stage": "benchmark", "input_artifact": "model_q4", "output_artifact": "benchmark_report"},
    ]

    # Invalid order plan: export -> benchmark -> quantize
    invalid_order_plan = [
        {"stage": "export", "input_artifact": "model_raw", "output_artifact": "model_onnx"},
        {"stage": "benchmark", "input_artifact": "model_onnx", "output_artifact": "benchmark_report"},
        {"stage": "quantize", "input_artifact": "model_onnx", "output_artifact": "model_q4"},
    ]

    # Unknown artifact plan: references "ghost_model"
    unknown_art_plan = [
        {"stage": "export", "input_artifact": "ghost_model", "output_artifact": "model_onnx"},
        {"stage": "quantize", "input_artifact": "model_onnx", "output_artifact": "model_q4"},
        {"stage": "benchmark", "input_artifact": "model_q4", "output_artifact": "benchmark_report"},
    ]

    validator = OptimizationPlanValidator()

    results: Dict[str, Any] = {
        "valid_plan_result": validator.validate_plan(valid_plan, initial),
        "invalid_order_rejection": None,
        "unknown_artifact_rejection": None,
    }

    try:
        validator.validate_plan(invalid_order_plan, initial)
    except PipelineValidationError as e:
        results["invalid_order_rejection"] = e.to_dict()

    try:
        validator.validate_plan(unknown_art_plan, initial)
    except PipelineValidationError as e:
        results["unknown_artifact_rejection"] = e.to_dict()

    return results


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
