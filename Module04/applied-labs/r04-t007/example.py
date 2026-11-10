#!/usr/bin/env python3
"""
Local Model-File Preflight - Worked Example with Checks (R04-T007)
Module 04: Llama.cpp Implementation Guide

Concept:
Before invoking native execution backends (e.g. `./build/bin/main` in llama.cpp),
applications must validate the model manifest locally. Checks verify:
1. Model container format is GGUF.
2. The referenced model file physically exists on the local path.
3. The requested inference context does not exceed the model's max context limit.

Notice:
Uses a lightweight dummy file (header placeholder) rather than gigabytes of
actual neural network weight tensors.
"""

import os
from typing import Dict, Any


def create_dummy_gguf_file(file_path: str) -> str:
    """Creates a minimal dummy file representing a GGUF artifact."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "wb") as f:
        # Magic bytes 'GGUF' + version 3
        f.write(b"GGUF\x03\x00\x00\x00_DUMMY_WEIGHTS_PLACEHOLDER_")
    return file_path


class LocalModelManifestValidator:
    """
    Validates model manifests before triggering llama.cpp or other edge inference runtimes.
    """

    def validate_and_preflight(
        self, manifest: Dict[str, Any], requested_context: int
    ) -> Dict[str, Any]:
        """
        Performs read-only validation against the model manifest.
        Raises ValueError or FileNotFoundError if requirements fail.
        """
        # 1. Format validation
        model_format = manifest.get("format", "").upper()
        if model_format != "GGUF":
            raise ValueError(f"Unsupported model format '{model_format}'. Expected 'GGUF'.")

        # 2. Local path existence validation
        model_path = manifest.get("path")
        if not model_path or not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Model file not found at '{model_path}'. Preflight failed before backend invocation."
            )

        # 3. Context boundary validation
        max_context = int(manifest.get("max_context", 2048))
        if requested_context <= 0:
            raise ValueError(f"Requested context must be positive, got {requested_context}.")

        if requested_context > max_context:
            raise ValueError(
                f"Requested context {requested_context} exceeds maximum model context limit {max_context}."
            )

        return {
            "status": "ACCEPTED",
            "format": "GGUF",
            "model_path": model_path,
            "max_context": max_context,
            "requested_context": requested_context,
            "allocated_context": requested_context,
            "backend_ready": True,
            "simulation_note": (
                "Preflight validation only. Uses local dummy file, does not load real "
                "weight tensors or allocate GPU VRAM."
            ),
        }


def run_demo() -> None:
    print("=== Module 04: Llama.cpp Local Model Preflight Demo ===")
    validator = LocalModelManifestValidator()

    dummy_path = "/tmp/demo_models/phi-4-mini-q4_0.gguf"
    create_dummy_gguf_file(dummy_path)

    manifest = {
        "format": "GGUF",
        "path": dummy_path,
        "max_context": 2048,
        "model_id": "phi-4-mini",
    }

    # Case 1: Valid request (1024 <= 2048)
    res_valid = validator.validate_and_preflight(manifest, requested_context=1024)
    print(f"Request 1024: Status = {res_valid['status']}, Context = {res_valid['allocated_context']}")

    # Case 2: Excessive request (4096 > 2048)
    try:
        validator.validate_and_preflight(manifest, requested_context=4096)
    except ValueError as err:
        print(f"Request 4096: Correctly rejected -> {err}")

    # Case 3: Missing path
    bad_manifest = dict(manifest, path="/tmp/non_existent_model.gguf")
    try:
        validator.validate_and_preflight(bad_manifest, requested_context=1024)
    except FileNotFoundError as err:
        print(f"Missing File: Correctly rejected -> {err}")


if __name__ == "__main__":
    run_demo()
