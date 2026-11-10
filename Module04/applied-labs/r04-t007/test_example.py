"""
Unit Tests for Local Model Preflight (R04-T007)
Module 04: Llama.cpp Implementation Guide
"""

import os
import tempfile
import unittest

try:
    from .example import LocalModelManifestValidator, create_dummy_gguf_file
except ImportError:
    from example import LocalModelManifestValidator, create_dummy_gguf_file


class TestLocalModelManifestValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dummy_path = os.path.join(self.temp_dir.name, "test_model.gguf")
        create_dummy_gguf_file(self.dummy_path)

        self.validator = LocalModelManifestValidator()
        self.manifest = {
            "format": "GGUF",
            "path": self.dummy_path,
            "max_context": 2048,
            "model_id": "test-gguf-model",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_accepts_valid_context_1024(self):
        """GGUF manifest with max_context=2048 accepts request 1024."""
        result = self.validator.validate_and_preflight(
            self.manifest, requested_context=1024
        )
        self.assertEqual(result["status"], "ACCEPTED")
        self.assertEqual(result["allocated_context"], 1024)
        self.assertEqual(result["max_context"], 2048)
        self.assertTrue(result["backend_ready"])

    def test_rejects_excessive_context_4096(self):
        """GGUF manifest with max_context=2048 rejects request 4096."""
        with self.assertRaises(ValueError) as ctx:
            self.validator.validate_and_preflight(
                self.manifest, requested_context=4096
            )
        self.assertIn("exceeds maximum model context limit", str(ctx.exception))

    def test_missing_local_model_path_fails(self):
        """A missing local model path fails with FileNotFoundError without launching anything."""
        missing_manifest = dict(
            self.manifest,
            path=os.path.join(self.temp_dir.name, "does_not_exist.gguf"),
        )
        with self.assertRaises(FileNotFoundError) as ctx:
            self.validator.validate_and_preflight(
                missing_manifest, requested_context=1024
            )
        self.assertIn("Model file not found", str(ctx.exception))

    def test_non_gguf_format_rejected(self):
        """Non-GGUF format is rejected."""
        non_gguf_manifest = dict(self.manifest, format="ONNX")
        with self.assertRaises(ValueError) as ctx:
            self.validator.validate_and_preflight(
                non_gguf_manifest, requested_context=1024
            )
        self.assertIn("Unsupported model format", str(ctx.exception))

    def test_zero_or_negative_context_rejected(self):
        """Non-positive context requests are rejected."""
        with self.assertRaises(ValueError):
            self.validator.validate_and_preflight(
                self.manifest, requested_context=0
            )
        with self.assertRaises(ValueError):
            self.validator.validate_and_preflight(
                self.manifest, requested_context=-128
            )


if __name__ == "__main__":
    unittest.main()
