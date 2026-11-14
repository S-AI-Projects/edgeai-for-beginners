"""R04-T046 - Installation preflight report: worked example with checks
(Module08/01.FoundryLocalSetup.md, "Session 1: Getting Started with Foundry Local").

Contract (small and local):
  * A READ-ONLY preflight checks an explicit list of executables and an explicit list of
    local configuration fields. It installs nothing and contacts no service.
  * A complete environment passes.
  * A missing executable and an absent config field are SEPARATE, ACTIONABLE failures: each
    is its own line, names the thing that is wrong and says what to do next.
  * Secret values are NEVER printed. A field is treated as secret if it is flagged secret OR
    its name contains KEY, TOKEN, SECRET or PASSWORD. The report does not even store values.

Focus - a worked input-to-output explanation, executed as a regression test:
  The README publishes two worked examples (input fixture -> exact output). worked_example.txt
  holds that exact output, and the tests re-run the examples and require the output to match
  the file AND the README character for character.

SIMULATION ONLY: environments are described by small fixtures (a fake PATH and a plain
dict). Nothing here installs Foundry Local, starts a service or checks real hardware, and it
makes no claim about any real machine. Standard library only (Python 3).
"""

import shutil
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Tuple

SECRET_NAME_PARTS = ("KEY", "TOKEN", "SECRET", "PASSWORD")


class SpecError(ValueError):
    """Raised when the requirements list or the config itself is unusable. `code` names the rule."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class ExecutableRequirement:
    name: str
    hint: str  # what to do if it is missing


@dataclass(frozen=True)
class ConfigRequirement:
    name: str
    hint: str  # what to do if it is absent
    secret: bool = False


@dataclass(frozen=True)
class Spec:
    executables: Tuple[ExecutableRequirement, ...] = ()
    config: Tuple[ConfigRequirement, ...] = ()


@dataclass(frozen=True)
class Check:
    kind: str     # "executable" or "config"
    name: str
    status: str   # OK, MISSING_EXECUTABLE, ABSENT_CONFIG, EMPTY_CONFIG
    message: str  # already safe to print: it never contains a config value for a secret

    @property
    def ok(self) -> bool:
        return self.status == "OK"


@dataclass(frozen=True)
class Report:
    checks: Tuple[Check, ...]

    @property
    def failures(self) -> Tuple[Check, ...]:
        return tuple(c for c in self.checks if not c.ok)

    @property
    def passed(self) -> bool:
        return not self.failures


class FakeProbe:
    """Fixture 'PATH': answers which() from a fixed list of names. Touches nothing."""

    def __init__(self, available: Iterable[str]):
        self.available = set(available)

    def which(self, name: str) -> bool:
        return name in self.available


class SystemProbe:
    """The only piece that looks at the real machine: a read-only PATH lookup, nothing is run."""

    def which(self, name: str) -> bool:
        return shutil.which(name) is not None


def is_secret(requirement: ConfigRequirement) -> bool:
    upper = requirement.name.upper()
    return requirement.secret or any(part in upper for part in SECRET_NAME_PARTS)


def _validate_spec(spec: Spec) -> None:
    if not spec.executables and not spec.config:
        raise SpecError("EMPTY_SPEC", "list at least one executable or config field to check")
    seen = set()
    for item in tuple(spec.executables) + tuple(spec.config):
        if not isinstance(item.name, str) or not item.name.strip():
            raise SpecError("BAD_REQUIREMENT", "every requirement needs a non-empty name")
        key = (type(item).__name__, item.name)
        if key in seen:
            raise SpecError("DUPLICATE_REQUIREMENT", f"'{item.name}' is listed more than once")
        seen.add(key)


def _validate_config(config) -> None:
    if not isinstance(config, Mapping):
        raise SpecError("BAD_CONFIG", "config must be a mapping of field name to text value")
    for name, value in config.items():
        if value is not None and not isinstance(value, str):
            raise SpecError("BAD_CONFIG", f"config field '{name}' must be text or None")


def check_environment(spec: Spec, probe, config: Mapping[str, Optional[str]]) -> Report:
    """Read-only preflight. Returns a Report; never modifies its inputs."""
    _validate_spec(spec)
    _validate_config(config)
    checks = []
    for req in spec.executables:
        if probe.which(req.name):
            checks.append(Check("executable", req.name, "OK", "found on PATH"))
        else:
            checks.append(Check("executable", req.name, "MISSING_EXECUTABLE",
                                f"not found on PATH -> {req.hint}"))
    for req in spec.config:
        value = config.get(req.name)
        if value is None:
            checks.append(Check("config", req.name, "ABSENT_CONFIG", f"not set -> {req.hint}"))
        elif not value.strip():
            checks.append(Check("config", req.name, "EMPTY_CONFIG", f"set but empty -> {req.hint}"))
        elif is_secret(req):
            checks.append(Check("config", req.name, "OK", "set (value hidden)"))
        else:
            checks.append(Check("config", req.name, "OK", f"set (value: {value})"))
    return Report(tuple(checks))


def render_report(report: Report) -> str:
    lines = ["Foundry Local preflight (read-only: nothing installed, no service contacted)"]
    for c in report.checks:
        tag = " OK " if c.ok else "FAIL"
        lines.append(f"[{tag}] {c.kind} {c.name}: {c.message}")
    bad = len(report.failures)
    if bad:
        lines.append(f"RESULT: FAILED - {bad} of {len(report.checks)} checks need attention")
    else:
        lines.append(f"RESULT: PASSED - {len(report.checks)} of {len(report.checks)} checks ok")
    return "\n".join(lines)


# --- worked-example fixtures (used by the demo, the README and the tests) --------
SPEC = Spec(
    executables=(
        ExecutableRequirement("foundry", "install Foundry Local (lesson Part 1), then re-run"),
        ExecutableRequirement("python", "install Python 3, then re-run"),
        ExecutableRequirement("pip", "install pip for your Python, then re-run"),
    ),
    config=(
        ConfigRequirement("MODEL", "set MODEL to a model alias such as phi-4-mini"),
        ConfigRequirement("BASE_URL", "set BASE_URL to your Foundry Local address"),
        ConfigRequirement("API_KEY", "set API_KEY (the lesson says local runs usually do not need one)",
                          secret=True),
    ),
)

DEMO_KEY = "demo-key-0000"  # an obviously fake value, used only to show that it is hidden

COMPLETE_PATH = ("foundry", "python", "pip")
COMPLETE_CONFIG = {"MODEL": "phi-4-mini", "BASE_URL": "http://localhost:8000", "API_KEY": DEMO_KEY}

BROKEN_PATH = ("foundry", "python")                              # pip is missing
BROKEN_CONFIG = {"MODEL": "phi-4-mini", "API_KEY": DEMO_KEY}     # BASE_URL is absent


def worked_example_a() -> str:
    return render_report(check_environment(SPEC, FakeProbe(COMPLETE_PATH), COMPLETE_CONFIG))


def worked_example_b() -> str:
    return render_report(check_environment(SPEC, FakeProbe(BROKEN_PATH), BROKEN_CONFIG))


def render_worked_examples() -> str:
    return worked_example_a() + "\n\n" + worked_example_b() + "\n"


def main() -> None:
    print(render_worked_examples(), end="")


if __name__ == "__main__":
    main()
