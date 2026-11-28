from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    FIXTURE_DISCLAIMER,
    ManifestValidationError,
    account_parameters,
    process_manifest_stream,
)


class TestParameterAccountingFailureRecovery(unittest.TestCase):
    def test_valid_fixture_encoder_frozen(self):
        """encoder:100, head:20 with encoder frozen gives total=120, trainable=20."""
        result = account_parameters({"encoder": 100, "head": 20}, ["encoder"])
        self.assertEqual(result["total"], 120)
        self.assertEqual(result["trainable"], 20)
        self.assertEqual(result["frozen"], 100)
        self.assertEqual(result["unmatched_prefixes"], [])
        self.assertEqual(result["fixture_note"], FIXTURE_DISCLAIMER)

    def test_unmatched_freeze_prefix_reported(self):
        """Unmatched freeze prefix is reported explicitly."""
        result = account_parameters({"encoder": 100, "head": 20}, ["encoder", "missing_layer"])
        self.assertEqual(result["total"], 120)
        self.assertEqual(result["trainable"], 20)
        self.assertEqual(result["unmatched_prefixes"], ["missing_layer"])

    def test_missing_and_invalid_data_raise_explained_error(self):
        """Missing manifest or negative count raises ManifestValidationError with explanation."""
        with self.assertRaises(ManifestValidationError) as missing_ctx:
            account_parameters(None, ["encoder"])
        self.assertIn("missing or empty", str(missing_ctx.exception).lower())

        with self.assertRaises(ManifestValidationError) as neg_ctx:
            account_parameters({"encoder": -1, "head": 20}, ["encoder"])
        self.assertIn("invalid count", str(neg_ctx.exception).lower())

    def test_recovery_on_next_valid_input_after_failure(self):
        """Batch processor records error on invalid input and cleanly recovers on next valid manifest."""
        outcomes = process_manifest_stream(
            [
                ("missing_manifest", {}, ["encoder"]),
                ("bad_count", {"encoder": -5, "head": 20}, ["encoder"]),
                ("recovered_valid", {"encoder": 100, "head": 20}, ["encoder"]),
            ]
        )
        self.assertEqual(outcomes[0]["status"], "error")
        self.assertEqual(outcomes[1]["status"], "error")
        self.assertEqual(outcomes[2]["status"], "ok")
        self.assertEqual(outcomes[2]["result"]["total"], 120)
        self.assertEqual(outcomes[2]["result"]["trainable"], 20)


if __name__ == "__main__":
    unittest.main()
