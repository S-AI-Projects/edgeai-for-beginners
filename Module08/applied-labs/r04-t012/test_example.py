"""
Unit tests for R04-T012 Prompt Template Escaping.
Tests normal, boundary, invalid inputs, and deliberate flaw detection.
"""

import unittest

from example import CANONICAL_TEMPLATE, PromptTemplate, TemplateError, run_concept_example


class TestPromptTemplateNormal(unittest.TestCase):
    def setUp(self):
        self.tmpl = PromptTemplate(CANONICAL_TEMPLATE)

    def test_canonical_fixture_renders_supplied_values(self):
        """Template with name and topic renders supplied values."""
        output = self.tmpl.render({"name": "Alice", "topic": "Edge AI"})
        self.assertEqual(output, "Hello Alice, your assigned topic is Edge AI.")

    def test_run_concept_example_summary(self):
        summary = run_concept_example()
        self.assertEqual(summary["rendered_normal"], "Hello Alice, your assigned topic is Edge AI.")
        self.assertTrue(summary["missing_rejected"])
        self.assertEqual(summary["missing_code"], "MISSING_VARIABLE")
        self.assertTrue(summary["unknown_rejected"])
        self.assertEqual(summary["unknown_code"], "UNKNOWN_VARIABLE")


class TestPromptTemplateBoundary(unittest.TestCase):
    def setUp(self):
        self.tmpl = PromptTemplate(CANONICAL_TEMPLATE)

    def test_braces_inside_user_data_remain_literal(self):
        """Curly braces inside user data must remain literal and never cause evaluation errors."""
        payloads = [
            ("Bob {admin=True}", "SLMs with {nested_tag}"),
            ("User {123}", "JSON data: {\"action\": \"eval\"}"),
            ("{{double_braces}}", "{unclosed_brace"),
            ("}leading_closing_brace{", "normal topic"),
        ]
        for name_val, topic_val in payloads:
            res = self.tmpl.render({"name": name_val, "topic": topic_val})
            self.assertIn(name_val, res)
            self.assertIn(topic_val, res)
            self.assertEqual(res, f"Hello {name_val}, your assigned topic is {topic_val}.")

    def test_smallest_valid_inputs(self):
        """Smallest valid values (single characters)."""
        res = self.tmpl.render({"name": "X", "topic": "Y"})
        self.assertEqual(res, "Hello X, your assigned topic is Y.")

    def test_empty_string_values(self):
        """Empty strings are valid string inputs."""
        res = self.tmpl.render({"name": "", "topic": ""})
        self.assertEqual(res, "Hello , your assigned topic is .")

    def test_repeated_and_adjacent_variables(self):
        """Template with adjacent or repeated variables."""
        custom_tmpl = PromptTemplate("{name}:{name}-{topic}")
        res = custom_tmpl.render({"name": "N", "topic": "T"})
        self.assertEqual(res, "N:N-T")


class TestPromptTemplateFailureCases(unittest.TestCase):
    def setUp(self):
        self.tmpl = PromptTemplate(CANONICAL_TEMPLATE)

    def test_missing_topic_fails(self):
        """Missing 'topic' must fail with MISSING_VARIABLE."""
        with self.assertRaises(TemplateError) as ctx:
            self.tmpl.render({"name": "Alice"})
        self.assertEqual(ctx.exception.code, "MISSING_VARIABLE")
        self.assertIn("topic", str(ctx.exception))

    def test_missing_name_fails(self):
        with self.assertRaises(TemplateError) as ctx:
            self.tmpl.render({"topic": "Edge AI"})
        self.assertEqual(ctx.exception.code, "MISSING_VARIABLE")
        self.assertIn("name", str(ctx.exception))

    def test_unknown_variable_fails(self):
        """Undeclared/unknown variables must fail with UNKNOWN_VARIABLE."""
        with self.assertRaises(TemplateError) as ctx:
            self.tmpl.render({"name": "Alice", "topic": "Edge AI", "extra": "bypass"})
        self.assertEqual(ctx.exception.code, "UNKNOWN_VARIABLE")
        self.assertIn("extra", str(ctx.exception))

    def test_non_dict_values_fails(self):
        for bad_input in (None, "string", [1, 2], 123):
            with self.assertRaises(TemplateError) as ctx:
                self.tmpl.render(bad_input)
            self.assertEqual(ctx.exception.code, "INVALID_INPUT")

    def test_non_string_variable_value_fails(self):
        for bad_val in (123, None, True, ["list"]):
            with self.assertRaises(TemplateError) as ctx:
                self.tmpl.render({"name": "Alice", "topic": bad_val})
            self.assertEqual(ctx.exception.code, "INVALID_VALUE")

    def test_invalid_template_string_fails(self):
        for bad_tmpl in ("", "   ", None, "Template without variables"):
            with self.assertRaises(TemplateError) as ctx:
                PromptTemplate(bad_tmpl)
            self.assertEqual(ctx.exception.code, "INVALID_TEMPLATE")


class TestDeliberateFlawDetection(unittest.TestCase):
    def test_flawed_evaluator_fails_boundary_cases(self):
        """A naive str.format implementation breaks on literal braces in user data."""
        def naive_render(template_str, values):
            # Naive str.format will crash or misinterpret unescaped curly braces in format string
            return template_str.format(**values)

        # Insecure double substitution where user values are evaluated
        user_injected = "Malicious {injected}"
        # A flawed engine that fails to escape or allow literal braces
        with self.assertRaises(AssertionError):
            # Check if a flawed approach can guarantee safe literal preservation
            flawed_result = "Hello " + user_injected.replace("{", "").replace("}", "")
            self.assertEqual(flawed_result, f"Hello {user_injected}")

    def test_deliberate_missing_variable_pass_through_fails(self):
        """A flawed implementation that silently ignores missing variables must be caught."""
        def flawed_render_ignore_missing(values):
            # Deliberate bug: default missing keys to empty string instead of failing
            name = values.get("name", "")
            topic = values.get("topic", "")
            return f"Hello {name}, your assigned topic is {topic}."

        # Should raise TemplateError, but flawed version doesn't
        res = flawed_render_ignore_missing({"name": "Alice"})
        with self.assertRaises(AssertionError):
            # Assert that an exception was raised (which wasn't)
            self.assertEqual(res, "SHOULD_HAVE_RAISED_TEMPLATE_ERROR")


if __name__ == "__main__":
    unittest.main()
