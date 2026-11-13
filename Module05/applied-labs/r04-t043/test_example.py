import math
import unittest
from dataclasses import replace

from example import (CASES, DEFAULT_FLOOR, DistributionError, check_invariant,
                     cross_entropy, cross_entropy_trace)


class NormalCases(unittest.TestCase):
    def test_teacher_one_zero_student_half_half_is_ln2(self):
        self.assertAlmostEqual(cross_entropy([1, 0], [0.5, 0.5]), math.log(2), places=12)

    def test_identical_one_hot_distributions_give_zero(self):
        self.assertAlmostEqual(cross_entropy([1, 0], [1, 0]), 0.0, places=12)
        self.assertAlmostEqual(cross_entropy([0, 1], [0, 1]), 0.0, places=12)

    def test_soft_teacher_matches_a_hand_calculation(self):
        # -(0.25*ln(0.25) + 0.75*ln(0.75)), worked out by hand as 0.5623351446...
        self.assertAlmostEqual(cross_entropy([0.25, 0.75], [0.25, 0.75]), 0.5623351446188083, places=12)

    def test_result_is_deterministic(self):
        a = cross_entropy([0.2, 0.3, 0.5], [0.1, 0.6, 0.3])
        b = cross_entropy([0.2, 0.3, 0.5], [0.1, 0.6, 0.3])
        self.assertEqual(a, b)


class BoundaryCases(unittest.TestCase):
    def test_floor_keeps_the_result_finite_when_student_gives_zero(self):
        result = cross_entropy([1, 0], [0, 1])
        self.assertTrue(math.isfinite(result))
        self.assertAlmostEqual(result, 27.631021115928547, places=9)  # -ln(1e-12)

    def test_custom_floor_changes_that_result(self):
        self.assertAlmostEqual(cross_entropy([1, 0], [0, 1], floor=1e-6), 13.815510557964274, places=9)

    def test_zero_teacher_probability_contributes_exactly_zero(self):
        trace = cross_entropy_trace([1, 0], [0.5, 0.5])
        self.assertEqual(trace.steps[1].term, 0.0)

    def test_single_class_distribution(self):
        self.assertAlmostEqual(cross_entropy([1], [1]), 0.0, places=12)

    def test_sum_within_tolerance_is_accepted(self):
        self.assertTrue(math.isfinite(cross_entropy([0.5, 0.5 + 1e-12], [0.5, 0.5])))


class FailureCases(unittest.TestCase):
    def assertCode(self, teacher, student, code, floor=DEFAULT_FLOOR, who=None):
        with self.assertRaises(DistributionError) as ctx:
            cross_entropy(teacher, student, floor)
        self.assertEqual(ctx.exception.code, code)
        if who:
            self.assertIn(who, str(ctx.exception))

    def test_teacher_not_normalized(self):
        self.assertCode([0.5, 0.4], [0.5, 0.5], "NOT_NORMALIZED", who="teacher")

    def test_student_not_normalized(self):
        self.assertCode([0.5, 0.5], [0.7, 0.7], "NOT_NORMALIZED", who="student")

    def test_negative_probability(self):
        self.assertCode([1.5, -0.5], [0.5, 0.5], "NEGATIVE_PROBABILITY", who="teacher")

    def test_not_finite(self):
        self.assertCode([float("nan"), 1.0], [0.5, 0.5], "NOT_FINITE")
        self.assertCode([0.5, 0.5], [float("inf"), 0.0], "NOT_FINITE")

    def test_non_numeric(self):
        self.assertCode(["a", 1.0], [0.5, 0.5], "NON_NUMERIC")
        self.assertCode([True, 0.0], [0.5, 0.5], "NON_NUMERIC")

    def test_empty(self):
        self.assertCode([], [], "EMPTY")
        self.assertCode([1.0], [], "EMPTY", who="student")

    def test_length_mismatch(self):
        self.assertCode([1, 0], [1], "LENGTH_MISMATCH")

    def test_bad_floor(self):
        for bad in (0, -1e-9, 1.0, 2, float("nan"), True):
            with self.subTest(floor=bad):
                self.assertCode([1, 0], [0.5, 0.5], "BAD_FLOOR", floor=bad)


class StateTraceAndInvariant(unittest.TestCase):
    def test_state_is_recorded_after_each_step(self):
        trace = cross_entropy_trace([0.25, 0.75], [0.5, 0.5])
        self.assertEqual(len(trace.steps), 2)
        self.assertAlmostEqual(trace.steps[0].term, 0.25 * math.log(2), places=12)
        self.assertAlmostEqual(trace.steps[0].running_total, 0.17328679513998632, places=12)
        self.assertAlmostEqual(trace.steps[1].running_total, 0.6931471805599453, places=12)
        self.assertAlmostEqual(trace.result, math.log(2), places=12)

    def test_floor_is_visible_in_the_state(self):
        step = cross_entropy_trace([1, 0], [0, 1]).steps[0]
        self.assertEqual(step.q, 0.0)
        self.assertEqual(step.q_floored, DEFAULT_FLOOR)

    def test_invariant_holds_for_valid_fixtures(self):
        fixtures = [
            ([1, 0], [0.5, 0.5]), ([1, 0], [1, 0]), ([1, 0], [0, 1]),
            ([0.2, 0.3, 0.5], [0.1, 0.6, 0.3]), ([0.25, 0.25, 0.25, 0.25], [0.7, 0.1, 0.1, 0.1]),
            ([0.0, 0.0, 1.0], [0.3, 0.3, 0.4]), ([1.0], [1.0]),
        ]
        for teacher, student in fixtures:
            with self.subTest(teacher=teacher, student=student):
                self.assertEqual(check_invariant(cross_entropy_trace(teacher, student)), [])

    def test_running_totals_never_decrease_and_terms_are_non_negative(self):
        trace = cross_entropy_trace([0.2, 0.3, 0.5], [0.1, 0.6, 0.3])
        totals = [s.running_total for s in trace.steps]
        self.assertEqual(totals, sorted(totals))
        self.assertTrue(all(s.term >= 0 for s in trace.steps))

    def test_result_equals_last_running_total(self):
        trace = cross_entropy_trace([0.2, 0.3, 0.5], [0.1, 0.6, 0.3])
        self.assertAlmostEqual(trace.result, trace.steps[-1].running_total, places=12)

    def test_invariant_check_catches_a_wrong_final_result(self):
        trace = cross_entropy_trace([1, 0], [0.5, 0.5])
        bad = replace(trace, result=trace.result + 0.01)
        self.assertIn("result != last running total", check_invariant(bad))

    def test_invariant_check_catches_a_corrupted_step(self):
        trace = cross_entropy_trace([0.25, 0.75], [0.5, 0.5])
        steps = list(trace.steps)
        steps[0] = replace(steps[0], term=steps[0].term + 0.5)  # state no longer matches
        self.assertNotEqual(check_invariant(replace(trace, steps=tuple(steps))), [])

    def test_invariant_check_catches_a_decreasing_running_total(self):
        trace = cross_entropy_trace([0.25, 0.75], [0.5, 0.5])
        steps = list(trace.steps)
        steps[1] = replace(steps[1], running_total=0.0)
        self.assertTrue(any("decreased" in p for p in check_invariant(replace(trace, steps=tuple(steps)))))

    def test_demo_cases_are_consistent_with_the_contract(self):
        for label, teacher, student in CASES:
            with self.subTest(case=label):
                try:
                    trace = cross_entropy_trace(teacher, student)
                except DistributionError:
                    continue
                self.assertEqual(check_invariant(trace), [])


if __name__ == "__main__":
    unittest.main()
