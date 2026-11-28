"""
Synthetic Model-Manifest Selection — Worked Example with Regression Checks (Teaching Fixture)

NOTE: All model entries, RAM values, and context limits are invented teaching
fixtures illustrating Module 02 Section 1 (Microsoft Phi Model Family Fundamentals).
They are NOT claims about real Phi models, device memory, or benchmark accuracy.
"""

from __future__ import annotations

from typing import Any


FIXTURE_DISCLAIMER = (
    "Invented synthetic teaching fixture, not a claim about real Phi models or hardware."
)

WORKED_MANIFEST: tuple[dict[str, Any], ...] = (
    {"name": "Model-A", "ram_gb": 4, "max_context": 2048},
    {"name": "Model-B", "ram_gb": 8, "max_context": 4096},
)

WORKED_INPUT = {
    "manifest": WORKED_MANIFEST,
    "ram_budget_gb": 6,
    "requested_context": 1024,
}

EXPECTED_WORKED_OUTPUT = {
    "eligible": ["Model-A"],
    "excluded": {
        "Model-B": ["ram_exceeds_budget (needs 8 > budget 6)"],
    },
    "ram_budget_gb": 6,
    "requested_context": 1024,
    "fixture_note": FIXTURE_DISCLAIMER,
}


def select_eligible_models(
    manifest: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ram_budget_gb: int,
    requested_context: int,
) -> dict[str, Any]:
    """Evaluate synthetic manifest entries against RAM budget and requested context."""
    if isinstance(ram_budget_gb, bool) or not isinstance(ram_budget_gb, int) or ram_budget_gb <= 0:
        raise ValueError("ram_budget_gb must be a positive integer.")
    if isinstance(requested_context, bool) or not isinstance(requested_context, int) or requested_context <= 0:
        raise ValueError("requested_context must be a positive integer.")

    eligible: list[str] = []
    excluded: dict[str, list[str]] = {}

    for entry in manifest:
        if "name" not in entry or "ram_gb" not in entry or "max_context" not in entry:
            raise ValueError(f"Manifest entry missing required fields: {entry!r}")

        reasons: list[str] = []
        if entry["ram_gb"] > ram_budget_gb:
            reasons.append(f"ram_exceeds_budget (needs {entry['ram_gb']} > budget {ram_budget_gb})")
        if entry["max_context"] < requested_context:
            reasons.append(
                f"context_below_request (max {entry['max_context']} < requested {requested_context})"
            )

        if reasons:
            excluded[entry["name"]] = reasons
        else:
            eligible.append(entry["name"])

    return {
        "eligible": eligible,
        "excluded": excluded,
        "ram_budget_gb": ram_budget_gb,
        "requested_context": requested_context,
        "fixture_note": FIXTURE_DISCLAIMER,
    }


def run_worked_example() -> dict[str, Any]:
    """Execute the exact published worked example input-to-output."""
    return select_eligible_models(
        manifest=WORKED_INPUT["manifest"],
        ram_budget_gb=WORKED_INPUT["ram_budget_gb"],
        requested_context=WORKED_INPUT["requested_context"],
    )


if __name__ == "__main__":
    print("=== R04-T027 Worked Model-Manifest Selection (Synthetic Fixture) ===")
    actual = run_worked_example()
    print("Input: ram_budget_gb=6, requested_context=1024")
    print("Output:", actual)
    assert actual == EXPECTED_WORKED_OUTPUT
