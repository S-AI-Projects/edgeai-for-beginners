"""
R04-T012: Prompt Template Escaping and Boundary Validation
Companion applied lab for Module08/05.AIPoweredAgents.md.

Demonstrates safe, deterministic prompt template rendering:
- Declares explicit template variables.
- Requires all declared variables (missing variable fails).
- Rejects undeclared/unknown variables.
- Treats user data strictly as literal strings; curly braces inside user values
  remain literal and are never evaluated as template tags.
- Disclaims that templating alone does NOT prevent prompt injection.

Prerequisites: Python 3 standard library only.
"""

import re
from typing import Any, Dict, Set


class TemplateError(Exception):
    """Raised when template validation or rendering fails."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class PromptTemplate:
    """
    Deterministic prompt template engine with strict variable validation
    and literal data substitution.
    """

    VAR_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def __init__(self, template_str: str):
        if not isinstance(template_str, str) or not template_str.strip():
            raise TemplateError("INVALID_TEMPLATE", "Template must be a non-empty string.")
        self.template_str = template_str
        # Extract declared variables from the template structure
        self.declared_variables: Set[str] = set(self.VAR_PATTERN.findall(template_str))
        if not self.declared_variables:
            raise TemplateError("INVALID_TEMPLATE", "Template contains no valid {variable} placeholders.")

    def render(self, values: Dict[str, Any]) -> str:
        """
        Renders the template with supplied values.
        - Fails if any declared variable is missing.
        - Fails if any unknown/undeclared variable is supplied.
        - Preserves literal braces in user values without secondary evaluation.
        """
        if not isinstance(values, dict):
            raise TemplateError("INVALID_INPUT", f"Values must be a dict, got {type(values).__name__}.")

        supplied_keys = set(values.keys())

        # Check for missing required variables
        missing = self.declared_variables - supplied_keys
        if missing:
            missing_sorted = sorted(list(missing))
            raise TemplateError(
                "MISSING_VARIABLE",
                f"Missing required template variable(s): {', '.join(missing_sorted)}"
            )

        # Check for unknown / undeclared variables
        unknown = supplied_keys - self.declared_variables
        if unknown:
            unknown_sorted = sorted(list(unknown))
            raise TemplateError(
                "UNKNOWN_VARIABLE",
                f"Unknown variable(s) supplied: {', '.join(unknown_sorted)}"
            )

        # Validate values are strings
        for k, v in values.items():
            if not isinstance(v, str):
                raise TemplateError("INVALID_VALUE", f"Value for '{k}' must be a string, got {type(v).__name__}.")

        # Single-pass substitution: replace each placeholder with literal string value
        # Using a regex replacer function ensures user data is NEVER scanned for template tokens.
        def replace_token(match: re.Match) -> str:
            var_name = match.group(1)
            return values[var_name]

        return self.VAR_PATTERN.sub(replace_token, self.template_str)


# Canonical task fixture
CANONICAL_TEMPLATE = "Hello {name}, your assigned topic is {topic}."


def run_concept_example() -> Dict[str, Any]:
    """Runs the canonical fixture and boundary cases."""
    tmpl = PromptTemplate(CANONICAL_TEMPLATE)

    # 1. Normal case: valid name and topic
    valid_data = {"name": "Alice", "topic": "Edge AI"}
    rendered_normal = tmpl.render(valid_data)

    # 2. Boundary case: user data contains literal curly braces
    boundary_data = {
        "name": "Bob {admin=True}",
        "topic": "SLMs with {nested_payload}"
    }
    rendered_boundary = tmpl.render(boundary_data)

    # 3. Missing variable case (missing 'topic')
    missing_rejected = False
    missing_code = None
    try:
        tmpl.render({"name": "Charlie"})
    except TemplateError as exc:
        missing_rejected = True
        missing_code = exc.code

    # 4. Unknown variable case
    unknown_rejected = False
    unknown_code = None
    try:
        tmpl.render({"name": "Dave", "topic": "Robotics", "role": "admin"})
    except TemplateError as exc:
        unknown_rejected = True
        unknown_code = exc.code

    return {
        "rendered_normal": rendered_normal,
        "rendered_boundary": rendered_boundary,
        "missing_rejected": missing_rejected,
        "missing_code": missing_code,
        "unknown_rejected": unknown_rejected,
        "unknown_code": unknown_code,
    }


if __name__ == "__main__":
    result = run_concept_example()
    print("=== Prompt Template Escaping Example ===")
    print(f"Normal Render: {result['rendered_normal']}")
    print(f"Boundary Render (literal braces preserved): {result['rendered_boundary']}")
    print(f"Missing variable rejection: {result['missing_rejected']} (code: {result['missing_code']})")
    print(f"Unknown variable rejection: {result['unknown_rejected']} (code: {result['unknown_code']})")
    print("\n[NOTE] Safe templating ensures structural separation; it does NOT prevent semantic prompt injection.")
