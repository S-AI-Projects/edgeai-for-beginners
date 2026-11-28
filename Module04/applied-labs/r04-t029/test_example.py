from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    DEFAULT_DUMMY_PATH,
    FIXTURE_DISCLAIMER,
    PreflightValidationError,
    run_controlled_experiment,
    validate_and_launch_manifest,
)


class TestLlamaCppManifestPreflight(unittest.TestCase):
    def test_gguf_manifest_accepts_1024_and_launches_once(self):
        """GGUF manifest with max_context=2048 accepts request 1024 and invokes launcher once."""
        launched = []

        def spy_launcher(path: Path, ctx: int) -> dict:
            launched.append((path, ctx))
            return {"launched": True}

        manifest = {"format": "GGUF", "path": str(DEFAULT_DUMMY_PATH), "max_context": 2048}
        result = validate_and_launch_manifest(manifest, requested_context=1024, backend_launcher=spy_launcher)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["headroom_tokens"], 1024)
        self.assertEqual(result["context_utilization"], 0.5)
        self.assertEqual(len(launched), 1)
        self.assertEqual(result["fixture_note"], FIXTURE_DISCLAIMER)

    def test_exact_boundary_2048_accepted(self):
        """Exact boundary requested_context == max_context (2048) is accepted with 0 headroom."""
        manifest = {"format": "GGUF", "path": str(DEFAULT_DUMMY_PATH), "max_context": 2048}
        result = validate_and_launch_manifest(manifest, requested_context=2048)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["headroom_tokens"], 0)
        self.assertEqual(result["context_utilization"], 1.0)

    def test_request_4096_rejected_without_launching(self):
        """Request 4096 exceeds max_context=2048 and rejects without launching backend."""
        launched = []
        manifest = {"format": "GGUF", "path": str(DEFAULT_DUMMY_PATH), "max_context": 2048}
        with self.assertRaises(PreflightValidationError):
            validate_and_launch_manifest(
                manifest,
                requested_context=4096,
                backend_launcher=lambda p, c: launched.append((p, c)) or {},
            )
        self.assertEqual(launched, [])

    def test_missing_model_path_fails_without_launching(self):
        """Missing local model path fails preflight before any launcher call."""
        launched = []
        missing_path = DEFAULT_DUMMY_PATH.parent / "nonexistent_weights.gguf"
        manifest = {"format": "GGUF", "path": str(missing_path), "max_context": 2048}
        with self.assertRaises(PreflightValidationError):
            validate_and_launch_manifest(
                manifest,
                requested_context=1024,
                backend_launcher=lambda p, c: launched.append((p, c)) or {},
            )
        self.assertEqual(launched, [])

    def test_unsupported_format_rejected_without_launching(self):
        launched = []
        manifest = {"format": "SAFETENSORS", "path": str(DEFAULT_DUMMY_PATH), "max_context": 2048}
        with self.assertRaises(PreflightValidationError):
            validate_and_launch_manifest(
                manifest,
                requested_context=1024,
                backend_launcher=lambda p, c: launched.append((p, c)) or {},
            )
        self.assertEqual(launched, [])

    def test_controlled_three_config_experiment_correctness_and_tradeoff(self):
        """Three controlled configurations report expected correctness and headroom trade-offs."""
        rows = run_controlled_experiment()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["correct"] for r in rows))
        self.assertEqual([r["accepted"] for r in rows], [True, True, False])
        self.assertEqual([r["launch_calls"] for r in rows], [1, 1, 0])
        self.assertGreater(rows[0]["headroom_tokens"], rows[1]["headroom_tokens"])


if __name__ == "__main__":
    unittest.main()
