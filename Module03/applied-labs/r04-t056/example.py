"""
Local Environment Preflight Check: Failure and Recovery Teaching Example.

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
5. Demonstrates failure diagnosis on invalid/missing-data cases and recovery on next valid input.
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
class PreflightReport:
    """Read-only preflight diagnostic report with sanitized credentials."""
    status: str  # "PASS" or "FAIL"
    passed: bool
    lesson_source: str
    executables_checked: Dict[str, bool]
    config_evaluated: Dict[str, Any]
    issues: List[PreflightIssue] = field(default_factory=list)

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
        }

    def summary(self) -> str:
        lines = [
            f"Preflight Status: {self.status}",
            f"Lesson Source: {self.lesson_source}",
            f"Executables Passed: {sum(1 for v in self.executables_checked.values() if v)}/{len(self.executables_checked)}",
            f"Config Fields Evaluated: {len(self.config_evaluated)}",
        ]
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


class LocalEnvironmentPreflight:
    """
    Read-only preflight checker for local SLM execution environments.
    Inspects binaries and configuration parameters without external networking
    or software modifications.
    """

    def __init__(
        self,
        required_executables: Optional[List[str]] = None,
        required_config_fields: Optional[List[str]] = None,
        secret_keys: Optional[Set[str]] = None,
        lesson_source: str = "Module03/02.DeployingSLMinLocalEnv.md",
    ):
        self.required_executables = (
            list(required_executables) if required_executables is not None else list(DEFAULT_REQUIRED_EXECUTABLES)
        )
        self.required_config_fields = (
            list(required_config_fields) if required_config_fields is not None else list(DEFAULT_REQUIRED_CONFIG_FIELDS)
        )
        self.secret_keys = set(secret_keys) if secret_keys is not None else set(DEFAULT_SECRET_KEYS)
        self.lesson_source = lesson_source

    def check(self, fixture: Dict[str, Any]) -> PreflightReport:
        """
        Execute read-only preflight check against a provided local environment fixture.
        
        Fixture structure:
        {
            "executables": {"ollama": True, "docker": True}, # or available_executables list/set
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                "model_name": "phi4:mini",
                "api_token": "sk-local-secret"
            }
        }
        """
        issues: List[PreflightIssue] = []

        # 1. Evaluate executables
        raw_executables = fixture.get("executables", {})
        if isinstance(raw_executables, (list, set, tuple)):
            exec_map = {req: (req in raw_executables) for req in self.required_executables}
        elif isinstance(raw_executables, dict):
            exec_map = {req: bool(raw_executables.get(req, False)) for req in self.required_executables}
        else:
            exec_map = {req: False for req in self.required_executables}

        for req_exe in self.required_executables:
            if not exec_map.get(req_exe, False):
                issues.append(
                    PreflightIssue(
                        category="MISSING_EXECUTABLE",
                        target=req_exe,
                        message=f"Required executable '{req_exe}' is missing or not found on PATH.",
                        action=f"Install '{req_exe}' or update PATH before starting local SLM deployment.",
                    )
                )

        # 2. Evaluate configuration fields
        raw_config = fixture.get("config", {})
        if not isinstance(raw_config, dict):
            raw_config = {}

        for req_field in self.required_config_fields:
            if req_field not in raw_config or raw_config[req_field] is None:
                issues.append(
                    PreflightIssue(
                        category="ABSENT_CONFIG_FIELD",
                        target=req_field,
                        message=f"Required configuration field '{req_field}' is absent.",
                        action=f"Specify '{req_field}' in local deployment configuration or environment file.",
                    )
                )
            else:
                val = raw_config[req_field]
                # Validate common field expectations
                if req_field == "port":
                    try:
                        port_num = int(val)
                        if not (1 <= port_num <= 65535):
                            issues.append(
                                PreflightIssue(
                                    category="INVALID_CONFIG_VALUE",
                                    target="port",
                                    message=f"Port value {val} is outside valid TCP port range (1-65535).",
                                    action="Provide a valid integer port between 1 and 65535 (e.g. 11434 or 8080).",
                                )
                            )
                    except (ValueError, TypeError):
                        issues.append(
                            PreflightIssue(
                                category="INVALID_CONFIG_VALUE",
                                target="port",
                                message=f"Port value '{val}' is not a valid integer.",
                                action="Specify port as a numeric integer (e.g. 11434).",
                            )
                        )
                elif req_field in ("endpoint", "model_name") and isinstance(val, str) and not val.strip():
                    issues.append(
                        PreflightIssue(
                            category="INVALID_CONFIG_VALUE",
                            target=req_field,
                            message=f"Configuration field '{req_field}' cannot be empty string.",
                            action=f"Provide a valid non-empty string for '{req_field}'.",
                        )
                    )

        # 3. Sanitize configuration to guarantee secret values are never printed
        sanitized_config = sanitize_config(raw_config, self.secret_keys)

        passed = len(issues) == 0
        status = "PASS" if passed else "FAIL"

        return PreflightReport(
            status=status,
            passed=passed,
            lesson_source=self.lesson_source,
            executables_checked=exec_map,
            config_evaluated=sanitized_config,
            issues=issues,
        )

    @staticmethod
    def identify_unestablished_behaviors() -> List[str]:
        """Explicitly declare real-service behaviors that this local fixture mock does not establish."""
        return [
            "Does not attempt network connections or TCP handshakes to live daemon endpoints (e.g. http://localhost:11434).",
            "Does not invoke external package managers (winget, brew, apt) or shell installation scripts.",
            "Does not inspect OS-level process management daemons, systemd services, or container runtime states.",
            "Does not query physical GPU drivers, CUDA libraries, or Windows ML / NPU hardware registers.",
            "Does not download, load, or run inference on real SLM weights (e.g. Phi-4, Qwen 2.5).",
        ]

    @staticmethod
    def explain_mapping() -> List[Dict[str, str]]:
        """Map teaching components directly to lesson concepts in Module03/02.DeployingSLMinLocalEnv.md."""
        return [
            {
                "preflight_component": "required_executables ('ollama', 'docker')",
                "lesson_concept": "Section 2 Deployment Platform Architecture (Ollama CLI and Docker containerization)",
                "pedagogical_purpose": "Confirms presence of host runtime tools prior to launching model workloads.",
            },
            {
                "preflight_component": "required_config_fields ('endpoint', 'port', 'model_name')",
                "lesson_concept": "API Endpoints & Modelfile Configuration (Ollama REST API / Foundry Local)",
                "pedagogical_purpose": "Validates routing parameters without executing real HTTP requests.",
            },
            {
                "preflight_component": "secret_keys & REDACTION_MASK ('***REDACTED***')",
                "lesson_concept": "Enterprise Security and Compliance Considerations (GDPR, HIPAA, credential protection)",
                "pedagogical_purpose": "Guarantees API keys and reverse-proxy auth tokens are never leaked into logs.",
            },
            {
                "preflight_component": "Separate MISSING_EXECUTABLE vs ABSENT_CONFIG_FIELD categories",
                "lesson_concept": "Pre-Deployment Assessment and Troubleshooting Checklist",
                "pedagogical_purpose": "Ensures developers receive distinct, actionable remediation advice for distinct failure modes.",
            },
            {
                "preflight_component": "Failure and Recovery Workflow",
                "lesson_concept": "Production Readiness and Resilient Operations",
                "pedagogical_purpose": "Demonstrates diagnosing invalid configuration and verifying clean recovery upon correction.",
            },
        ]


# Module-level aliases for convenience
explain_mapping = LocalEnvironmentPreflight.explain_mapping
identify_unestablished_behaviors = LocalEnvironmentPreflight.identify_unestablished_behaviors


def demonstrate_failure_and_recovery(
    checker: Optional[LocalEnvironmentPreflight] = None,
    initial_faulty_fixture: Optional[Dict[str, Any]] = None,
    recovery_patch: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Contribution Focus Demonstration:
    1. Exercise a documented invalid/missing-data case.
    2. Explain the diagnostic error and actionable remedy.
    3. Demonstrate recovery on the next valid input.
    """
    if checker is None:
        checker = LocalEnvironmentPreflight()

    # Documented invalid fixture: missing required executable and missing required config field
    if initial_faulty_fixture is None:
        initial_faulty_fixture = {
            "executables": {
                "ollama": False,  # Missing required binary
                "docker": True,
            },
            "config": {
                "endpoint": "http://localhost:11434",
                "port": 11434,
                # "model_name" is deliberately absent!
                "api_token": "super-secret-token-12345",  # Must be redacted
            },
        }

    # Step 1 & 2: Run preflight on invalid input and capture error explanation
    faulty_report = checker.check(initial_faulty_fixture)
    initial_passed = faulty_report.passed

    # Documented recovery patch
    if recovery_patch is None:
        recovery_patch = {
            "executables": {
                "ollama": True,
            },
            "config": {
                "model_name": "phi4:mini",
            },
        }

    # Step 3: Apply patch to construct valid fixture
    recovered_fixture: Dict[str, Any] = {
        "executables": dict(initial_faulty_fixture.get("executables", {})),
        "config": dict(initial_faulty_fixture.get("config", {})),
    }
    if "executables" in recovery_patch:
        recovered_fixture["executables"].update(recovery_patch["executables"])
    if "config" in recovery_patch:
        recovered_fixture["config"].update(recovery_patch["config"])

    # Step 4: Run preflight on recovered input
    recovered_report = checker.check(recovered_fixture)
    recovered_passed = recovered_report.passed

    return {
        "initial_attempt": {
            "status": faulty_report.status,
            "passed": faulty_report.passed,
            "missing_executables": faulty_report.missing_executables,
            "absent_config_fields": faulty_report.absent_config_fields,
            "issues": [i.to_dict() for i in faulty_report.issues],
            "sanitized_config": faulty_report.config_evaluated,
        },
        "recovery_patch_applied": recovery_patch,
        "recovered_attempt": {
            "status": recovered_report.status,
            "passed": recovered_report.passed,
            "missing_executables": recovered_report.missing_executables,
            "absent_config_fields": recovered_report.absent_config_fields,
            "issues": [i.to_dict() for i in recovered_report.issues],
            "sanitized_config": recovered_report.config_evaluated,
        },
        "recovery_successful": (not initial_passed) and recovered_passed,
    }


def main() -> None:
    """CLI demonstration of local environment preflight check with failure and recovery."""
    print("=" * 70)
    print("Local Environment Preflight Check Demonstration (Module03 Section 2)")
    print("=" * 70)

    checker = LocalEnvironmentPreflight()

    print("\n--- 1. Testing Complete Valid Fixture ---")
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
    print(report.summary())
    print("\nSanitized Config in Report (No secrets exposed):")
    print(json.dumps(report.config_evaluated, indent=2))

    print("\n--- 2. Demonstrating Failure & Recovery Cycle ---")
    flow = demonstrate_failure_and_recovery(checker)
    print("Initial Faulty Attempt Status:", flow["initial_attempt"]["status"])
    for issue in flow["initial_attempt"]["issues"]:
        print(f"  - [{issue['category']}] {issue['target']}: {issue['message']}")
        print(f"    Remedy: {issue['action']}")

    print("\nApplying Recovery Patch:", json.dumps(flow["recovery_patch_applied"]))
    print("Recovered Attempt Status:", flow["recovered_attempt"]["status"])
    print("Recovery Successful:", flow["recovery_successful"])

    print("\n--- 3. Unestablished Real-Service Behaviors ---")
    for unest in checker.identify_unestablished_behaviors():
        print(f"  * {unest}")


if __name__ == "__main__":
    main()
