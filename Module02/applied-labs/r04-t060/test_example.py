"""
Unit tests for Microsoft Phi Model Family Synthetic Manifest Selection & Applied Questions (R04-T060).

Tests:
1. Canonical contract: Budget RAM 6 GB, requested context 1024 admits only Fixture A.
2. Fixture B exclusion diagnostic details actionable reason (insufficient RAM 8.0 GB vs 6.0 GB).
3. Context window constraint failure diagnostic (requested context exceeds model capacity).
4. Dual resource constraint failure reporting multiple distinct reasons.
5. Applied Question 1 (Predict an output) verification and rationale.
6. Applied Question 2 (Diagnose a failure) verification and rationale.
7. Applied Question 3 (Choose a boundary policy) verification and rationale.
8. End-to-end applied questions suite verification.
9. Boundary condition: Exact equality under inclusive boundary admission policy.
10. Empty manifest handling.
11. Unestablished real-service behavior declarations.
12. Concept mapping integrity to Module02/01.PhiFamily.md.
"""

import unittest

from example import (
    FIXTURE_A,
    FIXTURE_B,
    STANDARD_TEACHING_MANIFEST,
    AppliedQuestion,
    ExclusionReport,
    ModelEntry,
    PhiModelManifestSelector,
    SelectionResult,
    check_choose_boundary_policy,
    check_diagnose_failure,
    check_predict_output,
    explain_mapping,
    get_applied_questions,
    identify_unestablished_behaviors,
    verify_all_applied_questions,
)


class TestPhiModelManifestSelectionAndQuestions(unittest.TestCase):
    def setUp(self):
        self.selector = PhiModelManifestSelector()

    def test_canonical_selection_admits_only_a(self):
        """Verify budget RAM 6.0 GB and requested context 1024 tokens admits only Fixture A."""
        result = self.selector.select(
            STANDARD_TEACHING_MANIFEST, ram_budget_gb=6.0, requested_context=1024
        )
        self.assertEqual(result.admitted_ids, ["fixture-a"])
        self.assertEqual(result.excluded_ids, ["fixture-b"])
        self.assertEqual(len(result.admitted_models), 1)
        self.assertEqual(len(result.excluded_models), 1)

    def test_fixture_b_exclusion_reason_reports_insufficient_ram(self):
        """Verify Fixture B exclusion explicitly details RAM insufficiency."""
        result = self.selector.select(
            STANDARD_TEACHING_MANIFEST, ram_budget_gb=6.0, requested_context=1024
        )
        exc_b = result.excluded_models[0]
        self.assertEqual(exc_b.model_id, "fixture-b")
        reason_str = " ".join(exc_b.reasons)
        self.assertIn("Insufficient RAM", reason_str)
        self.assertIn("8.0 GB", reason_str)
        self.assertIn("6.0 GB", reason_str)

    def test_context_insufficiency_exclusion(self):
        """Verify context window shortfall triggers actionable context diagnostics."""
        # Requesting 3000 tokens: Fixture A supports only 2048 -> Excluded
        result = self.selector.select(
            [FIXTURE_A], ram_budget_gb=10.0, requested_context=3000
        )
        self.assertEqual(result.admitted_ids, [])
        self.assertEqual(result.excluded_ids, ["fixture-a"])
        reason_str = " ".join(result.excluded_models[0].reasons)
        self.assertIn("Insufficient context capacity", reason_str)
        self.assertIn("2048", reason_str)
        self.assertIn("3000", reason_str)

    def test_dual_resource_failure_reporting(self):
        """Verify candidate failing both RAM and context reports both reasons."""
        demanding_model = ModelEntry(
            model_id="heavy-phi",
            name="Heavy Synthetic Model",
            required_ram_gb=16.0,
            max_context_length=1024,
        )
        result = self.selector.select(
            [demanding_model], ram_budget_gb=8.0, requested_context=4096
        )
        self.assertEqual(result.excluded_ids, ["heavy-phi"])
        reasons = result.excluded_models[0].reasons
        self.assertEqual(len(reasons), 2)
        self.assertTrue(any("Insufficient RAM" in r for r in reasons))
        self.assertTrue(any("Insufficient context capacity" in r for r in reasons))

    def test_applied_question_1_predict_output(self):
        """Verify Question 1 (Predict an output) produces the expected factual answer."""
        self.assertTrue(check_predict_output())
        questions = get_applied_questions()
        q1 = next(q for q in questions if q.question_id == "Q1_PREDICT_OUTPUT")
        self.assertEqual(q1.category, "predict_output")
        self.assertEqual(q1.factual_answer["admitted_ids"], ["fixture-b"])
        self.assertEqual(q1.factual_answer["excluded_ids"], ["fixture-a"])
        self.assertTrue(q1.verify())

    def test_applied_question_2_diagnose_failure(self):
        """Verify Question 2 (Diagnose a failure) correctly isolates the bottleneck."""
        self.assertTrue(check_diagnose_failure())
        questions = get_applied_questions()
        q2 = next(q for q in questions if q.question_id == "Q2_DIAGNOSE_FAILURE")
        self.assertEqual(q2.category, "diagnose_failure")
        self.assertEqual(q2.factual_answer["failing_model"], "fixture-a")
        self.assertEqual(q2.factual_answer["primary_bottleneck"], "RAM")
        self.assertTrue(q2.verify())

    def test_applied_question_3_choose_boundary_policy(self):
        """Verify Question 3 (Choose a boundary policy) enforces inclusive boundary admission."""
        self.assertTrue(check_choose_boundary_policy())
        questions = get_applied_questions()
        q3 = next(q for q in questions if q.question_id == "Q3_CHOOSE_BOUNDARY_POLICY")
        self.assertEqual(q3.category, "choose_boundary_policy")
        self.assertEqual(q3.factual_answer["chosen_policy"], "INCLUSIVE_BOUNDARY_ADMISSION")
        self.assertTrue(q3.verify())

    def test_verify_all_applied_questions(self):
        """Verify complete applied questions suite verifies successfully."""
        summary = verify_all_applied_questions()
        self.assertTrue(summary["all_passed"])
        self.assertEqual(summary["questions_count"], 3)
        for res in summary["results"]:
            self.assertTrue(res["check_passed"])

    def test_boundary_inclusive_admission(self):
        """Verify inclusive boundary conditions (required_ram == budget, max_context == requested)."""
        exact_model = ModelEntry(
            model_id="exact-fit",
            name="Exact Fit Model",
            required_ram_gb=6.0,
            max_context_length=1024,
        )
        res = self.selector.select([exact_model], ram_budget_gb=6.0, requested_context=1024)
        self.assertEqual(res.admitted_ids, ["exact-fit"])
        self.assertEqual(res.excluded_ids, [])

    def test_empty_manifest_boundary(self):
        """Verify empty manifest produces clean empty output."""
        res = self.selector.select([], ram_budget_gb=6.0, requested_context=1024)
        self.assertEqual(res.admitted_ids, [])
        self.assertEqual(res.excluded_ids, [])

    def test_unestablished_behaviors_documented(self):
        """Verify declarations preventing unsupported hardware or accuracy claims."""
        unestablished = identify_unestablished_behaviors()
        self.assertGreaterEqual(len(unestablished), 5)
        combined = " ".join(unestablished).lower()
        self.assertIn("memory registers", combined)
        self.assertIn("model weights", combined)
        self.assertIn("inference throughput", combined)
        self.assertIn("gpu vram", combined)

    def test_concept_mapping_integrity(self):
        """Verify mapping to Module02/01.PhiFamily.md concepts."""
        mappings = explain_mapping()
        self.assertGreaterEqual(len(mappings), 5)
        for item in mappings:
            self.assertIn("component", item)
            self.assertIn("lesson_concept", item)
            self.assertIn("pedagogical_purpose", item)


if __name__ == "__main__":
    unittest.main()
