"""
Unit tests for R04-T019 Quantization Error Budget.
"""

import unittest

from example import (
    QuantizationError,
    compare_three_configurations,
    dequantize_value,
    quantize_and_reconstruct,
    quantize_value,
    run_concept_example,
)


class TestQuantizationNormal(unittest.TestCase):
    def test_canonical_values_yield_exact_reconstruction(self):
        """Values [-1, 0, 1], scale=0.1 yield [-10, 0, 10] and reconstruct exactly."""
        res = quantize_and_reconstruct([-1.0, 0.0, 1.0], 0.1)
        self.assertEqual(res["quantized"], [-10, 0, 10])
        self.assertEqual(res["reconstructed"], [-1.0, 0.0, 1.0])
        self.assertEqual(res["clipping_count"], 0)
        self.assertEqual(res["mean_absolute_error"], 0.0)

    def test_canonical_value_twenty_clips_to_127(self):
        """Value 20 with scale=0.1 clips to 127."""
        q = quantize_value(20.0, 0.1)
        self.assertEqual(q, 127)
        rec = dequantize_value(q, 0.1)
        self.assertEqual(rec, 12.7)

    def test_negative_clipping_bound(self):
        """Value -20 with scale=0.1 clips to -127."""
        q = quantize_value(-20.0, 0.1)
        self.assertEqual(q, -127)
        rec = dequantize_value(q, 0.1)
        self.assertEqual(rec, -12.7)

    def test_run_concept_example_summary(self):
        summary = run_concept_example()
        self.assertEqual(summary["canonical_quantized"], [-10, 0, 10])
        self.assertTrue(summary["canonical_exact"])
        self.assertEqual(summary["clip_quantized"], 127)
        self.assertTrue(summary["rejected_zero"])
        self.assertTrue(summary["rejected_negative"])


class TestValidationAndBoundaries(unittest.TestCase):
    def test_reject_nonpositive_scales(self):
        """Scale <= 0 must be rejected with INVALID_SCALE."""
        for bad_scale in (0, 0.0, -0.1, -5.0):
            with self.assertRaises(QuantizationError) as ctx:
                quantize_value(1.0, bad_scale)
            self.assertEqual(ctx.exception.code, "INVALID_SCALE")

    def test_int8_symmetric_bounds_clamping(self):
        """Values must never exceed [-127, 127]."""
        self.assertEqual(quantize_value(1000.0, 0.1), 127)
        self.assertEqual(quantize_value(-1000.0, 0.1), -127)
        self.assertEqual(quantize_value(12.7, 0.1), 127)
        self.assertEqual(quantize_value(-12.7, 0.1), -127)

    def test_invalid_input_types(self):
        for bad_val in ("1.0", None, True, [1]):
            with self.assertRaises(QuantizationError) as ctx:
                quantize_value(bad_val, 0.1)
            self.assertEqual(ctx.exception.code, "INVALID_INPUT")


class TestControlledConfigurationComparison(unittest.TestCase):
    def test_three_configurations_tradeoffs(self):
        """Compare 3 controlled configurations: verifies clipping vs precision trade-off."""
        results = compare_three_configurations()
        self.assertEqual(len(results), 3)

        cfg_a, cfg_b, cfg_c = results[0], results[1], results[2]
        # Fine scale (0.01) clips on out-of-range elements (-20, 20)
        self.assertEqual(cfg_a["clipping_count"], 2)
        # Balanced scale (0.1) clips on (-20, 20)
        self.assertEqual(cfg_b["clipping_count"], 2)
        # Coarse scale (1.0) has dynamic range up to 127, so zero clipping on 20
        self.assertEqual(cfg_c["clipping_count"], 0)


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_asymmetric_bounds_fails(self):
        """A quantizer clipping to asymmetric 128 instead of 127 must fail assertion."""
        flawed_q = 128
        with self.assertRaises(AssertionError):
            self.assertEqual(flawed_q, 127)

    def test_flawed_zero_scale_acceptance_fails(self):
        """A flawed implementation that accepts zero scale produces ZeroDivisionError or wrong result."""
        def flawed_quantize(x, scale):
            return x / scale

        with self.assertRaises(ZeroDivisionError):
            flawed_quantize(1.0, 0.0)


if __name__ == "__main__":
    unittest.main()
