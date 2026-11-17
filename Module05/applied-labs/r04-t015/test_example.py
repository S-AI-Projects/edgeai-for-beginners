"""
Unit tests for R04-T015 Teacher/Student Probability Comparison.
Tests normal fixture values, distribution validation, adapter abstraction, and deliberate flaw detection.
"""

import math
import unittest

from example import (
    DistillationError,
    LocalDistillationAdapter,
    ProbabilityProvider,
    compute_cross_entropy,
    evaluate_distillation_sample,
    run_concept_example,
    validate_probability_distribution,
)


class TestDistillationNormal(unittest.TestCase):
    def test_canonical_soft_teacher_and_student_gives_ln2(self):
        """Teacher [1, 0] and Student [0.5, 0.5] gives ln(2)."""
        loss = compute_cross_entropy([1.0, 0.0], [0.5, 0.5])
        expected = math.log(2.0)
        self.assertAlmostEqual(loss, expected, places=6)

    def test_identical_one_hot_distributions_approach_zero(self):
        """Identical one-hot distributions approach 0 with the stated floor."""
        loss_1 = compute_cross_entropy([1.0, 0.0], [1.0, 0.0])
        self.assertAlmostEqual(loss_1, 0.0, places=7)

        loss_2 = compute_cross_entropy([0.0, 1.0], [0.0, 1.0])
        self.assertAlmostEqual(loss_2, 0.0, places=7)

    def test_multi_class_distribution(self):
        teacher = [0.7, 0.2, 0.1]
        student = [0.5, 0.3, 0.2]
        loss = compute_cross_entropy(teacher, student)
        expected = -(0.7 * math.log(0.5) + 0.2 * math.log(0.3) + 0.1 * math.log(0.2))
        self.assertAlmostEqual(loss, expected, places=6)

    def test_run_concept_example_summary(self):
        summary = run_concept_example()
        self.assertTrue(summary["matches_ln2"])
        self.assertTrue(summary["approaches_zero"])


class TestValidationAndBoundaries(unittest.TestCase):
    def test_dimension_mismatch_fails(self):
        with self.assertRaises(DistillationError) as ctx:
            compute_cross_entropy([1.0, 0.0], [0.5, 0.3, 0.2])
        self.assertEqual(ctx.exception.code, "DIMENSION_MISMATCH")

    def test_non_summing_to_one_fails(self):
        with self.assertRaises(DistillationError) as ctx:
            compute_cross_entropy([0.5, 0.2], [0.5, 0.5])
        self.assertEqual(ctx.exception.code, "INVALID_DISTRIBUTION")

    def test_negative_probability_fails(self):
        with self.assertRaises(DistillationError) as ctx:
            validate_probability_distribution([-0.1, 1.1])
        self.assertEqual(ctx.exception.code, "INVALID_DISTRIBUTION")

    def test_insufficient_classes_fails(self):
        with self.assertRaises(DistillationError) as ctx:
            validate_probability_distribution([1.0])
        self.assertEqual(ctx.exception.code, "INVALID_DISTRIBUTION")

    def test_student_zero_probability_clamped_safely(self):
        """Zero student probability does not crash with math domain error due to epsilon floor."""
        loss = compute_cross_entropy([1.0, 0.0], [0.0, 1.0])
        self.assertTrue(loss > 0)
        self.assertTrue(math.isfinite(loss))


class TestAdapterPattern(unittest.TestCase):
    def test_abstract_provider_raises(self):
        provider = ProbabilityProvider()
        with self.assertRaises(NotImplementedError):
            provider.get_distributions("test")

    def test_local_adapter_retrieves_canonical_fixtures(self):
        adapter = LocalDistillationAdapter()
        t, s = adapter.get_distributions("canonical_soft")
        self.assertEqual(t, [1.0, 0.0])
        self.assertEqual(s, [0.5, 0.5])

    def test_unknown_sample_raises_fixture_not_found(self):
        adapter = LocalDistillationAdapter()
        with self.assertRaises(DistillationError) as ctx:
            adapter.get_distributions("non_existent_sample")
        self.assertEqual(ctx.exception.code, "FIXTURE_NOT_FOUND")


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_loss_calculation_fails(self):
        """A flawed loss function omitting negative sign or log produces wrong result and fails."""
        def flawed_loss(p, q):
            # Deliberate bug: sums p * q instead of - p * log(q)
            return sum(p_i * q_i for p_i, q_i in zip(p, q))

        res = flawed_loss([1.0, 0.0], [0.5, 0.5])
        # Expected ln(2) ~ 0.693147, but flawed gives 0.5
        with self.assertRaises(AssertionError):
            self.assertAlmostEqual(res, math.log(2.0), places=3)

    def test_flawed_one_hot_not_approaching_zero_fails(self):
        """If identical one-hot returns non-zero offset, assertion fails."""
        flawed_result = 0.45
        with self.assertRaises(AssertionError):
            self.assertAlmostEqual(flawed_result, 0.0, places=2)


if __name__ == "__main__":
    unittest.main()
