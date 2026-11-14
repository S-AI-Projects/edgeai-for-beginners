import unittest

from example import (CAPABILITIES, CLIENT_CAPS, SERVER_CAPS, NegotiationError, _subsets,
                     equivalence_report, invoke_baseline, invoke_refactored, make_handlers,
                     negotiate_capabilities, run_case)

IMPLEMENTATIONS = (("baseline", invoke_baseline), ("refactored", invoke_refactored))


class Both(unittest.TestCase):
    """Every scenario is run against BOTH versions: the contract must not change."""

    def each(self):
        for label, impl in IMPLEMENTATIONS:
            with self.subTest(version=label):
                yield impl

    def call(self, impl, client, server, capability, handler_names=CAPABILITIES):
        return run_case(impl, client, server, capability, handler_names)


class TaskFixture(Both):
    def test_client_tools_resources_server_tools_prompts_negotiates_tools(self):
        self.assertEqual(negotiate_capabilities(CLIENT_CAPS, SERVER_CAPS), frozenset({"tools"}))

    def test_tools_is_dispatched(self):
        for impl in self.each():
            self.assertEqual(self.call(impl, CLIENT_CAPS, SERVER_CAPS, "tools"),
                             ("ok", "tools-handled:ping", ("tools",)))

    def test_resources_is_rejected_before_dispatch(self):
        for impl in self.each():
            self.assertEqual(self.call(impl, CLIENT_CAPS, SERVER_CAPS, "resources"),
                             ("error", "NOT_NEGOTIATED", ()))  # () = no handler ran

    def test_server_only_capability_is_rejected_before_dispatch(self):
        for impl in self.each():
            self.assertEqual(self.call(impl, CLIENT_CAPS, SERVER_CAPS, "prompts"),
                             ("error", "NOT_NEGOTIATED", ()))


class BoundaryCases(Both):
    def test_empty_intersection_rejects_everything(self):
        for impl in self.each():
            for capability in CAPABILITIES:
                self.assertEqual(self.call(impl, {"tools"}, {"prompts"}, capability)[:2],
                                 ("error", "NOT_NEGOTIATED"))

    def test_empty_sets_are_valid_and_negotiate_nothing(self):
        self.assertEqual(negotiate_capabilities(set(), set()), frozenset())
        self.assertEqual(negotiate_capabilities({"tools"}, set()), frozenset())

    def test_identical_sets_allow_everything(self):
        for impl in self.each():
            for capability in CAPABILITIES:
                self.assertEqual(self.call(impl, set(CAPABILITIES), set(CAPABILITIES), capability)[0], "ok")

    def test_matching_is_exact_and_case_sensitive(self):
        self.assertEqual(negotiate_capabilities({"Tools"}, {"tools"}), frozenset())
        for impl in self.each():
            self.assertEqual(self.call(impl, {"Tools"}, {"tools"}, "tools")[:2], ("error", "NOT_NEGOTIATED"))

    def test_lists_tuples_and_duplicates_are_accepted(self):
        self.assertEqual(negotiate_capabilities(["tools", "tools", "resources"], ("tools", "prompts")),
                         frozenset({"tools"}))

    def test_negotiated_capability_without_a_handler_is_reported(self):
        for impl in self.each():
            self.assertEqual(self.call(impl, CLIENT_CAPS, SERVER_CAPS, "tools", handler_names=())[:2],
                             ("error", "NO_HANDLER"))

    def test_gate_comes_before_the_handler_lookup(self):
        # not negotiated AND no handler registered: the answer is NOT_NEGOTIATED, not NO_HANDLER
        for impl in self.each():
            self.assertEqual(self.call(impl, CLIENT_CAPS, SERVER_CAPS, "resources", handler_names=())[:2],
                             ("error", "NOT_NEGOTIATED"))

    def test_handler_errors_are_not_swallowed(self):
        def boom(_):
            raise ValueError("handler failed")
        for impl in self.each():
            with self.assertRaises(ValueError):
                impl({"tools"}, {"tools"}, "tools", "ping", {"tools": boom})

    def test_inputs_are_not_modified(self):
        client, server = set(CLIENT_CAPS), set(SERVER_CAPS)
        negotiate_capabilities(client, server)
        self.assertEqual((client, server), (CLIENT_CAPS, SERVER_CAPS))


class FailureCases(Both):
    def assertCode(self, impl, client, server, capability, code):
        with self.assertRaises(NegotiationError) as ctx:
            impl(client, server, capability, "ping", {})
        self.assertEqual(ctx.exception.code, code)

    def test_a_bare_string_is_not_a_capability_set(self):
        # "tools" would silently become the characters t, o, o, l, s if iterated
        for impl in self.each():
            self.assertCode(impl, "tools", {"tools"}, "tools", "BAD_CAPABILITY_SET")
            self.assertCode(impl, {"tools"}, "tools", "tools", "BAD_CAPABILITY_SET")

    def test_none_and_non_collections_are_rejected(self):
        for impl in self.each():
            for bad in (None, 5, {"a": 1}):
                self.assertCode(impl, bad, {"tools"}, "tools", "BAD_CAPABILITY_SET")

    def test_non_string_or_empty_members_are_rejected(self):
        for impl in self.each():
            for bad in ({1}, {""}, [None], {"tools", 2}):
                self.assertCode(impl, bad, {"tools"}, "tools", "BAD_CAPABILITY_SET")

    def test_bad_request_capability_is_rejected(self):
        for impl in self.each():
            for bad in ("", None, 3):
                self.assertCode(impl, {"tools"}, {"tools"}, bad, "BAD_REQUEST")

    def test_unknown_capability_is_not_negotiated(self):
        for impl in self.each():
            self.assertCode(impl, {"tools"}, {"tools"}, "telepathy", "NOT_NEGOTIATED")


class NegotiationProperties(unittest.TestCase):
    def test_result_is_the_common_subset_and_order_independent(self):
        for a in _subsets(CAPABILITIES):
            for b in _subsets(CAPABILITIES):
                result = negotiate_capabilities(a, b)
                self.assertEqual(result, negotiate_capabilities(b, a))
                self.assertTrue(result <= a and result <= b)

    def test_handlers_record_calls(self):
        log = []
        make_handlers(["tools"], log)["tools"]("x")
        self.assertEqual(log, ["tools"])


class BeforeAfterEquivalence(unittest.TestCase):
    def test_baseline_and_refactor_agree_on_every_generated_case(self):
        checked, mismatches = equivalence_report()
        self.assertEqual(checked, 8 * 8 * 4 * 2)  # a non-zero, known case count
        self.assertEqual(mismatches, [])

    def test_the_comparison_can_fail(self):
        # a deliberately wrong "refactor" that forgets to gate must be caught
        def ungated(client, server, capability, payload, handlers):
            handler = handlers.get(capability)
            if handler is None:
                raise NegotiationError("NO_HANDLER", "no handler")
            return handler(payload)
        _, mismatches = equivalence_report(invoke_baseline, ungated)
        self.assertGreater(len(mismatches), 0)

    def test_a_refactor_that_uses_a_union_must_be_caught(self):
        def union_version(client, server, capability, payload, handlers):
            if capability not in (set(client) | set(server)):
                raise NegotiationError("NOT_NEGOTIATED", "x")
            return invoke_baseline(set(CAPABILITIES), set(CAPABILITIES), capability, payload, handlers)
        _, mismatches = equivalence_report(invoke_baseline, union_version)
        self.assertGreater(len(mismatches), 0)


if __name__ == "__main__":
    unittest.main()
