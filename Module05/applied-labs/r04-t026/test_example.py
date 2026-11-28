from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from example import (
    FIXTURE_DISCLAIMER,
    account_parameters_baseline,
    account_parameters_refactored,
    classify_freeze_matches,
)


class TestParameterAccountingRefactor(unittest.TestCase):
    def test_encoder_frozen_yields_total_120_trainable_20(self):
        """encoder:100, head:20 with encoder frozen gives total=120, trainable=20."""
        manifest = {"encoder": 100, "head": 20}
        base = account_parameters_baseline(manifest, ["encoder"])
        ref = account_parameters_refactored(manifest, ["encoder"])
        self.assertEqual(base, ref)
        self.assertEqual(ref["total"], 120)
        self.assertEqual(ref["trainable"], 20)
        self.assertEqual(ref["frozen"], 100)
        self.assertEqual(ref["unmatched_prefixes"], [])
        self.assertEqual(ref["fixture_note"], FIXTURE_DISCLAIMER)

    def test_unmatched_freeze_prefix_reported_and_equivalent(self):
        """Unmatched prefix 'decoder' is reported identically before and after refactor."""
        manifest = {"encoder": 100, "head": 20}
        prefixes = ["encoder", "decoder"]
        base = account_parameters_baseline(manifest, prefixes)
        ref = account_parameters_refactored(manifest, prefixes)
        self.assertEqual(base, ref)
        self.assertEqual(ref["unmatched_prefixes"], ["decoder"])
        self.assertEqual(ref["trainable"], 20)

    def test_before_after_equivalence_across_multiple_fixtures(self):
        """Baseline and refactored functions stay equivalent across empty, full-freeze, and multi-layer manifests."""
        cases = [
            ({}, ["encoder"]),
            ({"encoder": 100, "head": 20}, []),
            ({"encoder.layer0": 60, "encoder.layer1": 40, "head": 20}, ["encoder."]),
            ({"encoder": 100, "head": 20}, ["encoder", "head"]),
        ]
        for manifest, prefixes in cases:
            self.assertEqual(
                account_parameters_baseline(manifest, prefixes),
                account_parameters_refactored(manifest, prefixes),
            )

    def test_extracted_responsibility_classify_freeze_matches(self):
        frozen_names, unmatched = classify_freeze_matches(
            ["encoder.0", "head"], ["encoder.", "missing."]
        )
        self.assertEqual(frozen_names, {"encoder.0"})
        self.assertEqual(unmatched, ["missing."])

    def test_invalid_manifest_or_prefix_rejected(self):
        with self.assertRaises(ValueError):
            account_parameters_refactored({"encoder": -5}, ["encoder"])
        with self.assertRaises(ValueError):
            account_parameters_refactored({"encoder": 10}, [""])


if __name__ == "__main__":
    unittest.main()
