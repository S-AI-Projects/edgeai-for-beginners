"""
Local Model-File Preflight & Controlled Configuration Experiment (Teaching Fixture)

NOTE: Uses a tiny dummy placeholder file (dummy_model.gguf), NOT real model
weights, and a mock backend launcher callable. Makes NO claims about real
llama.cpp performance, hardware memory, or trained-model accuracy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


FIXTURE_DISCLAIMER = (
    "Local preflight simulation using a tiny dummy file and mock launcher; "
    "makes no claims about real hardware, llama.cpp runtime, or model accuracy."
)
DEFAULT_DUMMY_PATH = Path(__file__).resolve().parent / "dummy_model.gguf"


class PreflightValidationError(ValueError):
    """Raised when local model manifest preflight fails before backend launch."""


def validate_and_launch_manifest(
    manifest: dict[str, Any],
    requested_context: int,
    backend_launcher: Callable[[Path, int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate format, local file existence, and context limit before invoking backend."""
    if isinstance(requested_context, bool) or not isinstance(requested_context, int) or requested_context <= 0:
        raise PreflightValidationError("requested_context must be a positive integer.")

    model_format = str(manifest.get("format", "")).strip().upper()
    if model_format != "GGUF":
        raise PreflightValidationError(
            f"Unsupported model format {manifest.get('format')!r}; expected 'GGUF'."
        )

    raw_path = manifest.get("path")
    if not raw_path:
        raise PreflightValidationError("Missing local model path in manifest.")
    model_path = Path(raw_path)
    if not model_path.is_file():
        raise PreflightValidationError(f"Local model file does not exist: {model_path}")

    max_context = manifest.get("max_context")
    if isinstance(max_context, bool) or not isinstance(max_context, int) or max_context <= 0:
        raise PreflightValidationError(f"Invalid manifest max_context: {max_context!r}")

    if requested_context > max_context:
        raise PreflightValidationError(
            f"Requested context {requested_context} exceeds manifest max_context {max_context}."
        )

    launcher = backend_launcher or (
        lambda path, ctx: {"mock_launched": True, "path": str(path), "context": ctx}
    )
    launch_result = launcher(model_path, requested_context)
    return {
        "accepted": True,
        "format": model_format,
        "path": str(model_path),
        "max_context": max_context,
        "requested_context": requested_context,
        "headroom_tokens": max_context - requested_context,
        "context_utilization": round(requested_context / max_context, 4),
        "launch_result": launch_result,
        "fixture_note": FIXTURE_DISCLAIMER,
    }


def run_controlled_experiment(model_path: Path = DEFAULT_DUMMY_PATH) -> list[dict[str, Any]]:
    """Compare three controlled context configurations on the same GGUF manifest."""
    configs = [
        {"config_id": "small_512", "requested_context": 512, "expected_accepted": True},
        {"config_id": "medium_1024", "requested_context": 1024, "expected_accepted": True},
        {"config_id": "oversized_4096", "requested_context": 4096, "expected_accepted": False},
    ]
    manifest = {"format": "GGUF", "path": str(model_path), "max_context": 2048}
    rows: list[dict[str, Any]] = []

    for cfg in configs:
        launch_calls = 0

        def tracked_launcher(p: Path, ctx: int) -> dict[str, Any]:
            nonlocal launch_calls
            launch_calls += 1
            return {"mock_launched": True, "path": str(p), "context": ctx}

        try:
            res = validate_and_launch_manifest(
                manifest, cfg["requested_context"], backend_launcher=tracked_launcher
            )
            rows.append(
                {
                    "config_id": cfg["config_id"],
                    "requested_context": cfg["requested_context"],
                    "max_context": 2048,
                    "accepted": True,
                    "correct": cfg["expected_accepted"] is True,
                    "headroom_tokens": res["headroom_tokens"],
                    "context_utilization": res["context_utilization"],
                    "launch_calls": launch_calls,
                }
            )
        except PreflightValidationError as exc:
            rows.append(
                {
                    "config_id": cfg["config_id"],
                    "requested_context": cfg["requested_context"],
                    "max_context": 2048,
                    "accepted": False,
                    "correct": cfg["expected_accepted"] is False,
                    "headroom_tokens": 2048 - cfg["requested_context"],
                    "context_utilization": round(cfg["requested_context"] / 2048, 4),
                    "launch_calls": launch_calls,
                    "error": str(exc),
                }
            )
    return rows


if __name__ == "__main__":
    print("=== R04-T029 Local Model-File Preflight & Controlled Experiment ===")
    for row in run_controlled_experiment():
        print(
            f"[{row['config_id']}] req={row['requested_context']}/2048 -> "
            f"accepted={row['accepted']}, correct={row['correct']}, "
            f"utilization={row['context_utilization']}, headroom={row['headroom_tokens']}, "
            f"launch_calls={row['launch_calls']}"
        )
