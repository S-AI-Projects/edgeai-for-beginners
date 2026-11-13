#!/usr/bin/env python3
"""
Unit tests for Symmetric Signed-INT8 Quantizer (R04-T053)
Module 02: BitNET Family Fundamentals (04.BitNETFamily.md)
"""

import unittest
from example import (
    SymmetricInt8Quantizer,
    compare_approaches,
    explain_mapping,
    reference_dequantize,
    reference_pipeline,
    reference_quantize,
)


class TestSymmetricInt8Quantizer(unittest.TestCase):
    """Test suite verifying contract compliance of SymmetricInt8Quantizer and approach comparison."""

    def setUp(self) -> None:
        """Initialize standard test quantizer with scale=0.1."""
        self.quantizer = SymmetricInt8Quantizer(scale=0.1)

    # -----------------------------------------------------------------
    # Primary Contract Requirements
    # -----------------------------------------------------------------
    def test_exact_reconstruction_values(self) -> None:
        """Values [-1, 0, 1] with scale=0.1 yield [-10, 0, 10] and reconstruct exactly."""
        inputs = [-1.0, 0.0, 1.0]
        q_vals = self.quantizer.quantize_sequence(inputs)
        self.assertEqual(q_vals, [-10, 0, 10])

        recon_vals = self.quantizer.dequantize_sequence(q_vals)
        self.assertEqual(recon_vals, [-1.0, 0.0, 1.0])

        # Verify through full process pipeline
        result = self.quantizer.process(inputs)
        self.assertEqual(result["quantized"], [-10, 0, 10])
        self.assertEqual(result["reconstructed"], [-1.0, 0.0, 1.0])
        self.assertEqual(result["errors"], [0.0, 0.0, 0.0])
        self.assertEqual(result["max_error"], 0.0)

    def test_value_20_clips_to_127(self) -> None:
        """Value 20 with scale=0.1 clips to 127 and reconstructs to 12.7."""
        q_val = self.quantizer.quantize(20.0)
        self.assertEqual(q_val, 127)

        recon_val = self.quantizer.dequantize(q_val)
        self.assertEqual(recon_val, 12.7)

    def test_negative_value_clips_to_minus_127(self) -> None:
        """Value -20 with scale=0.1 clips to -127 and reconstructs to -12.7."""
        q_val = self.quantizer.quantize(-20.0)
        self.assertEqual(q_val, -127)

        recon_val = self.quantizer.dequantize(q_val)
        self.assertEqual(recon_val, -12.7)

    def test_nonpositive_scale_rejected(self) -> None:
        """Nonpositive scale values (0 or negative) must raise ValueError."""
        with self.assertRaises(ValueError) as ctx_zero:
            SymmetricInt8Quantizer(scale=0.0)
        self.assertIn("positive", str(ctx_zero.exception).lower())

        with self.assertRaises(ValueError) as ctx_neg:
            SymmetricInt8Quantizer(scale=-0.1)
        self.assertIn("positive", str(ctx_neg.exception).lower())

        with self.assertRaises(ValueError):
            reference_quantize(1.0, scale=0.0)

    # -----------------------------------------------------------------
    # Boundary and Rounding Tests
    # -----------------------------------------------------------------
    def test_exact_clipping_boundary(self) -> None:
        """Exact clipping boundaries 12.7 and -12.7 map to 127 and -127 without saturation error."""
        self.assertEqual(self.quantizer.quantize(12.7), 127)
        self.assertEqual(self.quantizer.quantize(-12.7), -127)
        self.assertEqual(self.quantizer.dequantize(127), 12.7)
        self.assertEqual(self.quantizer.dequantize(-127), -12.7)

    def test_zero_preservation(self) -> None:
        """Zero maps to zero and reconstructs exactly."""
        self.assertEqual(self.quantizer.quantize(0.0), 0)
        self.assertEqual(self.quantizer.dequantize(0), 0.0)

    def test_dequantize_out_of_bounds_rejected(self) -> None:
        """Quantized integer outside [-127, 127] raises ValueError on dequantize."""
        with self.assertRaises(ValueError):
            self.quantizer.dequantize(128)
        with self.assertRaises(ValueError):
            self.quantizer.dequantize(-128)

    # -----------------------------------------------------------------
    # Focus: Compare Two Approaches on Identical Inputs
    # -----------------------------------------------------------------
    def test_two_approaches_comparison_exact_inputs(self) -> None:
        """Direct and Reference approaches yield identical quantization and reconstruction on [-1, 0, 1]."""
        test_inputs = [-1.0, 0.0, 1.0]
        scale = 0.1

        comparison = compare_approaches(test_inputs, scale=scale)
        self.assertTrue(comparison["identical_quantization"])
        self.assertTrue(comparison["identical_reconstruction"])
        self.assertTrue(comparison["all_match"])
        self.assertEqual(comparison["direct"]["quantized"], comparison["reference"]["quantized"])
        self.assertEqual(comparison["direct"]["reconstructed"], comparison["reference"]["reconstructed"])

    def test_two_approaches_comparison_extended_inputs(self) -> None:
        """Direct and Reference approaches agree across mixed, clipping, and fractional inputs."""
        test_inputs = [-20.0, -12.7, -1.0, -0.05, 0.0, 0.05, 1.0, 12.7, 20.0]
        scale = 0.1

        comparison = compare_approaches(test_inputs, scale=scale)
        self.assertTrue(comparison["all_match"])
        for row in comparison["comparison_table"]:
            self.assertTrue(row["q_match"], f"Quantization mismatch at input {row['input']}")
            self.assertTrue(row["recon_match"], f"Reconstruction mismatch at input {row['input']}")

    def test_concept_mapping_coverage(self) -> None:
        """Ensure all primary quantizer concepts are defined in explain_mapping."""
        mapping = explain_mapping()
        for key in ["scale", "quantize", "dequantize", "clipping", "reconstruction_error", "approach_comparison"]:
            self.assertIn(key, mapping)


if __name__ == "__main__":
    unittest.main()
