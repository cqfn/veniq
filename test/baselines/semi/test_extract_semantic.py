from typing import List
from itertools import zip_longest
from unittest import TestCase

from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.baselines.semi._common_types import StatementSemantic
from .utils import objects_semantic, get_method_ast


class ExtractStatementSemanticTestCase(TestCase):
    def test_block_method(self):
        self._test_helper("block", [objects_semantic("x")])

    def test_for_cycle_method(self):
        self._test_helper("forCycle", [objects_semantic("x", "i"), objects_semantic("x", "i", "result")])

    def test_while_cycle_method(self):
        self._test_helper("whileCycle", [objects_semantic("x"), objects_semantic("x")])

    def test_do_while_cycle_method(self):
        self._test_helper("doWhileCycle", [objects_semantic("x"), objects_semantic("x")])

    def test_if_branching_method(self):
        self._test_helper("ifBranching", [
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
        ])

    def test_synchronized_block_method(self):
        self._test_helper("synchronizedBlock", [objects_semantic("x"), objects_semantic("x")])

    def test_switch_branching_method(self):
        self._test_helper("switchBranching", [
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
        ])

    def test_try_block_method(self):
        self._test_helper("tryBlock", [
            objects_semantic("x", "resource"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
        ])

    def test_assert_statement_method(self):
        self._test_helper("assertStatement", [objects_semantic("x")])

    def test_return_statement_method(self):
        self._test_helper("returnStatement", [objects_semantic("x")])

    def test_expression_method(self):
        self._test_helper("expression", [objects_semantic("x")])

    def test_throw_statement_method(self):
        self._test_helper("throwStatement", [objects_semantic("x")])

    def test_local_variable_declaration_method(self):
        self._test_helper("localVariableDeclaration", [objects_semantic("x")])

    def test_break_statement_method(self):
        self._test_helper("breakStatement", [StatementSemantic(), StatementSemantic()])

    def test_continue_statement_method(self):
        self._test_helper("continueStatement", [StatementSemantic(), StatementSemantic()])

    def test_local_method_call_method(self):
        self._test_helper("localMethodCall", [StatementSemantic(used_methods={"localMethod"})])

    def test_object_method_call_method(self):
        self._test_helper("objectMethodCall", [StatementSemantic(used_objects={"o"}, used_methods={"method"})])

    def test_nested_object_method(self):
        self._test_helper("nestedObject", [StatementSemantic(used_objects={"o.x"})])

    def test_nested_object_method_call_method(self):
        self._test_helper("nestedObjectMethodCall", [
            StatementSemantic(used_objects={"o.nestedObject"}, used_methods={"method"})
        ])

    def test_several_statement_method(self):
        self._test_helper("severalStatements", [
            objects_semantic("x"),
            objects_semantic("x"),
            StatementSemantic(used_objects={"System.out", "x"}, used_methods={"println"}),
            objects_semantic("x"),
        ])

    def test_deep_nesting_method(self):
        self._test_helper("deepNesting", [
            objects_semantic("i"),
            objects_semantic("i"),
            StatementSemantic(used_objects={"System.out", "i"}, used_methods={"println"}),
            StatementSemantic(used_objects={"System.out"}, used_methods={"println"}),
        ])

    def test_complex_expressions_method(self):
        self._test_helper("complexExpressions", [
            objects_semantic("x", "y"),
            objects_semantic("o1", "o2"),
            StatementSemantic(used_objects={"o1", "x", "y", "z"}, used_methods={"method", "secondMethod"}),
            StatementSemantic(
                used_objects={"o1", "o2", "z"},
                used_methods={"method", "thirdMethod", "fourthMethod", "temporalMethod"},
            ),
        ])

    def test_multiline_statement_method(self):
        self._test_helper("multilineStatement", [objects_semantic("x", "y", "o")])

    def test_multiple_statements_per_line_method(self):
        self._test_helper("multipleStatementsPerLine", [
            StatementSemantic(used_methods={"localMethod"}, used_objects={"x"}),
            StatementSemantic(used_methods={"localMethod"}, used_objects={"y"}),
        ])

    def _test_helper(self, method_name: str, expected_statements_semantics: List[StatementSemantic]):
        method_ast = get_method_ast("SemanticExtractionTest.java", "SimpleMethods", method_name)
        method_semantic = extract_method_statements_semantic(method_ast)
        for (
            comparison_index,
            (statement, actual_statement_semantic, expected_statement_semantic),
        ) in enumerate(
            zip_longest(
                method_semantic.keys(),
                method_semantic.values(),
                expected_statements_semantics,
            )
        ):
            self.assertEqual(
                actual_statement_semantic,
                expected_statement_semantic,
                f"{comparison_index}th comparison failed for {statement.node_type} on line {statement.line}.",
            )
