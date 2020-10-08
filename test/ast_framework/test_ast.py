from unittest import TestCase
from pathlib import Path
from itertools import zip_longest

from veniq.ast_framework import ASTNodeType, build_ast


class ASTTestSuite(TestCase):
    def test_parsing(self):
        ast = build_ast(self._current_directory / "SimpleClass.java")
        actual_node_types = [node.node_type for node in ast]
        self.assertEqual(actual_node_types, ASTTestSuite._java_simple_class_preordered)

    def test_subtrees_selection(self):
        ast = build_ast(self._current_directory / "SimpleClass.java")
        subtrees = ast.get_subtrees(ASTNodeType.BASIC_TYPE)
        for actual_subtree, expected_subtree in zip_longest(
            subtrees, ASTTestSuite._java_simple_class_basic_type_subtrees
        ):
            with self.subTest():
                self.assertEqual([node.node_index for node in actual_subtree], expected_subtree)

    def test_complex_fields(self):
        ast = build_ast(self._current_directory / "StaticConstructor.java")
        class_declaration = next(
            (
                declaration
                for declaration in ast.get_root().types
                if declaration.node_type == ASTNodeType.CLASS_DECLARATION
            ),
            None,
        )
        assert class_declaration is not None, "Cannot find class declaration"

        static_constructor, method_declaration = class_declaration.body
        self.assertEqual(
            [node.node_type for node in static_constructor],
            [ASTNodeType.STATEMENT_EXPRESSION, ASTNodeType.STATEMENT_EXPRESSION],
        )
        self.assertEqual(method_declaration.node_type, ASTNodeType.METHOD_DECLARATION)

    _current_directory = Path(__file__).absolute().parent

    _java_simple_class_preordered = [
        ASTNodeType.COMPILATION_UNIT,
        ASTNodeType.CLASS_DECLARATION,
        ASTNodeType.COLLECTION,
        ASTNodeType.STRING,
        ASTNodeType.FIELD_DECLARATION,
        ASTNodeType.COLLECTION,
        ASTNodeType.STRING,
        ASTNodeType.BASIC_TYPE,
        ASTNodeType.STRING,
        ASTNodeType.VARIABLE_DECLARATOR,
        ASTNodeType.STRING,
        ASTNodeType.LITERAL,
        ASTNodeType.STRING,
        ASTNodeType.METHOD_DECLARATION,
        ASTNodeType.COLLECTION,
        ASTNodeType.STRING,
        ASTNodeType.BASIC_TYPE,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
        ASTNodeType.STATEMENT_EXPRESSION,
        ASTNodeType.ASSIGNMENT,
        ASTNodeType.MEMBER_REFERENCE,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
        ASTNodeType.LITERAL,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
        ASTNodeType.RETURN_STATEMENT,
        ASTNodeType.MEMBER_REFERENCE,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
    ]

    _java_simple_class_basic_type_subtrees = [
        [8, 9],
        [17, 18],
    ]
