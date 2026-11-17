"""
Gemma Family Synthetic Model-Manifest Selection Teaching Example.

Extends Section 3: Gemma Family Fundamentals at Module02/03.GemmaFamily.md.
Demonstrates deterministic local filtering of a synthetic model manifest
based on explicit RAM and context constraints, providing actionable exclusion explanations.

Contract:
- Manifest entries specify required RAM (GB) and maximum supported context length (tokens).
- Fixture A requires RAM 4 GB, context 2048 tokens.
- Fixture B requires RAM 8 GB, context 4096 tokens.
- Given budget RAM 6 GB and requested context 1024 tokens, only Fixture A is admitted.
- Excluded entries explicitly detail the reason for failure.
- Values are invented teaching fixtures, not claims about named real models.
- Focus: Publish a worked input-to-output explanation and execute the exact example as a regression test.
"""

from dataclasses import asdict, dataclass, field
import json
from typing import Any, Dict, List, Optional


@dataclass
class ModelEntry:
    """Synthetic model metadata entry."""
    model_id: str
    name: str
    required_ram_gb: float
    max_context_length: int
    family: str = "gemma-synthetic"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
    """Structured result of model manifest filtering."""
    admitted_models: List[ModelEntry]
    excluded_models: List[ExclusionReport]
    ram_budget_gb: float
    requested_context: int
    lesson_source: str = "Module02/03.GemmaFamily.md"

    @property
    def admitted_ids(self) -> List[str]:
        return [m.model_id for m in self.admitted_models]

    @property
    def excluded_ids(self) -> List[str]:
        return [e.model_id for e in self.excluded_models]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lesson_source": self.lesson_source,
            "ram_budget_gb": self.ram_budget_gb,
            "requested_context": self.requested_context,
            "admitted_models": [m.to_dict() for m in self.admitted_models],
            "excluded_models": [e.to_dict() for e in self.excluded_models],
            "admitted_ids": self.admitted_ids,
            "excluded_ids": self.excluded_ids,
            "summary": {
                "total_evaluated": len(self.admitted_models) + len(self.excluded_models),
                "admitted_count": len(self.admitted_models),
                "excluded_count": len(self.excluded_models),
            },
        }

    def summary(self) -> str:
        lines = [
            f"Model Selection Summary (Lesson: {self.lesson_source})",
            f"Host Budget: RAM={self.ram_budget_gb} GB, Requested Context={self.requested_context} tokens",
            f"Admitted Models ({len(self.admitted_models)}):",
        ]
        for m in self.admitted_models:
            lines.append(f"  - [{m.model_id}] {m.name} (RAM: {m.required_ram_gb} GB, Context: {m.max_context_length})")
        lines.append(f"Excluded Models ({len(self.excluded_models)}):")
        for e in self.excluded_models:
            lines.append(f"  - [{e.model_id}] {e.name}")
            for r in e.reasons:
                lines.append(f"    * {r}")
        return "\n".join(lines)


# Standard canonical teaching fixtures defined in task contract
FIXTURE_A = ModelEntry(
    model_id="fixture-a",
    name="Synthetic Gemma Teaching Variant A",
    required_ram_gb=4.0,
    max_context_length=2048,
    family="gemma-synthetic",
)

FIXTURE_B = ModelEntry(
    model_id="fixture-b",
    name="Synthetic Gemma Teaching Variant B",
    required_ram_gb=8.0,
    max_context_length=4096,
    family="gemma-synthetic",
)

STANDARD_TEACHING_MANIFEST: List[ModelEntry] = [FIXTURE_A, FIXTURE_B]


class ModelManifestSelector:
    """Filters model manifest entries according to hardware budget and context requirements."""

    def __init__(self, lesson_source: str = "Module02/03.GemmaFamily.md"):
        self.lesson_source = lesson_source

    def select(
        self,
        manifest: List[Any],
        ram_budget_gb: float,
        requested_context: int,
    ) -> SelectionResult:
        """
        Evaluate candidate models in manifest against RAM budget and context requirement.
        
        Validation rules:
        - ram_budget_gb must be positive (> 0).
        - requested_context must be a positive integer (> 0).
        - Model admitted iff required_ram_gb <= ram_budget_gb AND max_context_length >= requested_context.
        """
        if ram_budget_gb <= 0:
            raise ValueError(f"RAM budget must be positive (> 0), got: {ram_budget_gb}")
        if requested_context <= 0 or not isinstance(requested_context, int):
            raise ValueError(f"Requested context must be a positive integer (> 0), got: {requested_context}")

        admitted: List[ModelEntry] = []
        excluded: List[ExclusionReport] = []

        for item in manifest:
            # Normalize dict or ModelEntry
            if isinstance(item, ModelEntry):
                model = item
            elif isinstance(item, dict):
                model = ModelEntry(
                    model_id=item["model_id"],
                    name=item.get("name", item["model_id"]),
                    required_ram_gb=float(item["required_ram_gb"]),
                    max_context_length=int(item["max_context_length"]),
                    family=item.get("family", "gemma-synthetic"),
                )
            else:
                raise TypeError(f"Manifest items must be dict or ModelEntry, got: {type(item)}")

            reasons: List[str] = []

            # Constraint 1: RAM requirement
            if model.required_ram_gb > ram_budget_gb:
                reasons.append(
                    f"Insufficient RAM: model requires {model.required_ram_gb} GB, but host budget is {ram_budget_gb} GB."
                )

            # Constraint 2: Context length requirement
            if model.max_context_length < requested_context:
                reasons.append(
                    f"Insufficient context capacity: model supports up to {model.max_context_length} tokens, "
                    f"but requested context is {requested_context} tokens."
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

    @staticmethod
    def identify_unestablished_behaviors() -> List[str]:
        """Declare real-service behaviors that this local synthetic mock does not establish."""
        return [
            "Does not query physical OS RAM, swap partitions, or unified memory subsystems.",
            "Does not download, load, or verify real Gemma model weights (e.g. Gemma 2 2B, 9B, 27B).",
            "Does not allocate GPU VRAM, CUDA unified buffers, or configure runtime KV caches.",
            "Does not establish real-world inference throughput, latency, or model response accuracy.",
            "Values are invented teaching fixtures designed solely for deterministic constraint verification.",
        ]

    @staticmethod
    def explain_mapping() -> List[Dict[str, str]]:
        """Map teaching components directly to lesson concepts in Module02/03.GemmaFamily.md."""
        return [
            {
                "selector_component": "required_ram_gb (4 GB vs 8 GB)",
                "lesson_concept": "Model Size and Deployment Options (Gemma 2B/4B edge vs 8B/27B workstation sizes)",
                "pedagogical_purpose": "Illustrates memory footprint planning for constrained edge hardware.",
            },
            {
                "selector_component": "max_context_length (2048 vs 4096 tokens)",
                "lesson_concept": "Context Window Expansion Innovations (8K vs 128K context capabilities)",
                "pedagogical_purpose": "Ensures model context window accommodates workload document lengths.",
            },
            {
                "selector_component": "ram_budget_gb & requested_context constraints",
                "lesson_concept": "Key Deployment Requirements (Edge Deployment & Cost Effectiveness)",
                "pedagogical_purpose": "Defines explicit environmental resource envelopes before model loading.",
            },
            {
                "selector_component": "Explicit Exclusion Reporting",
                "lesson_concept": "Deployment Planning and Troubleshooting Best Practices",
                "pedagogical_purpose": "Provides deterministic, actionable explanations when a model is disqualified.",
            },
            {
                "selector_component": "Worked Input-to-Output Regression Example",
                "lesson_concept": "Practical Decision-Making Matrix for Gemma Variant Selection",
                "pedagogical_purpose": "Demonstrates regression-tested step-by-step evaluation from inputs to outputs.",
            },
        ]


def explain_worked_example(
    manifest: Optional[List[ModelEntry]] = None,
    ram_budget_gb: float = 6.0,
    requested_context: int = 1024,
) -> str:
    """
    Publish a worked input-to-output explanation as required by the contribution focus.
    Details step-by-step evaluation of Fixture A and Fixture B under RAM budget 6 GB and requested context 1024 tokens.
    """
    if manifest is None:
        manifest = STANDARD_TEACHING_MANIFEST

    selector = ModelManifestSelector()
    result = selector.select(manifest, ram_budget_gb, requested_context)

    lines = [
        "================================================================================",
        "Worked Input-to-Output Explanation: Gemma Synthetic Manifest Selection",
        "================================================================================",
        "\n1. INPUT SPECIFICATION",
        "-----------------------",
        f"Host Environmental Constraints: Budget RAM = {ram_budget_gb} GB, Requested Context = {requested_context} tokens.",
        "Candidate Manifest Entries:",
    ]
    for m in manifest:
        lines.append(
            f"  * [{m.model_id}] {m.name}: required_ram_gb = {m.required_ram_gb} GB, "
            f"max_context_length = {m.max_context_length} tokens"
        )

    lines.append("\n2. STEP-BY-STEP EVALUATION")
    lines.append("---------------------------")
    for m in manifest:
        ram_ok = m.required_ram_gb <= ram_budget_gb
        context_ok = m.max_context_length >= requested_context
        lines.append(f"Evaluating {m.model_id} ({m.name}):")
        lines.append(
            f"  - RAM check: required {m.required_ram_gb} GB <= budget {ram_budget_gb} GB -> "
            f"{'PASS' if ram_ok else 'FAIL (exceeds budget by ' + str(round(m.required_ram_gb - ram_budget_gb, 2)) + ' GB)'}"
        )
        lines.append(
            f"  - Context check: max context {m.max_context_length} >= requested {requested_context} tokens -> "
            f"{'PASS' if context_ok else 'FAIL (short by ' + str(requested_context - m.max_context_length) + ' tokens)'}"
        )
        if ram_ok and context_ok:
            lines.append("  => VERDICT: ADMITTED (all constraints satisfied)")
        else:
            lines.append("  => VERDICT: EXCLUDED (insufficient resources)")

    lines.append("\n3. DETERMINISTIC OUTPUT REPORT")
    lines.append("------------------------------")
    lines.append(f"Admitted Models: {result.admitted_ids}")
    lines.append(f"Excluded Models: {result.excluded_ids}")
    for e in result.excluded_models:
        lines.append(f"  - [{e.model_id}] Exclusion Reasons:")
        for r in e.reasons:
            lines.append(f"      * {r}")

    lines.append("\n4. CONCLUSION & REGRESSION GUARANTEE")
    lines.append("------------------------------------")
    lines.append(
        f"Under RAM budget {ram_budget_gb} GB and requested context {requested_context} tokens, "
        "only Fixture A is admitted. Fixture B is rejected strictly due to exceeding host RAM capacity."
    )
    return "\n".join(lines)


# Module-level aliases for ease of access
explain_mapping = ModelManifestSelector.explain_mapping
identify_unestablished_behaviors = ModelManifestSelector.identify_unestablished_behaviors


def select_eligible_models(
    manifest: List[Any],
    ram_budget_gb: float,
    requested_context: int,
) -> SelectionResult:
    """Convenience function executing ModelManifestSelector.select()."""
    selector = ModelManifestSelector()
    return selector.select(manifest, ram_budget_gb, requested_context)


def main() -> None:
    """Run CLI demonstration of Gemma synthetic model manifest selection."""
    print(explain_worked_example())


if __name__ == "__main__":
    main()
