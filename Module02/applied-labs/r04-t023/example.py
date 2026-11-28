"""
Synthetic Model-Manifest Selection — Compare Two Approaches (Teaching Fixture)

NOTE: All model names, RAM requirements, and context limits in this module are
invented teaching fixtures for demonstrating deterministic manifest eligibility
selection in Module 02 Section 3 (Gemma Family Fundamentals). They are NOT
claims about real Gemma models, hardware benchmarks, or cloud services.
"""

from __future__ import annotations

from typing import Any


FIXTURE_DISCLAIMER = (
    "Invented synthetic teaching fixture, not a claim about real models or hardware."
)

SYNTHETIC_MANIFEST: tuple[dict[str, Any], ...] = (
    {"name": "Model-A", "ram_gb": 4, "max_context": 2048},
    {"name": "Model-B", "ram_gb": 8, "max_context": 4096},
)

EXPLICIT_EXPECTED_TABLE: dict[tuple[int, int], tuple[list[str], dict[str, list[str]]]] = {
    (6, 1024): (["Model-A"], {"Model-B": ["ram_exceeds_budget (needs 8 > budget 6)"]}),
    (8, 1024): (["Model-A", "Model-B"], {}),
    (6, 3072): ([], {"Model-A": ["context_below_request (max 2048 < requested 3072)"], "Model-B": ["ram_exceeds_budget (needs 8 > budget 6)"]}),
    (8, 4096): (["Model-B"], {"Model-A": ["context_below_request (max 2048 < requested 4096)"]}),
    (3, 1024): (
        [],
        {
            "Model-A": ["ram_exceeds_budget (needs 4 > budget 3)"],
            "Model-B": ["ram_exceeds_budget (needs 8 > budget 3)"],
        },
    ),
}


def _validate_inputs(
    manifest: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ram_budget_gb: int,
    requested_context: int,
) -> None:
    if isinstance(ram_budget_gb, bool) or not isinstance(ram_budget_gb, int) or ram_budget_gb <= 0:
        raise ValueError("ram_budget_gb must be a positive integer.")
    if isinstance(requested_context, bool) or not isinstance(requested_context, int) or requested_context <= 0:
        raise ValueError("requested_context must be a positive integer.")
    for entry in manifest:
        if "name" not in entry or "ram_gb" not in entry or "max_context" not in entry:
            raise ValueError(f"Manifest entry missing required fields: {entry!r}")


def select_eligible_models(
    manifest: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ram_budget_gb: int,
    requested_context: int,
) -> dict[str, Any]:
    """Direct manifest selection filtering by RAM budget and requested context."""
    _validate_inputs(manifest, ram_budget_gb, requested_context)

    eligible: list[str] = []
    excluded: dict[str, list[str]] = {}

    for entry in manifest:
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


def independent_eligible_calculation(
    manifest: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ram_budget_gb: int,
    requested_context: int,
) -> tuple[list[str], dict[str, list[str]]]:
    """Simpler independent predicate + failure-reason calculation on identical inputs."""
    _validate_inputs(manifest, ram_budget_gb, requested_context)
    admitted = [
        item["name"]
        for item in manifest
        if (item["ram_gb"] <= ram_budget_gb) and (item["max_context"] >= requested_context)
    ]
    rejected: dict[str, list[str]] = {}
    for item in manifest:
        if item["name"] not in admitted:
            item_reasons: list[str] = []
            if not (item["ram_gb"] <= ram_budget_gb):
                item_reasons.append(f"ram_exceeds_budget (needs {item['ram_gb']} > budget {ram_budget_gb})")
            if not (item["max_context"] >= requested_context):
                item_reasons.append(
                    f"context_below_request (max {item['max_context']} < requested {requested_context})"
                )
            rejected[item["name"]] = item_reasons
    return admitted, rejected


def compare_selection_approaches(ram_budget_gb: int, requested_context: int) -> dict[str, Any]:
    """Compare direct manifest selection against independent calculation and expected table."""
    direct = select_eligible_models(SYNTHETIC_MANIFEST, ram_budget_gb, requested_context)
    indep_eligible, indep_excluded = independent_eligible_calculation(
        SYNTHETIC_MANIFEST, ram_budget_gb, requested_context
    )
    matches_independent = (
        direct["eligible"] == indep_eligible and direct["excluded"] == indep_excluded
    )
    table_entry = EXPLICIT_EXPECTED_TABLE.get((ram_budget_gb, requested_context))
    matches_table = (
        table_entry is not None
        and direct["eligible"] == table_entry[0]
        and direct["excluded"] == table_entry[1]
    )
    return {
        "direct": direct,
        "independent": {"eligible": indep_eligible, "excluded": indep_excluded},
        "matches_independent": matches_independent,
        "matches_expected_table": matches_table,
    }


if __name__ == "__main__":
    print("=== R04-T023 Model-Manifest Selection Comparison (Synthetic Fixture) ===")
    for budget_ram, req_ctx in [(6, 1024), (8, 1024), (6, 3072), (8, 4096), (3, 1024)]:
        summary = compare_selection_approaches(budget_ram, req_ctx)
        print(
            f"RAM={budget_ram}, ctx={req_ctx} -> "
            f"eligible={summary['direct']['eligible']}, "
            f"excluded={summary['direct']['excluded']}, "
            f"matches_independent={summary['matches_independent']}, "
            f"matches_table={summary['matches_expected_table']}"
        )
