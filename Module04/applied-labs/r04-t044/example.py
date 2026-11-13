"""R04-T044 - Optimization-stage ordering: offline service adapter
(Module04/04.openvino.md, "Section 4 : OpenVINO Toolkit Optimization Suite").

Contract (small and local):
  * A plan is a list of stages. Each stage records the artifact IDs it READS (inputs) and
    WRITES (outputs).
  * Stage order is export -> quantize -> benchmark. [export, quantize, benchmark] is
    accepted; benchmark before quantize is rejected; an input that no earlier stage
    produced (an unknown artifact reference) is rejected.
  * The plan is validated BEFORE anything runs (validation before execution).

Focus - the external dependency behind a callable interface:
  * The real optimization work (OpenVINO export, NNCF quantization, a timed benchmark)
    would live in an external service. Here it is just a callable:
        runner(stage, inputs) -> {output_artifact_id: descriptor}
    execute_plan() only ever talks to that interface.
  * LocalOfflineAdapter is the deterministic local stand-in: it converts nothing and calls
    no library. Same stage + same inputs always give the same labelled descriptors.
  * NOT_ESTABLISHED lists what this mock does NOT prove about the real service.

SIMULATION ONLY: no model is converted, quantized or benchmarked, and nothing here says
how fast, accurate or compatible any real model or device is. Standard library only.
"""

import hashlib
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

STAGE_ORDER = ("export", "quantize", "benchmark")

# What the local mock does NOT establish about the real service (see README / lesson).
NOT_ESTABLISHED = (
    "That OpenVINO, NNCF or any converter can actually export or quantize a given model.",
    "Any real latency, throughput, memory or accuracy number: a benchmark output here is just a label.",
    "Real service failures: timeouts, partial writes, version mismatches, missing devices or credentials.",
    "That the artifacts are valid IR/model files or are compatible with any particular device.",
)


class PlanError(ValueError):
    """Raised when a plan is rejected before execution. `code` names the rule."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class AdapterError(RuntimeError):
    """Raised when the adapter breaks the interface or fails while a stage runs.

    `completed` lists the StageRecords of the stages that finished before the failure.
    """

    def __init__(self, code: str, message: str, completed: Sequence["StageRecord"] = ()):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.completed = list(completed)


@dataclass(frozen=True)
class Stage:
    name: str
    inputs: Sequence[str]
    outputs: Sequence[str]


@dataclass(frozen=True)
class StageRecord:
    name: str
    inputs: Tuple[str, ...]
    outputs: Dict[str, str]  # output artifact ID -> descriptor returned by the adapter


@dataclass(frozen=True)
class ExecutionRecord:
    stages: Tuple[StageRecord, ...]
    artifacts: Dict[str, str]  # every artifact ID known at the end -> descriptor


# The external dependency, reduced to a callable.
StageRunner = Callable[[Stage, Mapping[str, str]], Mapping[str, str]]


def validate_plan(plan: Sequence[Stage], starting_artifacts: Sequence[str]) -> List[str]:
    """Validate a plan without running anything. Return stage names, or raise PlanError."""
    if not plan:
        raise PlanError("EMPTY_PLAN", "a plan needs at least one stage")
    known = set(starting_artifacts)
    seen = set()
    last_rank = -1
    for stage in plan:
        if stage.name not in STAGE_ORDER:
            raise PlanError("UNKNOWN_STAGE", f"'{stage.name}' is not one of {STAGE_ORDER}")
        if stage.name in seen:
            raise PlanError("DUPLICATE_STAGE", f"'{stage.name}' appears more than once")
        rank = STAGE_ORDER.index(stage.name)
        if rank < last_rank:
            raise PlanError(
                "OUT_OF_ORDER", f"'{stage.name}' cannot come after '{STAGE_ORDER[last_rank]}'"
            )
        seen.add(stage.name)
        last_rank = rank
        if not stage.inputs:
            raise PlanError("MISSING_INPUT", f"stage '{stage.name}' records no input artifact")
        if not stage.outputs:
            raise PlanError("MISSING_OUTPUT", f"stage '{stage.name}' records no output artifact")
        for artifact in stage.inputs:
            if artifact not in known:
                raise PlanError(
                    "UNKNOWN_ARTIFACT",
                    f"stage '{stage.name}' reads '{artifact}', which no earlier stage produced",
                )
        for artifact in stage.outputs:
            if artifact in known:
                raise PlanError(
                    "DUPLICATE_ARTIFACT", f"stage '{stage.name}' re-creates artifact '{artifact}'"
                )
            known.add(artifact)
    return [stage.name for stage in plan]


def execute_plan(plan: Sequence[Stage], starting_artifacts: Sequence[str],
                 runner: StageRunner) -> ExecutionRecord:
    """Validate first, then run each stage through `runner`, recording what comes back."""
    validate_plan(plan, starting_artifacts)  # no runner call can happen before this passes

    artifacts: Dict[str, str] = {a: "provided" for a in starting_artifacts}
    records: List[StageRecord] = []
    for stage in plan:
        inputs = {a: artifacts[a] for a in stage.inputs}
        try:
            produced = runner(stage, dict(inputs))
        except Exception as exc:  # the adapter (the "service") failed
            raise AdapterError("ADAPTER_FAILED", f"stage '{stage.name}': {exc}", records) from exc
        if not isinstance(produced, Mapping) or set(produced) != set(stage.outputs):
            raise AdapterError(
                "BAD_OUTPUTS", f"stage '{stage.name}' must return exactly {sorted(stage.outputs)}", records
            )
        if any(not isinstance(v, str) or not v for v in produced.values()):
            raise AdapterError(
                "BAD_OUTPUTS", f"stage '{stage.name}' returned an empty or non-text descriptor", records
            )
        artifacts.update(produced)
        records.append(StageRecord(stage.name, tuple(stage.inputs), dict(produced)))
    return ExecutionRecord(tuple(records), artifacts)


class LocalOfflineAdapter:
    """Deterministic local stand-in for the external optimization service."""

    def __init__(self) -> None:
        self.calls: List[str] = []  # stage names, in the order they were run

    def __call__(self, stage: Stage, inputs: Mapping[str, str]) -> Mapping[str, str]:
        self.calls.append(stage.name)
        seed = stage.name + "|" + "|".join(f"{k}={inputs[k]}" for k in sorted(inputs))
        result = {}
        for out in stage.outputs:
            digest = hashlib.sha256(f"{seed}|{out}".encode()).hexdigest()[:8]
            result[out] = f"sim-{stage.name}-{digest}"
        return result


class FlakyAdapter:
    """Wraps another adapter and 'loses the service' when it reaches `fail_on`."""

    def __init__(self, inner: StageRunner, fail_on: str) -> None:
        self.inner = inner
        self.fail_on = fail_on

    def __call__(self, stage: Stage, inputs: Mapping[str, str]) -> Mapping[str, str]:
        if stage.name == self.fail_on:
            raise RuntimeError("simulated service timeout")
        return self.inner(stage, inputs)


# --- demo fixtures (also used by the tests) ------------------------------------
STARTING_ARTIFACTS = ["source_model"]


def good_plan() -> List[Stage]:
    return [
        Stage("export", ("source_model",), ("ov_ir",)),
        Stage("quantize", ("ov_ir",), ("ov_int8",)),
        Stage("benchmark", ("ov_int8",), ("bench_report",)),
    ]


def out_of_order_plan() -> List[Stage]:
    return [
        Stage("export", ("source_model",), ("ov_ir",)),
        Stage("benchmark", ("ov_ir",), ("bench_report",)),
        Stage("quantize", ("ov_ir",), ("ov_int8",)),
    ]


def unknown_artifact_plan() -> List[Stage]:
    return [
        Stage("export", ("source_model",), ("ov_ir",)),
        Stage("quantize", ("ov_int8_typo",), ("ov_int8",)),
    ]


def main() -> None:
    print("starting artifacts:", STARTING_ARTIFACTS)

    adapter = LocalOfflineAdapter()
    record = execute_plan(good_plan(), STARTING_ARTIFACTS, adapter)
    print("good plan [export, quantize, benchmark]: ACCEPTED and run through LocalOfflineAdapter")
    for stage in record.stages:
        outs = ", ".join(f"{k} = {v}" for k, v in stage.outputs.items())
        print(f"  {stage.name}: reads {list(stage.inputs)} -> writes {outs}")
    print(f"  adapter calls: {adapter.calls}")

    for label, plan in (("benchmark before quantize", out_of_order_plan()),
                        ("unknown artifact reference", unknown_artifact_plan())):
        adapter = LocalOfflineAdapter()
        try:
            execute_plan(plan, STARTING_ARTIFACTS, adapter)
        except PlanError as err:
            print(f"{label}: REJECTED {err.code} (adapter calls: {len(adapter.calls)})")

    try:
        execute_plan(good_plan(), STARTING_ARTIFACTS, FlakyAdapter(LocalOfflineAdapter(), "quantize"))
    except AdapterError as err:
        done = [r.name for r in err.completed]
        print(f"adapter fails at quantize: {err.code}; stages completed before it: {done}")

    print("not established by this mock:")
    for item in NOT_ESTABLISHED:
        print(f"  - {item}")


if __name__ == "__main__":
    main()
