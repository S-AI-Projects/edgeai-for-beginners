#!/usr/bin/env python3
"""
Platform-Compatibility Preflight: Refactor the Teaching Example (R04-T055)
Module 04: Qualcomm QNN Optimization Suite (07.QualcommQNN.md)

Concept:
In edge AI deployment targeting specialized accelerators like the Qualcomm Hexagon NPU,
applications must verify that target execution environments satisfy strict hardware,
OS, architecture, and runtime backend requirements before loading compiled QNN model
libraries (e.g. libQnnHtp.so). A manifest-driven platform preflight check decouples
system validation from physical hardware probing, reporting exact mismatched fields
and missing capabilities.

Focus:
1. Implement a correct baseline monolithic checker (BaselineQNNPlatformChecker).
2. Extract the single named responsibility (PlatformRuleValidator).
3. Implement the refactored checker (RefactoredQNNPlatformChecker) delegating to the validator.
4. Maintain the identical contract and prove before/after equivalence on all fixtures.
5. Record the exact lesson requirements from Module04/07.QualcommQNN.md.
6. Identify which real-service behavior this mock does not establish.

Pedagogical Notice:
Operates on local dictionary fixtures without physical Qualcomm hardware or SDK binaries.
"""

import copy
from typing import Any, Dict, List, Optional, Tuple


# Exact requirements read from Section 7 of Module04/07.QualcommQNN.md
QNN_LESSON_REQUIREMENTS: Dict[str, Any] = {
    "lesson_source": "Module04/07.QualcommQNN.md",
    "target_suite": "Qualcomm QNN (Qualcomm Neural Network) Optimization Suite",
    "required_os": "Linux",
    "required_architecture": "aarch64",
    "required_backend": "htp",  # Hexagon Tensor Processor (libQnnHtp.so)
    "required_capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
}


# =====================================================================
# Approach A: Baseline Monolithic Checker (Before Refactoring)
# =====================================================================

class BaselineQNNPlatformChecker:
    """Monolithic platform compatibility validator combining coordination and rule evaluation."""

    def __init__(self, requirements: Optional[Dict[str, Any]] = None) -> None:
        self.requirements = copy.deepcopy(requirements if requirements is not None else QNN_LESSON_REQUIREMENTS)

    def check(self, probe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate probe data against lesson requirements in a single monolithic method."""
        if not isinstance(probe_data, dict):
            raise ValueError(f"probe_data must be a dictionary, got: {type(probe_data).__name__}")

        mismatches: List[Dict[str, Any]] = []
        missing_capabilities: List[str] = []

        # 1. Direct validation of platform attributes
        for field in ["os", "architecture", "backend"]:
            req_key = f"required_{field}"
            expected = self.requirements.get(req_key)
            actual = probe_data.get(field)
            if actual != expected:
                mismatches.append({
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                })

        # 2. Validation of capabilities
        required_caps = self.requirements.get("required_capabilities", [])
        actual_caps = probe_data.get("capabilities", [])
        if not isinstance(actual_caps, list):
            actual_caps = []

        actual_set = set(actual_caps)
        for cap in required_caps:
            if cap not in actual_set:
                missing_capabilities.append(cap)

        compatible = (len(mismatches) == 0 and len(missing_capabilities) == 0)

        return {
            "compatible": compatible,
            "status": "PASS" if compatible else "FAIL",
            "lesson_source": self.requirements.get("lesson_source", "Module04/07.QualcommQNN.md"),
            "target_suite": self.requirements.get("target_suite", "Qualcomm QNN"),
            "requirements": copy.deepcopy(self.requirements),
            "probe_data": copy.deepcopy(probe_data),
            "mismatches": mismatches,
            "missing_capabilities": missing_capabilities,
        }


# =====================================================================
# Extracted Named Responsibility: PlatformRuleValidator
# =====================================================================

class PlatformRuleValidator:
    """Encapsulates the single named responsibility of evaluating platform rules and capabilities."""

    @staticmethod
    def validate_attributes(requirements: Dict[str, Any], probe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare OS, architecture, and backend fields against requirements."""
        mismatches: List[Dict[str, Any]] = []
        for field in ["os", "architecture", "backend"]:
            req_key = f"required_{field}"
            expected = requirements.get(req_key)
            actual = probe_data.get(field)
            if actual != expected:
                mismatches.append({
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                })
        return mismatches

    @staticmethod
    def validate_capabilities(required_capabilities: List[str], actual_capabilities: Any) -> List[str]:
        """Identify missing capabilities without guessing."""
        if not isinstance(actual_capabilities, list):
            actual_capabilities = []
        actual_set = set(actual_capabilities)
        return [cap for cap in required_capabilities if cap not in actual_set]

    def evaluate(self, requirements: Dict[str, Any], probe_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """Evaluate both attributes and capabilities, returning (compatible, mismatches, missing_caps)."""
        mismatches = self.validate_attributes(requirements, probe_data)
        required_caps = requirements.get("required_capabilities", [])
        actual_caps = probe_data.get("capabilities", [])
        missing_capabilities = self.validate_capabilities(required_caps, actual_caps)
        compatible = (len(mismatches) == 0 and len(missing_capabilities) == 0)
        return compatible, mismatches, missing_capabilities


# =====================================================================
# Approach B: Refactored Checker (Delegating to Extracted Responsibility)
# =====================================================================

class RefactoredQNNPlatformChecker:
    """Refactored platform compatibility validator delegating evaluation to PlatformRuleValidator."""

    def __init__(
        self,
        requirements: Optional[Dict[str, Any]] = None,
        validator: Optional[PlatformRuleValidator] = None,
    ) -> None:
        self.requirements = copy.deepcopy(requirements if requirements is not None else QNN_LESSON_REQUIREMENTS)
        self.validator = validator or PlatformRuleValidator()

    def check(self, probe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate platform preflight check by delegating rule verification."""
        if not isinstance(probe_data, dict):
            raise ValueError(f"probe_data must be a dictionary, got: {type(probe_data).__name__}")

        compatible, mismatches, missing_capabilities = self.validator.evaluate(
            self.requirements, probe_data
        )

        return {
            "compatible": compatible,
            "status": "PASS" if compatible else "FAIL",
            "lesson_source": self.requirements.get("lesson_source", "Module04/07.QualcommQNN.md"),
            "target_suite": self.requirements.get("target_suite", "Qualcomm QNN"),
            "requirements": copy.deepcopy(self.requirements),
            "probe_data": copy.deepcopy(probe_data),
            "mismatches": mismatches,
            "missing_capabilities": missing_capabilities,
        }

    @staticmethod
    def identify_unestablished_behaviors() -> List[str]:
        """Document the real-service behaviors this offline mock does not establish."""
        return [
            "Hardware Register Probing: Does not probe physical Hexagon NPU registers or Snapdragon SoC firmware.",
            "Dynamic Library Loading: Does not dlopen libQnnHtp.so or verify dynamic linker symbols.",
            "Kernel Device Node Inspection: Does not check /dev/kgsl-3d0 or Qualcomm NPU character devices.",
            "Runtime Execution: Does not allocate NPU memory or execute real quantized QNN inference graphs.",
        ]


# Default standard QNN platform checker points to the refactored implementation
QNNPlatformChecker = RefactoredQNNPlatformChecker


def prove_equivalence(fixtures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Demonstrate before/after refactoring equivalence across provided fixtures."""
    baseline = BaselineQNNPlatformChecker()
    refactored = RefactoredQNNPlatformChecker()

    all_equivalent = True
    results = []
    for f in fixtures:
        res_baseline = baseline.check(f)
        res_refactored = refactored.check(f)
        matches = (res_baseline == res_refactored)
        if not matches:
            all_equivalent = False
        results.append({
            "fixture": f,
            "matches": matches,
            "status": res_refactored["status"],
            "mismatches": res_refactored["mismatches"],
            "missing_capabilities": res_refactored["missing_capabilities"],
        })

    return {
        "all_equivalent": all_equivalent,
        "total_fixtures": len(fixtures),
        "results": results,
    }


def explain_mapping() -> Dict[str, str]:
    """Map public components to lesson concepts in Module04/07.QualcommQNN.md."""
    return {
        "required_os": "Target operating system (Linux / Android for Qualcomm QNN deployment)",
        "required_architecture": "Target instruction set architecture (aarch64 for Snapdragon devices)",
        "required_backend": "Hexagon Tensor Processor backend (htp / libQnnHtp.so)",
        "required_capabilities": "Required hardware and SDK primitives (Hexagon_NPU, HTP_Backend, QNN_SDK)",
        "mismatches": "Explicit field-by-field discrepancies reported rather than guessed",
        "missing_capabilities": "Explicitly enumerated missing features preventing execution",
        "extracted_responsibility": "PlatformRuleValidator separating evaluation rules from coordination",
    }


def main() -> None:
    """Run CLI demonstration proving refactoring equivalence and contract compliance."""
    print("=" * 70)
    print("Qualcomm QNN Platform Check: Refactored Teaching Example (R04-T055)")
    print("=" * 70)

    # Standard fixtures
    matching_fixture = {
        "os": "Linux",
        "architecture": "aarch64",
        "backend": "htp",
        "capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
    }
    changed_arch_fixture = {
        "os": "Linux",
        "architecture": "x86_64",
        "backend": "htp",
        "capabilities": ["Hexagon_NPU", "HTP_Backend", "QNN_SDK"],
    }
    missing_cap_fixture = {
        "os": "Linux",
        "architecture": "aarch64",
        "backend": "htp",
        "capabilities": ["QNN_SDK"],
    }

    test_fixtures = [matching_fixture, changed_arch_fixture, missing_cap_fixture]
    proof = prove_equivalence(test_fixtures)

    print(f"\n1. Refactoring Equivalence Proof (Baseline vs Refactored):")
    print(f"   Tested {proof['total_fixtures']} fixtures. All outputs identical: {proof['all_equivalent']}")

    checker = RefactoredQNNPlatformChecker()

    print(f"\n2. Matching Fixture:")
    res_pass = checker.check(matching_fixture)
    print(f"   Status: {res_pass['status']} (Compatible: {res_pass['compatible']})")

    print(f"\n3. Changed Architecture Fixture:")
    res_arch = checker.check(changed_arch_fixture)
    print(f"   Status: {res_arch['status']} (Mismatches: {res_arch['mismatches']})")

    print(f"\n4. Missing Capabilities Fixture:")
    res_cap = checker.check(missing_cap_fixture)
    print(f"   Status: {res_cap['status']} (Missing: {res_cap['missing_capabilities']})")

    print(f"\n5. Exact Lesson Requirement Used:")
    print(f"   Source: {res_pass['lesson_source']}")
    print(f"   Requirements: {res_pass['requirements']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
