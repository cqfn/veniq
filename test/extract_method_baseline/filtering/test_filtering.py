from typing import List
from pathlib import Path
from unittest import TestCase

from veniq.baselines.semi.filter import filter_extraction_opportunities, ExtractionOpportunity
from veniq.ast_framework import AST, ASTNode, ASTNodeType
from veniq.utils.ast_builder import build_ast


class FilteringTestCase(TestCase):
    def test_non_continuos_statements_range(self):
        self._opportunity_test_helper([59, 71], False)

    def test_not_whole_block_selected(self):
        self._opportunity_test_helper([55, 59, 66, 67], False)

    def test_non_continuos_high_level_nodes(self):
        self._opportunity_test_helper([25, 78, 100, 109, 113], False)

    def test_statement_out_of_parent_block(self):
        self._opportunity_test_helper([67, 71], False)

    def test_correct_simple_opportunity(self):
        self._opportunity_test_helper([41, 50, 55, 59, 66, 67, 71], True)

    def test_correct_large_opportunity(self):
        self._opportunity_test_helper([32, 41, 50, 55, 59, 66, 67, 71, 78, 100, 109, 113, 118], True)

    def _opportunity_test_helper(
        self, extraction_opportunity_statements_ids: List[int], is_opportunity_correct: bool
    ):
        method_ast = self._get_method_ast()
        extraction_opportunity = self._create_extraction_opportunity(
            method_ast, extraction_opportunity_statements_ids
        )
        self.assertEqual(
            self._is_correct_extraction_opportunity(extraction_opportunity, method_ast),
            is_opportunity_correct,
        )

    @staticmethod
    def _create_extraction_opportunity(method_ast: AST, statements_ids: List[int]) -> ExtractionOpportunity:
        return [ASTNode(method_ast.tree, statement_id) for statement_id in statements_ids]

    @staticmethod
    def _is_correct_extraction_opportunity(
        extraction_opportunity: ExtractionOpportunity, method_ast: AST
    ) -> bool:
        filtered_extraction_opportunities = filter_extraction_opportunities(
            [extraction_opportunity], method_ast
        )
        return len(filtered_extraction_opportunities) == 1  # the given item was kept

    @staticmethod
    def _get_method_ast() -> AST:
        current_directory = Path(__file__).absolute().parent
        filepath = current_directory / "Example.java"
        ast = AST.build_from_javalang(build_ast(str(filepath)))

        try:
            class_declaration = next(
                node
                for node in ast.get_root().types
                if node.node_type == ASTNodeType.CLASS_DECLARATION and node.name == "Example"
            )

            method_declaration = next(
                node for node in class_declaration.methods if node.name == "exampleMethod"
            )
        except StopIteration:
            raise RuntimeError(f"Failed to find method 'exampleMethod' in class 'Example' in file {filepath}")

        return ast.get_subtree(method_declaration)
