"""
Microsoft Phi Model Family Synthetic Manifest Selection & Applied Questions Example (R04-T060).
Module 02: Small Language Model (SLM) Families (01.PhiFamily.md)

Concept:
In edge AI deployments, Small Language Models (such as the Microsoft Phi model family)
must be selected based on strict resource envelopes (RAM budget and requested context window).
A deterministic model manifest selector evaluates candidate models, admits compliant models,
and produces actionable exclusion diagnostics when a model fails resource criteria.

Canonical Contract:
- Manifest Entries:
  * Fixture A: required RAM 4.0 GB, max context 2048 tokens.
  * Fixture B: required RAM 8.0 GB, max context 4096 tokens.
- Constraints:
  * Host RAM budget: 6.0 GB.
  * Requested context length: 1024 tokens.
- Outcome:
  * Admits only Fixture A.
  * Excludes Fixture B with actionable explanation (insufficient RAM: 8.0 GB > 6.0 GB).
- Synthetic Teaching Fixtures:
  * Values are invented teaching fixtures, not claims about the named real models.

Contribution Focus:
Three applied questions about the local example:
1. Predict an output: predict admission/exclusion for a modified resource envelope.
2. Diagnose a failure: diagnose specific resource bottlenecks and actionable remedies.
3. Choose a boundary policy: choose inclusive boundary admission (<= and >=) with factual rationale and executable checks.
"""

from dataclasses import asdict, dataclass, field
import json
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ModelEntry:
    """Synthetic model metadata entry."""
    model_id: str
    name: str
    required_ram_gb: float
    max_context_length: int
    family: str = "phi-synthetic"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Canonical Teaching Fixtures
FIXTURE_A = ModelEntry(
    model_id="fixture-a",
    name="Synthetic Phi-Mini Teaching Variant A",
    required_ram_gb=4.0,
    max_context_length=2048,
    family="phi-synthetic",
)

FIXTURE_B = ModelEntry(
    model_id="fixture-b",
    name="Synthetic Phi-Medium Teaching Variant B",
    required_ram_gb=8.0,
    max_context_length=4096,
    family="phi-synthetic",
)

STANDARD_TEACHING_MANIFEST: List[ModelEntry] = [FIXTURE_A, FIXTURE_B]


@dataclass
class ExclusionReport:
    """Details why a model was excluded from eligibility."""
    model_id: str
    name: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SelectionResult:
    """Result of evaluating a model manifest against constraints."""
    admitted_models: List[ModelEntry]
    excluded_models: List[ExclusionReport]
    ram_budget_gb: float
    requested_context: int
    lesson_source: str = "Module02/01.PhiFamily.md"

    @property
    def admitted_ids(self) -> List[str]:
        return [m.model_id for m in self.admitted_models]

    @property
    def excluded_ids(self) -> List[str]:
        return [e.model_id for e in self.excluded_models]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ram_budget_gb": self.ram_budget_gb,
            "requested_context": self.requested_context,
            "lesson_source": self.lesson_source,
            "admitted_models": [m.to_dict() for m in self.admitted_models],
            "excluded_models": [e.to_dict() for e in self.excluded_models],
            "admitted_ids": self.admitted_ids,
            "excluded_ids": self.excluded_ids,
        }

    def summary(self) -> str:
        lines = [
            f"Evaluation against RAM budget {self.ram_budget_gb} GB, context {self.requested_context} tokens:",
            f"Admitted ({len(self.admitted_models)}): {self.admitted_ids}",
            f"Excluded ({len(self.excluded_models)}): {self.excluded_ids}",
        ]
        for exc in self.excluded_models:
            lines.append(f"  - [{exc.model_id}] {'; '.join(exc.reasons)}")
        return "\n".join(lines)


class PhiModelManifestSelector:
    """
    Deterministic selector matching synthetic SLM manifest entries against host constraints.
    """

    def __init__(self, lesson_source: str = "Module02/01.PhiFamily.md"):
        self.lesson_source = lesson_source

    def select(
        self,
        manifest: List[ModelEntry],
        ram_budget_gb: float,
        requested_context: int,
    ) -> SelectionResult:
        """
        Evaluate candidate models against host constraints.
        
        Boundary Policy:
        - Memory constraint: required_ram_gb <= ram_budget_gb (inclusive).
        - Context constraint: max_context_length >= requested_context (inclusive).
        """
        admitted: List[ModelEntry] = []
        excluded: List[ExclusionReport] = []

        for model in manifest:
            reasons: List[str] = []

            # 1. RAM check
            if model.required_ram_gb > ram_budget_gb:
                reasons.append(
                    f"Insufficient RAM: model requires {model.required_ram_gb} GB, "
                    f"but host budget is {ram_budget_gb} GB."
                )

            # 2. Context length check
            if model.max_context_length < requested_context:
                reasons.append(
                    f"Insufficient context capacity: model supports {model.max_context_length} tokens, "
                    f"but workload requires {requested_context} tokens."
                )

            if reasons:
                excluded.append(
                    ExclusionReport(
                        model_id=model.model_id,
                        name=model.name,
                        reasons=reasons,
                    )
                )
            else:
                admitted.append(model)

        return SelectionResult(
            admitted_models=admitted,
            excluded_models=excluded,
            ram_budget_gb=ram_budget_gb,
            requested_context=requested_context,
            lesson_source=self.lesson_source,
        )


# =============================================================================
# Applied Questions (Contribution Focus)
# =============================================================================

@dataclass
class AppliedQuestion:
    """Applied pedagogical question with factual answer, rationale, and executable check."""
    question_id: str
    category: str  # "predict_output", "diagnose_failure", "choose_boundary_policy"
    prompt: str
    factual_answer: Any
    rationale: str
    executable_check: Callable[[], bool] = field(repr=False)

    def verify(self) -> bool:
        """Execute the factual verification check."""
        return bool(self.executable_check())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "category": self.category,
            "prompt": self.prompt,
            "factual_answer": self.factual_answer,
            "rationale": self.rationale,
            "check_passed": self.verify(),
        }


def check_predict_output() -> bool:
    """Executable check for Question 1 (Predict an output)."""
    selector = PhiModelManifestSelector()
    # Scenario: Host RAM budget = 10.0 GB, Requested context = 3000 tokens
    res = selector.select(STANDARD_TEACHING_MANIFEST, ram_budget_gb=10.0, requested_context=3000)
    # Fixture A: 4.0 GB <= 10.0 GB (PASS), context 2048 < 3000 (FAIL) -> Excluded
    # Fixture B: 8.0 GB <= 10.0 GB (PASS), context 4096 >= 3000 (PASS) -> Admitted
    return (res.admitted_ids == ["fixture-b"]) and (res.excluded_ids == ["fixture-a"])


def check_diagnose_failure() -> bool:
    """Executable check for Question 2 (Diagnose a failure)."""
    selector = PhiModelManifestSelector()
    # Scenario: Low-memory host with RAM budget = 3.0 GB, Requested context = 1024 tokens
    res = selector.select(STANDARD_TEACHING_MANIFEST, ram_budget_gb=3.0, requested_context=1024)
    # Both fail. Fixture A must report insufficient RAM (4.0 > 3.0)
    exc_a = next((e for e in res.excluded_models if e.model_id == "fixture-a"), None)
    if not exc_a:
        return False
    reason_str = " ".join(exc_a.reasons)
    return (
        ("Insufficient RAM" in reason_str)
        and ("4.0 GB" in reason_str)
        and ("3.0 GB" in reason_str)
        and (len(res.admitted_ids) == 0)
    )


def check_choose_boundary_policy() -> bool:
    """Executable check for Question 3 (Choose a boundary policy)."""
    selector = PhiModelManifestSelector()
    # Boundary case: candidate model requirements match host envelope exactly
    boundary_fixture = ModelEntry(
        model_id="boundary-exact",
        name="Synthetic Boundary Model",
        required_ram_gb=6.0,
        max_context_length=1024,
    )
    res = selector.select([boundary_fixture], ram_budget_gb=6.0, requested_context=1024)
    # Under inclusive boundary policy (<= and >=), exact equality must be ADMITTED
    return res.admitted_ids == ["boundary-exact"] and len(res.excluded_ids) == 0


def get_applied_questions() -> List[AppliedQuestion]:
    """Retrieve the three applied pedagogical questions."""
    return [
        AppliedQuestion(
            question_id="Q1_PREDICT_OUTPUT",
            category="predict_output",
            prompt=(
                "Given an edge host configured with RAM budget 10.0 GB and requested context length 3000 tokens, "
                "which models from [Fixture A (RAM4/context2048), Fixture B (RAM8/context4096)] are admitted and which are excluded?"
            ),
            factual_answer={
                "admitted_ids": ["fixture-b"],
                "excluded_ids": ["fixture-a"],
            },
            rationale=(
                "Fixture A requires 4.0 GB RAM (within 10.0 GB budget) but its maximum context window of 2048 tokens "
                "is insufficient for the requested 3000 tokens, leading to exclusion. Fixture B requires 8.0 GB RAM "
                "(within 10.0 GB budget) and supports 4096 tokens (satisfying 3000 tokens), qualifying for admission."
            ),
            executable_check=check_predict_output,
        ),
        AppliedQuestion(
            question_id="Q2_DIAGNOSE_FAILURE",
            category="diagnose_failure",
            prompt=(
                "When evaluating [Fixture A, Fixture B] on a constrained device with RAM budget 3.0 GB and requested context 1024 tokens, "
                "both models fail admission. What is the specific resource bottleneck causing Fixture A's disqualification, "
                "and what actionable remedy resolves it?"
            ),
            factual_answer={
                "failing_model": "fixture-a",
                "primary_bottleneck": "RAM",
                "required_vs_budget": "4.0 GB required vs 3.0 GB budget",
                "diagnostic_reason": "Insufficient RAM: model requires 4.0 GB, but host budget is 3.0 GB.",
                "actionable_remedy": "Increase host RAM allocation to at least 4.0 GB or apply INT4 quantization to reduce memory footprint below 3.0 GB.",
            },
            rationale=(
                "The memory admission policy enforces required_ram_gb <= ram_budget_gb. Fixture A requires 4.0 GB, exceeding "
                "the 3.0 GB limit by 1.0 GB. Although its context length of 2048 tokens easily satisfies the 1024-token requirement, "
                "memory insufficiency causes immediate disqualification."
            ),
            executable_check=check_diagnose_failure,
        ),
        AppliedQuestion(
            question_id="Q3_CHOOSE_BOUNDARY_POLICY",
            category="choose_boundary_policy",
            prompt=(
                "For an edge device where a model entry's resource requirements match the environment constraints exactly "
                "(required RAM == host budget, and max context == requested context), which boundary policy should the selector enforce: "
                "inclusive boundary admission (<= and >=) or strict inequality (< and >)?"
            ),
            factual_answer={
                "chosen_policy": "INCLUSIVE_BOUNDARY_ADMISSION",
                "ram_comparison": "<=",
                "context_comparison": ">=",
                "boundary_verdict": "ADMITTED",
            },
            rationale=(
                "Edge resource envelopes define the upper bound of available physical memory and the lower bound of acceptable "
                "context capacity. A model requiring exactly the allocated memory (without exceeding it) and providing exactly the "
                "requested context operates safely within specification. Strict inequality would prematurely reject models that "
                "fit within the available envelope."
            ),
            executable_check=check_choose_boundary_policy,
        ),
    ]


def verify_all_applied_questions() -> Dict[str, Any]:
    """Execute and verify all three applied questions."""
    questions = get_applied_questions()
    results = [q.to_dict() for q in questions]
    all_passed = all(r["check_passed"] for r in results)
    return {
        "all_passed": all_passed,
        "questions_count": len(questions),
        "results": results,
    }


def identify_unestablished_behaviors() -> List[str]:
    """Identify behaviors that this offline educational validator does not establish."""
    return [
        "Does not query physical host memory registers, OS virtual swap, or unified memory architectures.",
        "Does not download, load, or evaluate real Microsoft Phi model weights (Phi-1, Phi-2, Phi-3, Phi-4).",
        "Does not measure real-world inference throughput (tokens/second), time-to-first-token, or GPU latency.",
        "Does not allocate physical GPU VRAM, CUDA buffers, or NPU runtime execution contexts.",
        "Does not validate model reasoning accuracy, benchmark scores (MMLU, GSM8K), or response quality.",
    ]


def explain_mapping() -> List[Dict[str, str]]:
    """Map selector components to Module02/01.PhiFamily.md concepts."""
    return [
        {
            "component": "required_ram_gb (4.0 GB vs 8.0 GB)",
            "lesson_concept": "Section 1 Microsoft Phi Model Family Fundamentals (Phi-3-mini vs Phi-3-medium)",
            "pedagogical_purpose": "Illustrates edge hardware footprint planning across compact SLM tiers.",
        },
        {
            "component": "max_context_length (2048 vs 4096 tokens)",
            "lesson_concept": "Section 1 Architectural Innovations & Context Window Scaling",
            "pedagogical_purpose": "Demonstrates matching task prompt lengths to model context capacity.",
        },
        {
            "component": "Actionable Exclusion Diagnostics",
            "lesson_concept": "Best Practices: Consider Hardware & Deployment Planning",
            "pedagogical_purpose": "Provides distinct explanations detailing why candidate models exceed host bounds.",
        },
        {
            "component": "Three Applied Pedagogical Questions",
            "lesson_concept": "Practical Decision-Making Matrix for Phi Variant Selection",
            "pedagogical_purpose": "Reinforces prediction, failure diagnosis, and boundary policy evaluation.",
        },
        {
            "component": "Inclusive Boundary Admission Policy",
            "lesson_concept": "Optimization Techniques for Resource-Constrained Devices",
            "pedagogical_purpose": "Ensures boundary-case resource envelope utilization without false rejections.",
        },
    ]


def main() -> None:
    """CLI demonstration of Phi model manifest selection and applied questions."""
    print("=" * 75)
    print("Microsoft Phi Model Family: Synthetic Manifest Selection (R04-T060)")
    print("Module 02 Section 1 (01.PhiFamily.md)")
    print("=" * 75)

    selector = PhiModelManifestSelector()

    print("\n--- 1. Evaluating Canonical Fixtures (Budget RAM 6 GB, Context 1024) ---")
    canonical_res = selector.select(
        STANDARD_TEACHING_MANIFEST, ram_budget_gb=6.0, requested_context=1024
    )
    print(canonical_res.summary())
    print("\nAdmitted IDs:", canonical_res.admitted_ids)
    print("Excluded IDs:", canonical_res.excluded_ids)

    print("\n--- 2. Executing Three Applied Questions ---")
    q_res = verify_all_applied_questions()
    for q in q_res["results"]:
        status = "✓ PASS" if q["check_passed"] else "✗ FAIL"
        print(f"\n[{q['category'].upper()}] - {status}")
        print(f"  Prompt: {q['prompt']}")
        print(f"  Answer: {json.dumps(q['factual_answer'])}")
        print(f"  Rationale: {q['rationale']}")

    print(f"\nAll Applied Questions Verified: {q_res['all_passed']}")

    print("\n--- 3. Unestablished Real-Service Behaviors ---")
    for unest in identify_unestablished_behaviors():
        print(f"  * {unest}")


if __name__ == "__main__":
    main()
