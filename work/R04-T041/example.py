"""R04-T041 - Optimization-stage ordering (OpenVINO lesson, Module04/04.openvino.md).

A tiny, fully local validator for an OpenVINO-style optimization plan.
It checks the plan BEFORE anything is executed (validation before execution):

  1. Stage order:   export  ->  quantize  ->  benchmark
  2. Provenance:    every stage lists the artifact IDs it reads and writes, and
                    every input must come from the starting artifacts or from an
                    EARLIER stage's output.

Nothing here runs OpenVINO, downloads a model or touches hardware. Stages are
plain data, so the example is a SIMULATION of plan checking only.
Standard library only (Python 3).
"""

from dataclasses import dataclass, field
from typing import List, Sequence, Set

# Canonical order taught in the lesson: export precedes quantize,
# quantize precedes benchmark.
STAGE_ORDER = ("export", "quantize", "benchmark")


class PlanError(ValueError):
    """Raised when an optimization plan is rejected. `code` names the rule."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class Stage:
    name: str
    inputs: Sequence[str] = field(default_factory=tuple)   # artifact IDs read
    outputs: Sequence[str] = field(default_factory=tuple)  # artifact IDs written


def validate_plan(plan: Sequence[Stage], starting_artifacts: Sequence[str]) -> List[str]:
    """Validate a plan. Return the accepted stage names, or raise PlanError.

    Inputs : plan               - ordered list of Stage objects
             starting_artifacts - artifact IDs that exist before stage 1
    Output : list of stage names in execution order (e.g. ["export", "quantize", "benchmark"])
    """
    if not plan:
        raise PlanError("EMPTY_PLAN", "a plan needs at least one stage")

    known: Set[str] = set(starting_artifacts)   # artifacts that exist so far
    last_rank = -1
    seen: Set[str] = set()

    for stage in plan:
        # --- ordering rules -------------------------------------------------
        if stage.name not in STAGE_ORDER:
            raise PlanError("UNKNOWN_STAGE", f"'{stage.name}' is not one of {STAGE_ORDER}")
        if stage.name in seen:
            raise PlanError("DUPLICATE_STAGE", f"'{stage.name}' appears more than once")
        rank = STAGE_ORDER.index(stage.name)
        if rank < last_rank:
            raise PlanError(
                "OUT_OF_ORDER",
                f"'{stage.name}' cannot come after '{STAGE_ORDER[last_rank]}'",
            )
        seen.add(stage.name)
        last_rank = rank

        # --- provenance rules -----------------------------------------------
        for artifact in stage.inputs:
            if artifact not in known:
                raise PlanError(
                    "UNKNOWN_ARTIFACT",
                    f"stage '{stage.name}' reads '{artifact}', which no earlier stage produced",
                )
        for artifact in stage.outputs:
            if artifact in known:
                raise PlanError(
                    "DUPLICATE_ARTIFACT",
                    f"stage '{stage.name}' re-creates artifact '{artifact}'",
                )
            known.add(artifact)

    return [stage.name for stage in plan]


# --- demo fixture (also used by the tests) -----------------------------------
STARTING_ARTIFACTS = ["source_model"]


def good_plan() -> List[Stage]:
    return [
        Stage("export", inputs=["source_model"], outputs=["ov_ir"]),
        Stage("quantize", inputs=["ov_ir"], outputs=["ov_int8"]),
        Stage("benchmark", inputs=["ov_int8"], outputs=["bench_report"]),
    ]


def main() -> None:
    print("starting artifacts:", STARTING_ARTIFACTS)
    cases = {
        "good plan": good_plan(),
        "benchmark before quantize": [
            Stage("export", ["source_model"], ["ov_ir"]),
            Stage("benchmark", ["ov_ir"], ["bench_report"]),
            Stage("quantize", ["ov_ir"], ["ov_int8"]),
        ],
        "unknown artifact": [
            Stage("export", ["source_model"], ["ov_ir"]),
            Stage("quantize", ["ov_int8_typo"], ["ov_int8"]),
        ],
    }
    for label, plan in cases.items():
        try:
            print(f"{label}: ACCEPTED {validate_plan(plan, STARTING_ARTIFACTS)}")
        except PlanError as err:
            print(f"{label}: REJECTED {err}")


if __name__ == "__main__":
    main()
