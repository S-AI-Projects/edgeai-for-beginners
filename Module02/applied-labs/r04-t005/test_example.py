"""
Unit Tests for Phi-Silica Platform Compatibility Preflight (R04-T005)
Module 02: Phi-Silica - Optimized On-Device Language Models
"""

import unittest

try:
    from .example import (
        PhiSilicaPlatformChecker,
        MockPlatformAdapter,
        PHI_SILICA_LESSON_REQUIREMENTS,
    )
except ImportError:
    from example import (
        PhiSilicaPlatformChecker,
        MockPlatformAdapter,
        PHI_SILICA_LESSON_REQUIREMENTS,
    )


class TestPhiSilicaPlatformCompatibility(unittest.TestCase):
    def setUp(self):
        self.checker = PhiSilicaPlatformChecker()

    def test_matching_fixture_passes(self):
        """A fixture matching required OS/architecture/backend passes."""
        matching_data = {
            "os": "Windows 11",
            "architecture": "ARM64",
            "backend": "DirectML",
            "capabilities": ["NPU", "DirectML", "WindowsAppSDK"],
        }
        probe = MockPlatformAdapter(matching_data)
        result = self.checker.check_compatibility(probe)

        self.assertTrue(result["compatible"])
        self.assertEqual(len(result["mismatches"]), 0)
        self.assertEqual(len(result["missing_capabilities"]), 0)
        self.assertEqual(
            result["lesson_requirement_used"]["lesson_source"],
            "Module02/06.phisilica.md",
        )

    def test_changed_architecture_fails_with_mismatched_field(self):
        """A changed architecture fails with the mismatched field explicitly recorded."""
        mismatched_data = {
            "os": "Windows 11",
            "architecture": "x86_64",  # changed architecture
            "backend": "DirectML",
            "capabilities": ["NPU", "DirectML", "WindowsAppSDK"],
        }
        probe = MockPlatformAdapter(mismatched_data)
        result = self.checker.check_compatibility(probe)

        self.assertFalse(result["compatible"])
        self.assertEqual(len(result["mismatches"]), 1)
        mismatch = result["mismatches"][0]
        self.assertEqual(mismatch["field"], "architecture")
        self.assertEqual(mismatch["expected"], "ARM64")
        self.assertEqual(mismatch["actual"], "x86_64")

    def test_missing_capability_reported_rather_than_guessed(self):
        """A missing capability is explicitly listed rather than assumed."""
        missing_cap_data = {
            "os": "Windows 11",
            "architecture": "ARM64",
            "backend": "DirectML",
            "capabilities": ["DirectML"],  # Missing 'NPU' and 'WindowsAppSDK'
        }
        probe = MockPlatformAdapter(missing_cap_data)
        result = self.checker.check_compatibility(probe)

        self.assertFalse(result["compatible"])
        self.assertIn("NPU", result["missing_capabilities"])
        self.assertIn("WindowsAppSDK", result["missing_capabilities"])

    def test_os_and_backend_mismatches(self):
        """Mismatched OS or backend are also explicitly identified."""
        incompatible_data = {
            "os": "Linux",
            "architecture": "ARM64",
            "backend": "CUDA",
            "capabilities": ["NPU", "DirectML", "WindowsAppSDK"],
        }
        probe = MockPlatformAdapter(incompatible_data)
        result = self.checker.check_compatibility(probe)

        self.assertFalse(result["compatible"])
        mismatched_fields = {m["field"] for m in result["mismatches"]}
        self.assertIn("os", mismatched_fields)
        self.assertIn("backend", mismatched_fields)

    def test_mock_limitations_stated_explicitly(self):
        """Mock limitations clarify unverified physical silicon behaviors."""
        probe = MockPlatformAdapter({
            "os": "Windows 11",
            "architecture": "ARM64",
            "backend": "DirectML",
            "capabilities": ["NPU", "DirectML", "WindowsAppSDK"],
        })
        result = self.checker.check_compatibility(probe)
        self.assertIn("mock_limitations", result)
        self.assertTrue(len(result["mock_limitations"]) > 0)


if __name__ == "__main__":
    unittest.main()
