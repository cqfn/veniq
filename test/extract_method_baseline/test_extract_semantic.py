from itertools import zip_longest
from pathlib import Path
from unittest import TestCase

from veniq.ast_framework import AST
from veniq.utils.ast_builder import build_ast
from veniq.baselines.semi.extract_semantic import (
    extract_method_statements_semantic,
    StatementSemantic,
)


def objects_semantic(*objects_names: str) -> StatementSemantic:
    return StatementSemantic(used_objects=set(objects_names))


class ExtractStatementSemanticTestCase(TestCase):
    current_directory = Path(__file__).absolute().parent

    def test_semantic_extraction(self):
        ast = AST.build_from_javalang(build_ast(self.current_directory / "SimpleMethods.java"))
        class_declaration = ast.get_root().types[0]
        assert class_declaration.name == "SimpleMethods", "Wrong java test class"

        for method_declaration in class_declaration.methods:
            with self.subTest(f"Test {method_declaration.name} method."):
                method_semantic = extract_method_statements_semantic(ast.get_subtree(method_declaration))
                items_for_comparison = enumerate(
                    zip_longest(
                        method_semantic.keys(),
                        method_semantic.values(),
                        self.expected_semantic[method_declaration.name],
                    )
                )
                for (
                    comparison_index,
                    (statement, actual_statement_semantic, expected_statement_semantic),
                ) in items_for_comparison:
                    with self.subTest(
                        f"Comparing {comparison_index}th statement {repr(statement)} "
                        f"on line {statement.line} of method {method_declaration.name}."
                    ):
                        self.assertEqual(actual_statement_semantic, expected_statement_semantic)

    expected_semantic = {
        "block": [objects_semantic("x")],
        "forCycle": [objects_semantic("x", "i"), objects_semantic("x", "i", "result")],
        "whileCycle": [objects_semantic("x"), objects_semantic("x")],
        "doWhileCycle": [objects_semantic("x"), objects_semantic("x")],
        "ifBranching": [
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
        ],
        "synchronizedBlock": [objects_semantic("x"), objects_semantic("x")],
        "switchBranching": [
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
        ],
        "tryBlock": [
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
            objects_semantic("x"),
        ],
        "assertStatement": [objects_semantic("x")],
        "returnStatement": [objects_semantic("x")],
        "expression": [objects_semantic("x")],
        "throwStatement": [objects_semantic("x")],
        "localVariableDeclaration": [objects_semantic("x")],
        "breakStatement": [StatementSemantic(), StatementSemantic()],
        "continueStatement": [StatementSemantic(), StatementSemantic()],
        "localMethodCall": [StatementSemantic(used_methods={"localMethod"})],
        "objectMethodCall": [StatementSemantic(used_objects={"o"}, used_methods={"method"})],
        "nestedObject": [StatementSemantic(used_objects={"o", "x"})],
        "nestedObjectMethodCall": [
            StatementSemantic(used_objects={"o", "nestedObject"}, used_methods={"method"})
        ],
        "severalStatements": [
            objects_semantic("x"),
            objects_semantic("x"),
            StatementSemantic(used_objects={"System", "out", "x"}, used_methods={"println"}),
            objects_semantic("x"),
        ],
        "deepNesting": [
            objects_semantic("i"),
            objects_semantic("i"),
            StatementSemantic(used_objects={"System", "out", "i"}, used_methods={"println"}),
            StatementSemantic(used_objects={"System", "out"}, used_methods={"println"}),
        ],
        "complexExpressions": [
            objects_semantic("x", "y"),
            objects_semantic("o1", "o2"),
            StatementSemantic(used_objects={"o1", "x", "y", "z"}, used_methods={"method", "secondMethod"}),
            StatementSemantic(
                used_objects={"o1", "o2", "z"},
                used_methods={"method", "thirdMethod", "fourthMethod", "temporalMethod"},
            ),
        ],
        "multilineStatement": [objects_semantic("x", "y", "o")],
        "multipleStatementsPerLine": [
            StatementSemantic(used_methods={"localMethod"}, used_objects={"x"}),
            StatementSemantic(used_methods={"localMethod"}, used_objects={"y"}),
        ],
    }
