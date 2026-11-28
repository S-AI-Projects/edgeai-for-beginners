"""
Trainable-Parameter Accounting — Baseline vs Refactored Responsibility (Synthetic Fixture)

NOTE: This module uses small synthetic named-parameter manifests (e.g.
encoder:100, head:20) to illustrate prefix-based layer freezing during fine-tuning.
It does NOT load PyTorch weights, GPU tensors, or real SLM checkpoints.
"""

from __future__ import annotations

from typing import Any


FIXTURE_DISCLAIMER = (
    "Synthetic named-parameter manifest fixture, not real model weights or GPU memory accounting."
)


def _validate_manifest_and_prefixes(
    manifest: dict[str, int],
    freeze_prefixes: list[str] | tuple[str, ...],
) -> None:
    if not isinstance(manifest, dict):
        raise TypeError("manifest must be a dict mapping parameter name to integer count.")
    for name, count in manifest.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Invalid parameter name: {name!r}")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"Invalid parameter count for {name!r}: {count!r}")
    for prefix in freeze_prefixes:
        if not isinstance(prefix, str) or not prefix:
            raise ValueError(f"Freeze prefix must be a non-empty string: {prefix!r}")


def account_parameters_baseline(
    manifest: dict[str, int],
    freeze_prefixes: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Monolithic baseline computing total, trainable, frozen counts and unmatched prefixes."""
    _validate_manifest_and_prefixes(manifest, freeze_prefixes)

    total = 0
    frozen = 0
    trainable = 0
    matched_prefixes: set[str] = set()

    for name, count in manifest.items():
        total += count
        matched = [p for p in freeze_prefixes if name.startswith(p)]
        if matched:
            frozen += count
            matched_prefixes.update(matched)
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


def classify_freeze_matches(
    param_names: list[str] | tuple[str, ...],
    freeze_prefixes: list[str] | tuple[str, ...],
) -> tuple[set[str], list[str]]:
    """Extracted responsibility: determine which parameter names freeze and which prefixes go unmatched."""
    frozen_names: set[str] = set()
    matched_prefixes: set[str] = set()
    for name in param_names:
        hits = [p for p in freeze_prefixes if name.startswith(p)]
        if hits:
            frozen_names.add(name)
            matched_prefixes.update(hits)
    unmatched = [p for p in freeze_prefixes if p not in matched_prefixes]
    return frozen_names, unmatched


def account_parameters_refactored(
    manifest: dict[str, int],
    freeze_prefixes: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Refactored parameter accounting delegating prefix matching to classify_freeze_matches."""
    _validate_manifest_and_prefixes(manifest, freeze_prefixes)

    frozen_names, unmatched_prefixes = classify_freeze_matches(
        list(manifest.keys()), freeze_prefixes
    )
    total = sum(manifest.values())
    frozen = sum(count for name, count in manifest.items() if name in frozen_names)
    trainable = total - frozen

    return {
        "total": total,
        "trainable": trainable,
        "frozen": frozen,
        "unmatched_prefixes": unmatched_prefixes,
        "fixture_note": FIXTURE_DISCLAIMER,
    }


if __name__ == "__main__":
    fixture = {"encoder": 100, "head": 20}
    print("=== R04-T026 Trainable-Parameter Accounting (Baseline vs Refactored) ===")
    for prefixes in (["encoder"], ["encoder", "adapter"], []):
        base = account_parameters_baseline(fixture, prefixes)
        ref = account_parameters_refactored(fixture, prefixes)
        print(
            f"freeze={prefixes} -> total={ref['total']}, trainable={ref['trainable']}, "
            f"frozen={ref['frozen']}, unmatched={ref['unmatched_prefixes']}, equivalent={base == ref}"
        )
