#!/usr/bin/env python3
"""
Platform-Compatibility Preflight - Offline Service Adapter (R04-T005)
Module 02: Phi-Silica - Optimized On-Device Language Models

Concept:
Phi-Silica is specifically engineered for on-device inference on Windows 11
Copilot+ PCs with NPU hardware acceleration and DirectML/Windows ML runtimes.
Before deploying or loading model weights, a preflight platform compatibility
check ensures that OS, processor architecture, runtime backend, and device
capabilities satisfy minimum specifications.

Focus:
Decouples environment probing behind a callable adapter interface
(Offline Service Adapter pattern) and supplies deterministic mock profiles
without touching host hardware. Explicitly enumerates real-world limitations.
"""

from typing import List, Dict, Any, Callable, Optional


# Exact requirements extracted from Module02/06.phisilica.md
PHI_SILICA_LESSON_REQUIREMENTS = {
    "lesson_source": "Module02/06.phisilica.md",
    "target_model": "Phi-Silica",
    "required_os": "Windows 11",
    "required_architecture": "ARM64",
    "required_backend": "DirectML",
    "required_capabilities": ["NPU", "DirectML", "WindowsAppSDK"],
}


class MockPlatformAdapter:
    """
    Deterministic offline adapter satisfying the PlatformProbe interface.
    Supplies fixed hardware and OS profile fixtures without calling system APIs.
    """

    def __init__(self, platform_data: Dict[str, Any]):
        self._data = dict(platform_data)

    def __call__(self) -> Dict[str, Any]:
        return dict(self._data)


class PhiSilicaPlatformChecker:
    """
    Manifest-driven platform compatibility validator for on-device Phi-Silica execution.
    """

    def __init__(self, manifest: Optional[Dict[str, Any]] = None):
        self.manifest = manifest or PHI_SILICA_LESSON_REQUIREMENTS

    def check_compatibility(
        self, probe_fn: Callable[[], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes preflight check using the provided platform probe callable.
        Reports exact mismatched fields and missing capabilities rather than guessing.
        """
        probe_data = probe_fn()

        mismatches: List[Dict[str, Any]] = []
        missing_capabilities: List[str] = []

        # 1. OS verification
        actual_os = probe_data.get("os")
        expected_os = self.manifest["required_os"]
        if actual_os != expected_os:
            mismatches.append({
                "field": "os",
                "expected": expected_os,
                "actual": actual_os,
                "action": f"Switch to {expected_os} Copilot+ PC environment",
            })

        # 2. Architecture verification
        actual_arch = probe_data.get("architecture")
        expected_arch = self.manifest["required_architecture"]
        if actual_arch != expected_arch:
            mismatches.append({
                "field": "architecture",
                "expected": expected_arch,
                "actual": actual_arch,
                "action": f"Architecture mismatch: {expected_arch} required for native NPU pipeline",
            })

        # 3. Backend verification
        actual_backend = probe_data.get("backend")
        expected_backend = self.manifest["required_backend"]
        if actual_backend != expected_backend:
            mismatches.append({
                "field": "backend",
                "expected": expected_backend,
                "actual": actual_backend,
                "action": f"Backend mismatch: Initialize {expected_backend} runtime",
            })

        # 4. Capabilities check
        reported_capabilities = set(probe_data.get("capabilities", []))
        for cap in self.manifest["required_capabilities"]:
            if cap not in reported_capabilities:
                missing_capabilities.append(cap)

        compatible = len(mismatches) == 0 and len(missing_capabilities) == 0

        return {
            "compatible": compatible,
            "mismatches": mismatches,
            "missing_capabilities": missing_capabilities,
            "lesson_requirement_used": dict(self.manifest),
            "reported_profile": probe_data,
            "mock_limitations": (
                "This offline adapter verifies metadata only; it does not query physical "
                "silicon registers, measure NPU TOPS performance, or test DirectML hardware driver stability."
            ),
        }


def run_demo() -> None:
    print("=== Module 02: Phi-Silica Platform Compatibility Preflight ===")
    checker = PhiSilicaPlatformChecker()

    # Matching profile fixture
    matching_fixture = {
        "os": "Windows 11",
        "architecture": "ARM64",
        "backend": "DirectML",
        "capabilities": ["NPU", "DirectML", "WindowsAppSDK"],
    }
    probe_pass = MockPlatformAdapter(matching_fixture)
    result_pass = checker.check_compatibility(probe_pass)
    print("\n1. Matching Copilot+ PC Fixture:")
    print(f"Compatible: {result_pass['compatible']}")

    # Mismatched architecture fixture
    x86_fixture = {
        "os": "Windows 11",
        "architecture": "x86_64",
        "backend": "DirectML",
        "capabilities": ["NPU", "DirectML", "WindowsAppSDK"],
    }
    probe_fail = MockPlatformAdapter(x86_fixture)
    result_fail = checker.check_compatibility(probe_fail)
    print("\n2. Mismatched Architecture Fixture:")
    print(f"Compatible: {result_fail['compatible']}")
    print(f"Mismatches: {result_fail['mismatches']}")


if __name__ == "__main__":
    run_demo()
