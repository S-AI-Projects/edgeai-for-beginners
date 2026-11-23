"""
Model-Manifest Selection with Malformed Data Failure and Recovery.

Selects eligible entries from a local synthetic model manifest using explicit
RAM and context requirements.
Handles malformed/missing manifest fields with structured errors and demonstrates
clean recovery on subsequent valid inputs.
"""

from typing import Dict, Any, List, Optional
import json


class ManifestValidationError(Exception):
    """Raised when a manifest entry has missing or invalid schema fields."""
    def __init__(self, message: str, entry: Dict[str, Any]):
        super().__init__(message)
        self.message = message
        self.entry = entry


class ResilientManifestSelector:
    """Selects eligible models while cleanly handling malformed manifest entries."""

    @staticmethod
    def validate_entry(entry: Any) -> None:
        """Validates that a manifest entry has required fields and correct types."""
        if not isinstance(entry, dict):
            raise ManifestValidationError("Manifest entry must be a dictionary", entry)

        required_fields = ["id", "required_ram_gb", "max_context"]
        for field in required_fields:
            if field not in entry:
                raise ManifestValidationError(f"Missing required field: '{field}'", entry)

        if not isinstance(entry["id"], str):
            raise ManifestValidationError("Field 'id' must be a string", entry)

        if not isinstance(entry["required_ram_gb"], (int, float)) or isinstance(entry["required_ram_gb"], bool):
            raise ManifestValidationError("Field 'required_ram_gb' must be numeric", entry)

        if not isinstance(entry["max_context"], int) or isinstance(entry["max_context"], bool):
            raise ManifestValidationError("Field 'max_context' must be an integer", entry)

    def select(self, manifest: List[Dict[str, Any]], available_ram_gb: float, requested_context: int) -> Dict[str, Any]:
        """
        Processes manifest. If a malformed entry is encountered, reports structured error.
        When valid manifest is provided, successfully filters eligible entries.
        """
        eligible: List[Dict[str, Any]] = []
        excluded: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for entry in manifest:
            try:
                self.validate_entry(entry)
            except ManifestValidationError as e:
                errors.append({
                    "error": "MALFORMED_MANIFEST_ENTRY",
                    "message": e.message,
                    "raw_entry": e.entry
                })
                continue

            ram_ok = entry["required_ram_gb"] <= available_ram_gb
            context_ok = entry["max_context"] >= requested_context

            reasons: List[str] = []
            if not ram_ok:
                reasons.append(
                    f"Required RAM {entry['required_ram_gb']}GB exceeds budget {available_ram_gb}GB"
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
            "eligible": eligible,
            "excluded": excluded,
            "errors": errors
        }


def run_demo() -> Dict[str, Any]:
    selector = ResilientManifestSelector()

    # Step 1: Malformed input scenario (missing 'max_context')
    malformed_manifest = [
        {"id": "Corrupted-Entry", "required_ram_gb": 4}
    ]
    failed_result = selector.select(malformed_manifest, available_ram_gb=6, requested_context=1024)

    # Step 2: Recovery with canonical valid fixture
    valid_manifest = [
        {"id": "Fixture-A", "required_ram_gb": 4, "max_context": 2048},
        {"id": "Fixture-B", "required_ram_gb": 8, "max_context": 4096},
    ]
    recovered_result = selector.select(valid_manifest, available_ram_gb=6, requested_context=1024)

    return {
        "step_1_failure": failed_result,
        "step_2_recovery": recovered_result
    }


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
