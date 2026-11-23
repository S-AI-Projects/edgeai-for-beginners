"""
Model-Manifest Selection with Offline Service Adapter.

Abstracts external model catalog / discovery services behind a callable
interface (ModelCatalogService) and provides a deterministic local offline adapter
(OfflineModelCatalogAdapter).
Filters candidates according to RAM budget and requested context window length.
Documents what real-world service behavior this mock does not establish.
"""

from typing import Dict, Any, List, Protocol
import json


class ModelCatalogService(Protocol):
    """Callable interface protocol for model catalog lookup."""
    def fetch_manifest(self) -> List[Dict[str, Any]]:
        ...


class OfflineModelCatalogAdapter:
    """
    Deterministic offline adapter satisfying the ModelCatalogService protocol.
    Serves local fixtures without network latency, authentication, or remote downtime.
    """
    def __init__(self, fixtures: List[Dict[str, Any]]):
        self._fixtures = list(fixtures)

    def fetch_manifest(self) -> List[Dict[str, Any]]:
        return list(self._fixtures)


class ManifestSelector:
    """Selects eligible models retrieved via a ModelCatalogService."""

    def __init__(self, catalog_service: ModelCatalogService):
        self.catalog_service = catalog_service

    def select_models(self, available_ram_gb: float, requested_context: int) -> Dict[str, Any]:
        manifest = self.catalog_service.fetch_manifest()
        eligible: List[Dict[str, Any]] = []
        excluded: List[Dict[str, Any]] = []

        for entry in manifest:
            ram_ok = entry["required_ram_gb"] <= available_ram_gb
            context_ok = entry["max_context"] >= requested_context

            reasons: List[str] = []
            if not ram_ok:
                reasons.append(
                    f"Required RAM {entry['required_ram_gb']}GB exceeds available {available_ram_gb}GB"
                )
            if not context_ok:
                reasons.append(
                    f"Max context {entry['max_context']} is less than requested {requested_context}"
                )

            if ram_ok and context_ok:
                eligible.append(entry)
            else:
                excluded.append({
                    "model_id": entry["id"],
                    "reasons": reasons
                })

        return {
            "available_ram_gb": available_ram_gb,
            "requested_context": requested_context,
            "eligible": eligible,
            "excluded": excluded
        }


def run_demo() -> Dict[str, Any]:
    fixtures = [
        {"id": "Fixture-A", "required_ram_gb": 4, "max_context": 2048},
        {"id": "Fixture-B", "required_ram_gb": 8, "max_context": 4096},
    ]
    adapter = OfflineModelCatalogAdapter(fixtures)
    selector = ManifestSelector(adapter)
    # Budget RAM 6 and requested context 1024 admits only Fixture A
    return selector.select_models(available_ram_gb=6, requested_context=1024)


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
