"""
R04-T015: Teacher/Student Probability Comparison - Offline Service Adapter
Companion applied lab for Module05/02.SLMOps-Distillation.md.

Demonstrates cross-entropy computation between teacher and student probability distributions:
- Validates both distributions (same dimension, non-negative, sum to 1.0).
- Applies a positive epsilon floor for numerical stability in logarithm computation.
- Canonical fixture:
    Teacher [1.0, 0.0], Student [0.5, 0.5] -> cross-entropy = ln(2) (~0.693147).
    Teacher [1.0, 0.0], Student [1.0, 0.0] -> cross-entropy = 0.0.
- Puts probability retrieval behind a callable interface with a deterministic local adapter.

Prerequisites: Python 3 standard library only.
"""

import math
from typing import Any, Callable, Dict, List, Optional, Tuple


class DistillationError(Exception):
    """Raised when probability distribution validation fails."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


EPSILON_FLOOR = 1e-12


def validate_probability_distribution(dist: Any, name: str = "distribution") -> List[float]:
    """
    Validates that input is a valid discrete probability distribution:
    - Sequence of numbers.
    - Dimension at least 2.
    - All elements non-negative.
    - Sums to 1.0 (within float tolerance).
    """
    if not isinstance(dist, (list, tuple)):
        raise DistillationError("INVALID_DISTRIBUTION", f"{name} must be a list or tuple, got {type(dist).__name__}.")

    if len(dist) < 2:
        raise DistillationError("INVALID_DISTRIBUTION", f"{name} must have at least 2 classes, got {len(dist)}.")

    float_vals = []
    for idx, v in enumerate(dist):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise DistillationError("INVALID_DISTRIBUTION", f"Item at index {idx} in {name} must be a number, got {type(v).__name__}.")
        if v < 0.0:
            raise DistillationError("INVALID_DISTRIBUTION", f"Item at index {idx} in {name} cannot be negative: {v}.")
        float_vals.append(float(v))

    total = sum(float_vals)
    if not math.isclose(total, 1.0, abs_tol=1e-4):
        raise DistillationError("INVALID_DISTRIBUTION", f"{name} must sum to 1.0, got sum={total:.6f}.")

    return float_vals


def compute_cross_entropy(
    teacher_probs: List[float],
    student_probs: List[float],
    eps: float = EPSILON_FLOOR
) -> float:
    """
    Computes cross-entropy loss H(teacher, student) = - sum(teacher_i * ln(max(student_i, eps))).
    Uses a small positive epsilon floor for student probabilities to avoid log(0).
    """
    p = validate_probability_distribution(teacher_probs, "teacher_probs")
    q = validate_probability_distribution(student_probs, "student_probs")

    if len(p) != len(q):
        raise DistillationError(
            "DIMENSION_MISMATCH",
            f"Teacher dimension ({len(p)}) does not match student dimension ({len(q)})."
        )

    loss = 0.0
    for p_i, q_i in zip(p, q):
        if p_i > 0.0:
            clamped_q = max(q_i, eps)
            loss -= p_i * math.log(clamped_q)

    # Protect against negative floating point zero (-0.0)
    return abs(loss) if abs(loss) < 1e-15 else loss


class ProbabilityProvider:
    """Callable interface for fetching teacher and student distribution pairs."""
    def get_distributions(self, sample_id: str) -> Tuple[List[float], List[float]]:
        raise NotImplementedError


class LocalDistillationAdapter(ProbabilityProvider):
    """
    Deterministic offline adapter for unit testing and local verification.
    Provides predictable distributions without requiring remote Azure ML services,
    GPU inference endpoints, or model weights.
    """
    def __init__(self, fixtures: Optional[Dict[str, Tuple[List[float], List[float]]]] = None):
        self.fixtures = fixtures or {
            "canonical_soft": ([1.0, 0.0], [0.5, 0.5]),
            "canonical_identical": ([1.0, 0.0], [1.0, 0.0]),
            "multi_class": ([0.7, 0.2, 0.1], [0.5, 0.3, 0.2]),
        }

    def get_distributions(self, sample_id: str) -> Tuple[List[float], List[float]]:
        if sample_id not in self.fixtures:
            raise DistillationError("FIXTURE_NOT_FOUND", f"No fixture found for sample '{sample_id}'.")
        return self.fixtures[sample_id]


def evaluate_distillation_sample(provider: ProbabilityProvider, sample_id: str) -> Dict[str, Any]:
    """Retrieves distributions through provider and calculates cross-entropy."""
    teacher_p, student_p = provider.get_distributions(sample_id)
    loss = compute_cross_entropy(teacher_p, student_p)
    return {
        "sample_id": sample_id,
        "teacher": teacher_p,
        "student": student_p,
        "cross_entropy": loss,
    }


def run_concept_example() -> Dict[str, Any]:
    """Runs canonical distillation scenarios."""
    adapter = LocalDistillationAdapter()

    # 1. Teacher [1, 0], Student [0.5, 0.5] -> ln(2)
    soft_res = evaluate_distillation_sample(adapter, "canonical_soft")

    # 2. Identical one-hot distributions -> approaches 0.0
    ident_res = evaluate_distillation_sample(adapter, "canonical_identical")

    # Expected ln(2)
    expected_ln2 = math.log(2.0)

    return {
        "soft_loss": soft_res["cross_entropy"],
        "expected_ln2": expected_ln2,
        "matches_ln2": math.isclose(soft_res["cross_entropy"], expected_ln2, rel_tol=1e-6),
        "identical_loss": ident_res["cross_entropy"],
        "approaches_zero": math.isclose(ident_res["cross_entropy"], 0.0, abs_tol=1e-9),
    }


if __name__ == "__main__":
    res = run_concept_example()
    print("=== Distillation Probability Comparison ===")
    print(f"Teacher [1, 0] vs Student [0.5, 0.5]: loss = {res['soft_loss']:.6f} (ln(2) = {res['expected_ln2']:.6f})")
    print(f"Matches ln(2): {res['matches_ln2']}")
    print(f"Teacher [1, 0] vs Student [1, 0]: loss = {res['identical_loss']:.9f} (approaches 0)")
    print("\n[NOTE] Local adapter mock does not establish GPU backward passes, temperature scaling, or FP16 rounding.")
