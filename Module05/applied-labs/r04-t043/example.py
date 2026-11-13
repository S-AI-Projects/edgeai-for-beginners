"""R04-T043 - Teacher/student probability comparison: invariant and state trace
(Module05/02.SLMOps-Distillation.md, "Section 2: Model Distillation - From Theory to Practice").

Contract (small and local):
  cross_entropy(teacher, student) = - sum_i  p_i * ln( max(q_i, FLOOR) )

  * `teacher` (p) and `student` (q) are probability distributions you supply by hand.
  * BOTH are validated first: non-empty, numeric, finite, no negative values, sum to 1
    (within 1e-9), and the same length.
  * A small positive FLOOR (default 1e-12) is applied inside the log so ln(0) never
    happens. Convention: a term with p_i == 0 contributes exactly 0.
  * The calculation records its intermediate state after EACH step (index, p, q, the
    floored q, the term, and the running total). check_invariant() then tests the link
    between that state and the final output:
        - every term is >= 0
        - running_total[k] equals the sum of terms[0..k]
        - running totals never decrease
        - the final result equals the last running total

Worked values: teacher [1,0] vs student [0.5,0.5] gives ln(2); identical one-hot
distributions give 0.

SIMULATION ONLY: the probabilities are typed in by hand. No model is run, nothing is
trained, and nothing here says how well any real distilled model performs on any
hardware or service. Standard library only (Python 3).
"""

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

DEFAULT_FLOOR = 1e-12
SUM_TOLERANCE = 1e-9
CHECK_TOLERANCE = 1e-12


class DistributionError(ValueError):
    """Raised when an input is rejected. `code` names the rule that failed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class Step:
    index: int
    p: float            # teacher probability for this class
    q: float            # student probability for this class (as supplied)
    q_floored: float    # max(q, floor): what actually goes into the log
    term: float         # -p * ln(q_floored), or exactly 0.0 when p == 0
    running_total: float


@dataclass(frozen=True)
class Trace:
    floor: float
    steps: Tuple[Step, ...]
    result: float


def validate_distribution(name: str, probs: Sequence[float]) -> None:
    """Reject anything that is not a usable probability distribution."""
    if probs is None or len(probs) == 0:
        raise DistributionError("EMPTY", f"{name} has no probabilities")
    for i, value in enumerate(probs):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise DistributionError("NON_NUMERIC", f"{name}[{i}] is not a number")
        if not math.isfinite(value):
            raise DistributionError("NOT_FINITE", f"{name}[{i}] is not finite")
        if value < 0:
            raise DistributionError("NEGATIVE_PROBABILITY", f"{name}[{i}] is negative")
    total = math.fsum(probs)
    if abs(total - 1.0) > SUM_TOLERANCE:
        raise DistributionError("NOT_NORMALIZED", f"{name} sums to {total}, not 1")


def validate_floor(floor: float) -> None:
    if isinstance(floor, bool) or not isinstance(floor, (int, float)) \
            or not math.isfinite(floor) or not (0 < floor < 1):
        raise DistributionError("BAD_FLOOR", "floor must be a number with 0 < floor < 1")


def cross_entropy_trace(teacher: Sequence[float], student: Sequence[float],
                        floor: float = DEFAULT_FLOOR) -> Trace:
    """Validate, then compute the cross-entropy while recording every step."""
    validate_distribution("teacher", teacher)
    validate_distribution("student", student)
    if len(teacher) != len(student):
        raise DistributionError(
            "LENGTH_MISMATCH", f"teacher has {len(teacher)} classes, student has {len(student)}"
        )
    validate_floor(floor)

    steps: List[Step] = []
    running = 0.0
    for i, (p, q) in enumerate(zip(teacher, student)):
        q_floored = max(q, floor)
        term = 0.0 if p == 0 else -p * math.log(q_floored) + 0.0  # + 0.0 turns -0.0 into 0.0
        running += term
        steps.append(Step(i, float(p), float(q), q_floored, term, running))
    # The result is summed a second, independent way (fsum) so the invariant is a real check.
    result = math.fsum(step.term for step in steps)
    return Trace(floor, tuple(steps), result)


def cross_entropy(teacher: Sequence[float], student: Sequence[float],
                  floor: float = DEFAULT_FLOOR) -> float:
    return cross_entropy_trace(teacher, student, floor).result


def check_invariant(trace: Trace) -> List[str]:
    """Test the link between the recorded state and the final output.

    Returns a list of violations; an empty list means the trace is consistent.
    """
    problems: List[str] = []
    if not trace.steps:
        return ["no steps recorded"]
    terms = [s.term for s in trace.steps]
    for k, step in enumerate(trace.steps):
        if step.term < 0:
            problems.append(f"step {k}: term is negative")
        expected = math.fsum(terms[: k + 1])
        if abs(step.running_total - expected) > CHECK_TOLERANCE:
            problems.append(f"step {k}: running total != sum of terms so far")
        if k > 0 and step.running_total < trace.steps[k - 1].running_total:
            problems.append(f"step {k}: running total decreased")
    if abs(trace.result - trace.steps[-1].running_total) > CHECK_TOLERANCE:
        problems.append("result != last running total")
    return problems


# --- demo fixtures (also used by the tests) ------------------------------------
CASES = [
    ("teacher [1,0] vs student [0.5,0.5]", [1, 0], [0.5, 0.5]),
    ("identical one-hot [1,0]", [1, 0], [1, 0]),
    ("floor in action: teacher [1,0] vs student [0,1]", [1, 0], [0, 1]),
    ("teacher not normalized", [0.5, 0.4], [0.5, 0.5]),
    ("length mismatch", [1, 0], [1]),
    ("negative probability", [1.5, -0.5], [0.5, 0.5]),
]


def main() -> None:
    print(f"floor = {DEFAULT_FLOOR}   (ln(2) = {math.log(2):.6f})")
    for label, teacher, student in CASES:
        print(f"{label}:")
        try:
            trace = cross_entropy_trace(teacher, student)
        except DistributionError as err:
            print(f"  REJECTED {err.code}")
            continue
        for s in trace.steps:
            print(f"  step {s.index}: p={s.p:.4f} q={s.q:.4f} q_floored={s.q_floored:.1e} "
                  f"term={s.term:.6f} running={s.running_total:.6f}")
        verdict = "holds" if not check_invariant(trace) else "VIOLATED"
        print(f"  result={trace.result:.6f}  invariant {verdict}")
    print("note: probabilities are typed in by hand; this is a simulation, not a trained model.")


if __name__ == "__main__":
    main()
