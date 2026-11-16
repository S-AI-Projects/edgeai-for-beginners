#!/usr/bin/env python3
"""
Model-Manifest Selection - Offline Service Adapter (R04-T054)
Module 02: Microsoft Mu Model Fundamentals (05.mumodel.md)

Concept:
In on-device and edge deployment scenarios (such as Microsoft Mu model integration
in Windows 11), host environments must evaluate model metadata against local resource
constraints (RAM capacity and context window requirements) before loading weights into
working memory. An offline service adapter decouples catalog fetching from external
services, enabling deterministic preflight admission control without live cloud or
hardware dependencies.

Focus:
1. Put the external model catalog dependency behind a callable interface.
2. Supply a deterministic local adapter with synthetic model fixtures.
3. Select eligible models and provide explicit failure explanations for excluded entries.
4. Enforce contract: Fixture A (RAM4/context2048), Fixture B (RAM8/context4096).
   Under budget RAM6 and requested context1024, admits ONLY Fixture A.
5. Explicitly identify real-service behaviors this mock does not establish.

Pedagogical Notice:
Values are invented teaching fixtures, not claims about the named real models.
"""

import copy
from typing import Any, Callable, Dict, List, Optional


# Synthetic teaching fixtures (invented values, not claims about real models)
DEFAULT_SYNTHETIC_MANIFEST: List[Dict[str, Any]] = [
    {
        "id": "fixture-a",
        "name": "Mu-Fixture-A",
        "min_ram_gb": 4,
        "max_context": 2048,
        "quantization": "INT8",
        "intended_use": "Compact system settings reasoning",
    },
    {
        "id": "fixture-b",
        "name": "Mu-Fixture-B",
        "min_ram_gb": 8,
        "max_context": 4096,
        "quantization": "FP16",
        "intended_use": "Expanded multi-turn system orchestration",
    },
]


class SyntheticManifestAdapter:
    """Callable offline service adapter providing deterministic synthetic model manifests."""

    def __init__(self, manifest: Optional[List[Dict[str, Any]]] = None) -> None:
        """Initialize adapter with synthetic manifest entries.

        Args:
            manifest: Optional custom manifest list. Defaults to DEFAULT_SYNTHETIC_MANIFEST.
        """
        self._manifest = copy.deepcopy(manifest if manifest is not None else DEFAULT_SYNTHETIC_MANIFEST)

    def __call__(self) -> List[Dict[str, Any]]:
        """Return a defensive copy of the synthetic model manifest."""
        return copy.deepcopy(self._manifest)


class ModelManifestSelector:
    """Evaluates and filters models against host RAM and requested context constraints."""

    def __init__(self, manifest_provider: Optional[Callable[[], List[Dict[str, Any]]]] = None) -> None:
        """Initialize selector with a callable manifest provider.

        Args:
            manifest_provider: Callable returning a list of model dictionaries.
        """
        self.manifest_provider = manifest_provider or SyntheticManifestAdapter()

    def select(self, available_ram_gb: float, requested_context: int) -> Dict[str, Any]:
        """Evaluate catalog entries against host RAM budget and required context length.

        Args:
            available_ram_gb: Available host memory budget in gigabytes.
            requested_context: Desired conversational token context capacity.

        Returns:
            Dictionary detailing admitted models, excluded models with failure reasons,
            and evaluation metadata.

        Raises:
            ValueError: If available_ram_gb or requested_context is nonpositive.
        """
        if available_ram_gb <= 0:
            raise ValueError(f"available_ram_gb must be positive (> 0), got: {available_ram_gb}")
        if requested_context <= 0:
            raise ValueError(f"requested_context must be positive (> 0), got: {requested_context}")

        manifest = self.manifest_provider()
        admitted: List[Dict[str, Any]] = []
        excluded: List[Dict[str, Any]] = []

        for entry in manifest:
            # Validate entry structure
            min_ram = entry.get("min_ram_gb")
            max_context = entry.get("max_context")
            model_id = entry.get("id", "unknown")

            if min_ram is None or max_context is None:
                raise ValueError(f"Malformed manifest entry missing required fields: {entry}")

            reasons: List[str] = []
            ram_ok = min_ram <= available_ram_gb
            context_ok = max_context >= requested_context

            if not ram_ok:
                reasons.append(
                    f"Insufficient RAM: requires {min_ram}GB, but host budget is {available_ram_gb}GB"
                )
            if not context_ok:
                reasons.append(
                    f"Insufficient context capacity: model supports max {max_context} tokens, "
                    f"but {requested_context} tokens were requested"
                )

            if ram_ok and context_ok:
                admitted.append(copy.deepcopy(entry))
            else:
                excluded.append({
                    "id": model_id,
                    "name": entry.get("name", model_id),
                    "min_ram_gb": min_ram,
                    "max_context": max_context,
                    "reasons": reasons,
                })

        return {
            "budget_ram_gb": available_ram_gb,
            "requested_context": requested_context,
            "admitted": admitted,
            "admitted_ids": [m["id"] for m in admitted],
            "excluded": excluded,
            "excluded_ids": [m["id"] for m in excluded],
            "total_evaluated": len(manifest),
            "teaching_note": "Values are invented teaching fixtures, not claims about the named real models.",
        }

    @staticmethod
    def identify_unestablished_behaviors() -> List[str]:
        """List the real-service behaviors that this offline mock does not establish."""
        return [
            "Network Transport & Catalog Sync: Does not establish live REST/RPC communication with Azure AI Foundry or Windows catalog endpoints.",
            "Dynamic Host Telemetry: Does not query live Windows kernel page files, physical RAM pressure, or DirectML NPU availability.",
            "Authentication & Quotas: Does not establish OAuth tokens, enterprise policy checks, or catalog rate limits.",
            "Live Weight Verification: Does not verify cryptographic weight checksums, on-disk file layout, or runtime quantization execution.",
        ]


def explain_mapping() -> Dict[str, str]:
    """Map public selector inputs and outputs to on-device Mu model deployment concepts."""
    return {
        "available_ram_gb": "Allocated host memory budget for on-device model execution",
        "requested_context": "Target token sequence length needed by the application",
        "min_ram_gb": "Minimum memory footprint required for model weights and KV cache",
        "max_context": "Architectural context window ceiling supported by the model",
        "admitted": "Models meeting both memory and context constraints for local execution",
        "excluded": "Models rejected due to resource deficits, with explicit failure rationales",
        "adapter_interface": "Callable abstraction isolating catalog discovery from environment specifics",
    }


def main() -> None:
    """Run CLI demonstration of manifest-driven model selection."""
    print("=" * 70)
    print("Model-Manifest Selection - Offline Service Adapter (R04-T054)")
    print("=" * 70)

    adapter = SyntheticManifestAdapter()
    selector = ModelManifestSelector(manifest_provider=adapter)

    # Standard Contract Fixture: RAM 6GB, context 1024
    ram_budget = 6.0
    context_req = 1024
    result = selector.select(available_ram_gb=ram_budget, requested_context=context_req)

    print(f"\n1. Evaluation Run (Budget RAM: {ram_budget}GB, Requested Context: {context_req}):")
    print(f"   Admitted IDs: {result['admitted_ids']}")
    print(f"   Excluded IDs: {result['excluded_ids']}")
    for exc in result["excluded"]:
        print(f"   - Excluded '{exc['id']}': {', '.join(exc['reasons'])}")

    print(f"\n2. Notice:")
    print(f"   {result['teaching_note']}")

    print(f"\n3. Unestablished Real-Service Behaviors:")
    for item in ModelManifestSelector.identify_unestablished_behaviors():
        print(f"   * {item}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
