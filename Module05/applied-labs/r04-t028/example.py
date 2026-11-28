"""
Trainable-Parameter Accounting — Failure and Recovery Example (Synthetic Fixture)

NOTE: This module uses synthetic named-parameter manifests (e.g., encoder:100,
head:20) to illustrate prefix-based layer freezing, invalid/missing-data failure
handling, and clean recovery on the next valid input. It does NOT load real
model weights, PyTorch tensors, or GPU hardware.
"""

from __future__ import annotations

from typing import Any


FIXTURE_DISCLAIMER = (
    "Synthetic named-parameter manifest fixture, not real model weights or GPU memory accounting."
)


class ManifestValidationError(ValueError):
    """Raised when a parameter manifest or freeze prefix configuration is missing or invalid."""


def account_parameters(
    manifest: dict[str, int] | None,
    freeze_prefixes: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Count total/trainable/frozen parameters and report unmatched freeze prefixes.

    Raises:
        ManifestValidationError: If manifest is None/empty, contains non-int or
            negative parameter counts, or freeze_prefixes contains an empty prefix.
    """
    if not manifest or not isinstance(manifest, dict):
        raise ManifestValidationError(
            "Manifest is missing or empty; provide at least one named parameter entry."
        )

    for prefix in freeze_prefixes:
        if not isinstance(prefix, str) or not prefix.strip():
            raise ManifestValidationError(f"Freeze prefix must be a non-empty string; got {prefix!r}.")

    total = 0
    frozen = 0
    trainable = 0
    matched_prefixes: set[str] = set()

    for name, count in manifest.items():
        if not isinstance(name, str) or not name.strip():
            raise ManifestValidationError(f"Invalid parameter name: {name!r}.")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ManifestValidationError(
                f"Parameter {name!r} has invalid count {count!r}; expected non-negative int."
            )
        total += count
        hits = [p for p in freeze_prefixes if name.startswith(p)]
        if hits:
            frozen += count
            matched_prefixes.update(hits)
        else:
            trainable += count

    unmatched_prefixes = [p for p in freeze_prefixes if p not in matched_prefixes]
    return {
        "total": total,
        "trainable": trainable,
        "frozen": frozen,
        "unmatched_prefixes": unmatched_prefixes,
        "fixture_note": FIXTURE_DISCLAIMER,
    }


def process_manifest_stream(
    batches: list[tuple[str, dict[str, int] | None, list[str]]],
) -> list[dict[str, Any]]:
    """Process a sequence of manifests, capturing errors without aborting recovery on valid inputs."""
    outcomes: list[dict[str, Any]] = []
    for label, manifest, prefixes in batches:
        try:
            result = account_parameters(manifest, prefixes)
            outcomes.append({"label": label, "status": "ok", "result": result})
        except ManifestValidationError as exc:
            outcomes.append({"label": label, "status": "error", "error": str(exc)})
    return outcomes


if __name__ == "__main__":
    print("=== R04-T028 Trainable-Parameter Accounting — Failure & Recovery ===")
    stream = [
        ("invalid_missing_manifest", None, ["encoder"]),
        ("invalid_negative_count", {"encoder": -10, "head": 20}, ["encoder"]),
        ("recovery_valid_fixture", {"encoder": 100, "head": 20}, ["encoder"]),
        ("unmatched_prefix_case", {"encoder": 100, "head": 20}, ["encoder", "decoder"]),
    ]
    for entry in process_manifest_stream(stream):
        if entry["status"] == "error":
            print(f"[{entry['label']}] ERROR: {entry['error']}")
        else:
            res = entry["result"]
            print(
                f"[{entry['label']}] OK: total={res['total']}, trainable={res['trainable']}, "
                f"frozen={res['frozen']}, unmatched={res['unmatched_prefixes']}"
            )
