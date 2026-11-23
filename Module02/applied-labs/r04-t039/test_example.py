"""
Unit tests for Symmetric Signed-Int8 Quantizer and Scenario Assessment.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from example import SymmetricInt8Quantizer, APPLIED_QUESTIONS, run_demo


class TestSymmetricQuantizer(unittest.TestCase):

    def test_canonical_quantization_and_exact_reconstruction(self):
        """Values [-1, 0, 1] with scale=0.1 yield [-10, 0, 10] and reconstruct exactly."""
        q = SymmetricInt8Quantizer(scale=0.1)
        inputs = [-1.0, 0.0, 1.0]
        q_vals = q.quantize_array(inputs)
        self.assertEqual(q_vals, [-10, 0, 10])

        recon = q.reconstruct_array(q_vals)
        self.assertEqual(recon, inputs)

    def test_clipping_to_127(self):
        """Value 20 with scale=0.1 clips to 127."""
        q = SymmetricInt8Quantizer(scale=0.1)
        self.assertEqual(q.quantize(20.0), 127)
        self.assertEqual(q.quantize(-20.0), -127)

    def test_nonpositive_scale_rejected(self):
        """Nonpositive scale is rejected with ValueError."""
        with self.assertRaises(ValueError):
            SymmetricInt8Quantizer(scale=0.0)
        with self.assertRaises(ValueError):
            SymmetricInt8Quantizer(scale=-0.1)
        with self.assertRaises(ValueError):
            SymmetricInt8Quantizer(scale=False)

    def test_applied_questions_executable_checks(self):
        """Executable verification of all 3 applied questions."""
        q = SymmetricInt8Quantizer(scale=0.1)

        # Q1 check
        q1_out = q.quantize(5.0)
        self.assertEqual(q1_out, APPLIED_QUESTIONS[0]["answer"]["quantized"])
        self.assertEqual(q.dequantize(q1_out), APPLIED_QUESTIONS[0]["answer"]["reconstructed"])

        # Q2 check
        with self.assertRaises(ValueError):
            SymmetricInt8Quantizer(scale=-0.5)

        # Q3 check: symmetric range bounds
        self.assertEqual(q.quantize(1000.0), 127)
        self.assertEqual(q.quantize(-1000.0), -127)

    def test_deliberate_wrong_result_fails(self):
        """Deliberate wrong assertion fails."""
        q = SymmetricInt8Quantizer(scale=0.1)
        self.assertNotEqual(q.quantize(20.0), 200)


if __name__ == "__main__":
    unittest.main()
