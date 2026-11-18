"""
Local Environment Preflight Check: Intermediate State Recording and Invariant Testing.

Demonstrates a read-only environment preflight validator for local SLM deployments
(Ollama / Microsoft Foundry Local / Docker) as outlined in:
Module03/02.DeployingSLMinLocalEnv.md

Core Contract:
1. Read-only validation: Inspects explicitly listed executables and configuration fields
   without installing packages or contacting remote services.
2. Complete fixture passes.
3. Missing executable and absent config field give separate actionable failures.
4. Secret values (tokens, credentials, API keys) are strictly redacted (masked)
   and never printed or serialized in cleartext.
5. Contribution Focus: Record intermediate state after each step and verify formal
   invariants that link intermediate states directly to the final diagnostic report.
"""

from dataclasses import asdict, dataclass, field
import json
from typing import Any, Dict, List, Optional, Set

# Default requirements derived from Module03/02.DeployingSLMinLocalEnv.md
DEFAULT_REQUIRED_EXECUTABLES: List[str] = ["ollama", "docker"]
DEFAULT_REQUIRED_CONFIG_FIELDS: List[str] = ["endpoint", "port", "model_name"]
DEFAULT_SECRET_KEYS: Set[str] = {
    "api_key",
    "api_token",
    "secret_key",
    "auth_token",
    "password",
    "token",
    "secret",
}

REDACTION_MASK = "***REDACTED***"


@dataclass
class PreflightIssue:
    """Actionable preflight issue representation."""
    category: str
    target: str
    message: str
    action: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class StepIntermediateState:
    """
    Deterministic snapshot of state recorded immediately after an evaluation step.
    Enables verifiable step-by-step auditing and invariant testing.
    """
    step_index: int
    step_name: str
    status: str  # "PASS" or "FAIL"
    passed: bool
    details: Dict[str, Any]
    issues: List[PreflightIssue] = field(default_factory=list)
    cumulative_issues_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_name": self.step_name,
            "status": self.status,
            "passed": self.passed,
            "details": self.details,
            "issues": [i.to_dict() for i in self.issues],
            "cumulative_issues_count": self.cumulative_issues_count,
        }


@dataclass
class InvariantCheck:
    """Individual invariant check verification record."""
    name: str
    passed: bool
    description: str
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InvariantValidationResult:
    """Result of verifying invariants linking intermediate states to the final report."""
    all_valid: bool
    checks: List[InvariantCheck] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "all_valid": self.all_valid,
            "checks": [c.to_dict() for c in self.checks],
        }


@dataclass
class PreflightReport:
    """Read-only preflight diagnostic report with sanitized credentials and intermediate states."""
    status: str  # "PASS" or "FAIL"
    passed: bool
    lesson_source: str
    executables_checked: Dict[str, bool]
    config_evaluated: Dict[str, Any]
    issues: List[PreflightIssue] = field(default_factory=list)
    intermediate_states: List[StepIntermediateState] = field(default_factory=list)

    @property
    def missing_executables(self) -> List[str]:
        return [i.target for i in self.issues if i.category == "MISSING_EXECUTABLE"]

    @property
    def absent_config_fields(self) -> List[str]:
        return [i.target for i in self.issues if i.category == "ABSENT_CONFIG_FIELD"]

    @property
    def invalid_config_fields(self) -> List[str]:
        return [i.target for i in self.issues if i.category == "INVALID_CONFIG_VALUE"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "lesson_source": self.lesson_source,
            "executables_checked": self.executables_checked,
            "config_evaluated": self.config_evaluated,
            "issues": [i.to_dict() for i in self.issues],
            "missing_executables": self.missing_executables,
            "absent_config_fields": self.absent_config_fields,
            "invalid_config_fields": self.invalid_config_fields,
            "intermediate_states": [s.to_dict() for s in self.intermediate_states],
        }

    def summary(self) -> str:
        lines = [
            f"Preflight Status: {self.status}",
            f"Lesson Source: {self.lesson_source}",
            f"Executables Passed: {sum(1 for v in self.executables_checked.values() if v)}/{len(self.executables_checked)}",
            f"Config Fields Evaluated: {len(self.config_evaluated)}",
            f"Intermediate States Recorded: {len(self.intermediate_states)}",
        ]
        for state in self.intermediate_states:
            lines.append(
                f"  - Step {state.step_index} [{state.step_name}]: {state.status} "
                f"({len(state.issues)} issue(s), cumulative: {state.cumulative_issues_count})"
            )
        if self.issues:
            lines.append("Diagnostics / Action Items:")
            for issue in self.issues:
                lines.append(f"  - [{issue.category}] {issue.target}: {issue.message}")
                lines.append(f"    Action: {issue.action}")
        else:
            lines.append("All preflight criteria satisfied. Local environment ready for deployment.")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()


def is_sensitive_key(key: str, secret_keys: Set[str]) -> bool:
    """Check if a configuration key represents sensitive data."""
    lowered = key.lower()
    if lowered in {k.lower() for k in secret_keys}:
        return True
    return any(s in lowered for s in ("token", "secret", "password", "key", "credential"))


def sanitize_config(config: Dict[str, Any], secret_keys: Set[str]) -> Dict[str, Any]:
    """
    Recursively sanitize configuration dictionary to ensure secrets are never exposed.
    Replaces sensitive values with REDACTION_MASK.
    """
    sanitized: Dict[str, Any] = {}
    for k, v in config.items():
        if is_sensitive_key(k, secret_keys):
            sanitized[k] = REDACTION_MASK
        elif isinstance(v, dict):
            sanitized[k] = sanitize_config(v, secret_keys)
        elif isinstance(v, list):
            sanitized[k] = [
                sanitize_config(item, secret_keys) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized


def find_raw_secrets(data: Any, secret_keys: Set[str]) -> List[str]:
    """Inspect data structure to detect if any cleartext secret values remain."""
    leaked: List[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if is_sensitive_key(k, secret_keys):
                if v != REDACTION_MASK and v is not None and v != "":
                    leaked.append(f"Key '{k}' contains unredacted secret value")
            elif isinstance(v, (dict, list)):
                leaked.extend(find_raw_secrets(v, secret_keys))
    elif isinstance(data, list):
        for item in data:
            leaked.extend(find_raw_secrets(item, secret_keys))
    return leaked


class LocalEnvironmentPreflight:
    """
    Read-only environment preflight validator for local SLM deployments.
    
    Verifies explicitly listed executables and configuration parameters offline.
    Records intermediate state after each step and enables invariant verification.
    """

    def __init__(
        self,
        required_executables: Optional[List[str]] = None,
        required_config_fields: Optional[List[str]] = None,
        secret_keys: Optional[Set[str]] = None,
        lesson_source: str = "Module03/02.DeployingSLMinLocalEnv.md",
    ):
        self.required_executables = (
            list(required_executables)
            if required_executables is not None
            else list(DEFAULT_REQUIRED_EXECUTABLES)
        )
        self.required_config_fields = (
            list(required_config_fields)
            if required_config_fields is not None
            else list(DEFAULT_REQUIRED_CONFIG_FIELDS)
        )
        self.secret_keys = (
            set(secret_keys) if secret_keys is not None else set(DEFAULT_SECRET_KEYS)
        )
        self.lesson_source = lesson_source

    def check(self, fixture: Dict[str, Any]) -> PreflightReport:
        """
        Execute preflight check on local fixture, recording intermediate state after each step.
        
        Evaluation Pipeline:
        Step 1: Check required executables -> record intermediate state 1.
        Step 2: Check required configuration fields and validity -> record intermediate state 2.
        Step 3: Redact and sanitize secrets -> record intermediate state 3.
        Step 4: Synthesize final PreflightReport linking all intermediate states.
        """
        intermediate_states: List[StepIntermediateState] = []
        cumulative_issues: List[PreflightIssue] = []

        # =====================================================================
        # Step 1: Check Required Executables
        # =====================================================================
        step1_issues: List[PreflightIssue] = []
        exec_fixture = fixture.get("executables", {})
        executables_checked: Dict[str, bool] = {}

        for exe in self.required_executables:
            is_present = False
            if isinstance(exec_fixture, dict):
                is_present = bool(exec_fixture.get(exe, False))
            elif isinstance(exec_fixture, (list, set)):
                is_present = exe in exec_fixture
            executables_checked[exe] = is_present

            if not is_present:
                issue = PreflightIssue(
                    category="MISSING_EXECUTABLE",
                    target=exe,
                    message=f"Required executable '{exe}' is missing or not found on PATH.",
                    action=f"Install '{exe}' or update PATH before starting local SLM deployment.",
                )
                step1_issues.append(issue)

        cumulative_issues.extend(step1_issues)
        step1_passed = len(step1_issues) == 0
        step1_status = "PASS" if step1_passed else "FAIL"

        state_1 = StepIntermediateState(
            step_index=1,
            step_name="check_executables",
            status=step1_status,
            passed=step1_passed,
            details={
                "required_executables": self.required_executables,
                "executables_checked": executables_checked,
                "missing_executables": [i.target for i in step1_issues],
            },
            issues=list(step1_issues),
            cumulative_issues_count=len(cumulative_issues),
        )
        intermediate_states.append(state_1)

        # =====================================================================
        # Step 2: Check Required Configuration Fields & Values
        # =====================================================================
        step2_issues: List[PreflightIssue] = []
        config_fixture = fixture.get("config", {})

        for field_name in self.required_config_fields:
            if field_name not in config_fixture or config_fixture[field_name] is None:
                issue = PreflightIssue(
                    category="ABSENT_CONFIG_FIELD",
                    target=field_name,
                    message=f"Required configuration field '{field_name}' is absent.",
                    action=f"Specify '{field_name}' in local deployment configuration or environment file.",
                )
                step2_issues.append(issue)
            else:
                val = config_fixture[field_name]
                # Validate port value bounds
                if field_name == "port":
                    try:
                        port_int = int(val)
                        if not (1 <= port_int <= 65535):
                            step2_issues.append(
                                PreflightIssue(
                                    category="INVALID_CONFIG_VALUE",
                                    target="port",
                                    message=f"Port value '{val}' is outside valid TCP port range (1-65535).",
                                    action="Provide a valid integer port between 1 and 65535 (e.g. 11434 or 8080).",
                                )
                            )
                    except (ValueError, TypeError):
                        step2_issues.append(
                            PreflightIssue(
                                category="INVALID_CONFIG_VALUE",
                                target="port",
                                message=f"Port value '{val}' is not a valid integer.",
                                action="Provide a valid integer port between 1 and 65535 (e.g. 11434 or 8080).",
                            )
                        )
                # Validate non-empty string fields
                elif isinstance(val, str) and not val.strip():
                    step2_issues.append(
                        PreflightIssue(
                            category="INVALID_CONFIG_VALUE",
                            target=field_name,
                            message=f"Configuration field '{field_name}' cannot be empty or whitespace.",
                            action=f"Provide a non-empty string value for '{field_name}'.",
                        )
                    )

        cumulative_issues.extend(step2_issues)
        step2_passed = len(step2_issues) == 0
        step2_status = "PASS" if step2_passed else "FAIL"

        state_2 = StepIntermediateState(
            step_index=2,
            step_name="check_config_fields",
            status=step2_status,
            passed=step2_passed,
            details={
                "required_config_fields": self.required_config_fields,
                "absent_config_fields": [
                    i.target for i in step2_issues if i.category == "ABSENT_CONFIG_FIELD"
                ],
                "invalid_config_fields": [
                    i.target for i in step2_issues if i.category == "INVALID_CONFIG_VALUE"
                ],
            },
            issues=list(step2_issues),
            cumulative_issues_count=len(cumulative_issues),
        )
        intermediate_states.append(state_2)

        # =====================================================================
        # Step 3: Sanitize Configuration and Strictly Redact Secrets
        # =====================================================================
        sanitized_config = sanitize_config(config_fixture, self.secret_keys)

        # Track which keys were masked
        redacted_keys = [
            k for k in sanitized_config.keys() if is_sensitive_key(k, self.secret_keys)
        ]
        leaks = find_raw_secrets(sanitized_config, self.secret_keys)
        step3_passed = len(leaks) == 0
        step3_status = "PASS" if step3_passed else "FAIL"
        step3_issues: List[PreflightIssue] = []

        if not step3_passed:
            for leak in leaks:
                step3_issues.append(
                    PreflightIssue(
                        category="SECRET_LEAK_DETECTED",
                        target="sanitization_engine",
                        message=leak,
                        action="Ensure all sensitive keys are properly mapped to redaction mask.",
                    )
                )

        cumulative_issues.extend(step3_issues)

        state_3 = StepIntermediateState(
            step_index=3,
            step_name="sanitize_and_redact_secrets",
            status=step3_status,
            passed=step3_passed,
            details={
                "secret_keys_redacted": redacted_keys,
                "redacted_count": len(redacted_keys),
                "leaks_detected": len(leaks),
            },
            issues=list(step3_issues),
            cumulative_issues_count=len(cumulative_issues),
        )
        intermediate_states.append(state_3)

        # =====================================================================
        # Final Output Synthesis
        # =====================================================================
        overall_passed = (
            step1_passed and step2_passed and step3_passed and len(cumulative_issues) == 0
        )
        overall_status = "PASS" if overall_passed else "FAIL"

        return PreflightReport(
            status=overall_status,
            passed=overall_passed,
            lesson_source=self.lesson_source,
            executables_checked=executables_checked,
            config_evaluated=sanitized_config,
            issues=cumulative_issues,
            intermediate_states=intermediate_states,
        )

    def verify_invariants(self, report: PreflightReport) -> InvariantValidationResult:
        """
        Verify the formal invariants that link intermediate step states to the final report:
        
        1. Invariant: Status Equivalence
           The final status is PASS if and only if all intermediate step states are PASS.
           `report.passed == all(s.passed for s in report.intermediate_states)`
        
        2. Invariant: Issue Partition & Union
           The final issues list is the exact ordered concatenation of issues from all intermediate steps.
           `report.issues == [issue for s in report.intermediate_states for issue in s.issues]`
        
        3. Invariant: Categorical Consistency
           - `missing_executables` in final report matches Step 1 details.
           - `absent_config_fields` in final report matches Step 2 details.
           - `invalid_config_fields` in final report matches Step 2 details.
        
        4. Invariant: Strict Redaction Preservation
           All sensitive keys identified in Step 3 are masked as `***REDACTED***` in both
           Step 3 and final report, and no cleartext secret exists anywhere in any step.
        
        5. Invariant: Step Chronological Monotonicity
           Intermediate states are recorded in ascending order (step_index 1..N) and
           cumulative issue count is monotonically non-decreasing.
        """
        checks: List[InvariantCheck] = []
        states = report.intermediate_states

        # Invariant 1: Status Equivalence
        expected_overall_pass = all(s.passed for s in states)
        inv1_passed = (report.passed == expected_overall_pass) and (
            report.status == ("PASS" if expected_overall_pass else "FAIL")
        )
        checks.append(
            InvariantCheck(
                name="status_equivalence",
                passed=inv1_passed,
                description="Final report status must equal conjunction of all intermediate step statuses.",
                details=f"report.status={report.status}, all_steps_passed={expected_overall_pass}",
            )
        )

        # Invariant 2: Issue Partition & Union
        step_issues = [issue for s in states for issue in s.issues]
        inv2_passed = (report.issues == step_issues) and (
            len(report.issues) == (states[-1].cumulative_issues_count if states else 0)
        )
        checks.append(
            InvariantCheck(
                name="issue_partition_and_union",
                passed=inv2_passed,
                description="Final report issues list must equal the ordered union of all intermediate step issues.",
                details=f"final_issues_count={len(report.issues)}, sum_step_issues={len(step_issues)}",
            )
        )

        # Invariant 3: Categorical Consistency
        step1 = next((s for s in states if s.step_name == "check_executables"), None)
        step2 = next((s for s in states if s.step_name == "check_config_fields"), None)
        s1_missing = step1.details.get("missing_executables", []) if step1 else []
        s2_absent = step2.details.get("absent_config_fields", []) if step2 else []
        s2_invalid = step2.details.get("invalid_config_fields", []) if step2 else []

        inv3_passed = (
            set(report.missing_executables) == set(s1_missing)
            and set(report.absent_config_fields) == set(s2_absent)
            and set(report.invalid_config_fields) == set(s2_invalid)
        )
        checks.append(
            InvariantCheck(
                name="categorical_consistency",
                passed=inv3_passed,
                description="Categorical failure lists in final report must match intermediate state details.",
                details=(
                    f"missing_executables={report.missing_executables == s1_missing}, "
                    f"absent_config_fields={report.absent_config_fields == s2_absent}, "
                    f"invalid_config_fields={report.invalid_config_fields == s2_invalid}"
                ),
            )
        )

        # Invariant 4: Strict Redaction Preservation
        step3 = next((s for s in states if s.step_name == "sanitize_and_redact_secrets"), None)
        redacted_in_step3 = step3.details.get("secret_keys_redacted", []) if step3 else []
        leaks = find_raw_secrets(report.config_evaluated, self.secret_keys)
        all_redacted = all(
            report.config_evaluated.get(k) == REDACTION_MASK for k in redacted_in_step3
        )
        inv4_passed = (len(leaks) == 0) and all_redacted
        checks.append(
            InvariantCheck(
                name="strict_redaction_preservation",
                passed=inv4_passed,
                description="Every sensitive key must be masked in Step 3 and final config with zero leaks.",
                details=f"redacted_keys={redacted_in_step3}, leaks_found={len(leaks)}",
            )
        )

        # Invariant 5: Step Chronological Monotonicity
        indices = [s.step_index for s in states]
        is_sequential = indices == list(range(1, len(states) + 1))
        counts = [s.cumulative_issues_count for s in states]
        is_monotonic = all(counts[i] <= counts[i + 1] for i in range(len(counts) - 1))
        inv5_passed = is_sequential and is_monotonic
        checks.append(
            InvariantCheck(
                name="chronological_monotonicity",
                passed=inv5_passed,
                description="Step indices must be sequential and cumulative issue counts non-decreasing.",
                details=f"indices={indices}, cumulative_counts={counts}",
            )
        )

        all_valid = all(c.passed for c in checks)
        return InvariantValidationResult(all_valid=all_valid, checks=checks)

    @staticmethod
    def identify_unestablished_behaviors() -> List[str]:
        """
        Identify behaviors that this offline educational validator does not establish.
        Prevents unsupported claims about real hardware or live services.
        """
        return [
            "Does not establish network reachability, socket handshakes, or HTTP endpoint health.",
            "Does not invoke OS package managers (winget, brew, apt) or install host executables.",
            "Does not query physical GPU / NPU hardware registers or measure VRAM allocation.",
            "Does not inspect OS-level kernel process tables or active daemon services.",
            "Does not load model weights, verify tensor buffers, or evaluate live inference throughput.",
        ]

    @staticmethod
    def explain_mapping() -> List[Dict[str, str]]:
        """Map validator components to Module03/02.DeployingSLMinLocalEnv.md concepts."""
        return [
            {
                "preflight_component": "Intermediate state recording per evaluation step",
                "lesson_concept": "Section 2 Deployment Platform Architecture & Verification",
                "pedagogical_purpose": "Demonstrates deterministic phase transitions and auditability of host requirements.",
            },
            {
                "preflight_component": "Invariant testing linking intermediate state to final output",
                "lesson_concept": "Section 2 Production Readiness & Quality Assurance",
                "pedagogical_purpose": "Proves formal correctness guarantees that every reported failure originates in an intermediate step.",
            },
            {
                "preflight_component": "Separate actionable diagnostic categories (Missing Exe vs Absent Config)",
                "lesson_concept": "Section 2 Pre-Deployment Assessment and Troubleshooting Checklist",
                "pedagogical_purpose": "Ensures engineers receive distinct, actionable remediation advice for distinct failure modes.",
            },
            {
                "preflight_component": "Strict credential redaction (***REDACTED***)",
                "lesson_concept": "Section 2 Security and Compliance Considerations",
                "pedagogical_purpose": "Guarantees API keys and credentials are never exposed in log output or diagnostic summaries.",
            },
            {
                "preflight_component": "Read-only non-intrusive fixture inspection",
                "lesson_concept": "Section 2 Privacy-First Local Solutions",
                "pedagogical_purpose": "Enforces safe, zero-side-effect assessment without external network dependencies.",
            },
        ]


# Backward-compatible convenience aliases
explain_mapping = LocalEnvironmentPreflight.explain_mapping
identify_unestablished_behaviors = LocalEnvironmentPreflight.identify_unestablished_behaviors


def demonstrate_intermediate_states_and_invariants(
    checker: Optional[LocalEnvironmentPreflight] = None,
) -> Dict[str, Any]:
    """
    Demonstrate intermediate state recording after each step and invariant testing.
    
    Covers:
    1. Complete valid fixture (PASS with all intermediate steps passing).
    2. Missing executable fixture (FAIL triggered in Step 1, invariant verified).
    3. Absent config field fixture (FAIL triggered in Step 2, invariant verified).
    4. Credential redaction verification (Masked in Step 3 and final output).
    """
    if checker is None:
        checker = LocalEnvironmentPreflight()

    # Scenario 1: Complete Valid Fixture
    valid_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
            "api_token": "sk-local-secret-live-token",
        },
    }
    report_valid = checker.check(valid_fixture)
    invariants_valid = checker.verify_invariants(report_valid)

    # Scenario 2: Missing Executable Fixture
    missing_exe_fixture = {
        "executables": {"ollama": False, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
        },
    }
    report_missing_exe = checker.check(missing_exe_fixture)
    invariants_missing_exe = checker.verify_invariants(report_missing_exe)

    # Scenario 3: Absent Config Field Fixture
    absent_config_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            # "model_name" is absent!
        },
    }
    report_absent_config = checker.check(absent_config_fixture)
    invariants_absent_config = checker.verify_invariants(report_absent_config)

    return {
        "scenario_valid": {
            "status": report_valid.status,
            "passed": report_valid.passed,
            "intermediate_states_count": len(report_valid.intermediate_states),
            "step_statuses": [
                {"step": s.step_name, "status": s.status}
                for s in report_valid.intermediate_states
            ],
            "invariants_all_valid": invariants_valid.all_valid,
            "invariant_checks": [c.to_dict() for c in invariants_valid.checks],
        },
        "scenario_missing_executable": {
            "status": report_missing_exe.status,
            "passed": report_missing_exe.passed,
            "missing_executables": report_missing_exe.missing_executables,
            "step1_status": report_missing_exe.intermediate_states[0].status,
            "invariants_all_valid": invariants_missing_exe.all_valid,
        },
        "scenario_absent_config": {
            "status": report_absent_config.status,
            "passed": report_absent_config.passed,
            "absent_config_fields": report_absent_config.absent_config_fields,
            "step2_status": report_absent_config.intermediate_states[1].status,
            "invariants_all_valid": invariants_absent_config.all_valid,
        },
        "all_invariants_confirmed": (
            invariants_valid.all_valid
            and invariants_missing_exe.all_valid
            and invariants_absent_config.all_valid
        ),
    }


def main() -> None:
    """CLI demonstration of local environment preflight check with intermediate states and invariants."""
    print("=" * 75)
    print("Local Environment Preflight Check: Intermediate State & Invariant Testing")
    print("Module03 Section 2 (R04-T058)")
    print("=" * 75)

    checker = LocalEnvironmentPreflight()

    print("\n--- 1. Evaluating Complete Valid Fixture ---")
    valid_fixture = {
        "executables": {"ollama": True, "docker": True},
        "config": {
            "endpoint": "http://localhost:11434",
            "port": 11434,
            "model_name": "phi4:mini",
            "api_token": "sk-local-secret-live-token",
        },
    }
    report = checker.check(valid_fixture)
    print("Preflight Status:", report.status)
    print("Intermediate Steps Count:", len(report.intermediate_states))
    for state in report.intermediate_states:
        print(f"  Step {state.step_index} [{state.step_name}]: {state.status}")
    print("Config Evaluated:", report.config_evaluated["api_token"])

    inv_results = checker.verify_invariants(report)
    print("Invariants Valid:", inv_results.all_valid)
    for check in inv_results.checks:
        status_symbol = "✓" if check.passed else "✗"
        print(f"  [{status_symbol}] {check.name}: {check.description}")

    print("\n--- 2. Full Invariant & Scenario Demonstration ---")
    demo = demonstrate_intermediate_states_and_invariants(checker)
    print(f"Scenario Valid Status: {demo['scenario_valid']['status']}")
    print(f"Scenario Missing Executable Status: {demo['scenario_missing_executable']['status']}")
    print(f"Scenario Absent Config Status: {demo['scenario_absent_config']['status']}")
    print(f"All Invariants Confirmed: {demo['all_invariants_confirmed']}")

    print("\n--- 3. Unestablished Real-Service Behaviors ---")
    for unest in checker.identify_unestablished_behaviors():
        print(f"  * {unest}")


if __name__ == "__main__":
    main()
