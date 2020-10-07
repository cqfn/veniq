from typing import List, Union
from pathlib import Path
from unittest import TestCase

from veniq.baselines.semi.filter import filter_extraction_opportunities
from veniq.baselines.semi._common_types import ExtractionOpportunity, Statement as ExtractionStatement
from veniq.ast_framework.block_statement_graph import build_block_statement_graph, Block, Statement
from veniq.ast_framework import AST, ASTNodeType
from veniq.utils.ast_builder import build_ast


class FilteringTestCase(TestCase):
    def test_non_continuos_statements_range(self):
        self._opportunity_test_helper([9, 15], False)

    def test_not_whole_block_selected(self):
        self._opportunity_test_helper([8, 9, 11, 12], False)

    def test_non_continuos_high_level_nodes(self):
        self._opportunity_test_helper([3, 19, 20, 21, 22], False)

    def test_statement_out_of_parent_block(self):
        self._opportunity_test_helper([11, 15], False)

    def test_correct_simple_opportunity(self):
        self._opportunity_test_helper([6, 7, 8, 9, 11, 12, 15], True)

    def test_correct_large_opportunity(self):
        self._opportunity_test_helper([5, 6, 7, 8, 9, 11, 12, 15, 19, 20, 21, 22], True)

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
    def _create_extraction_opportunity(method_ast: AST, statements_lines: List[int]) -> ExtractionOpportunity:
        extraction_opportunity_list: List[ExtractionStatement] = []
        block_statement_graph = build_block_statement_graph(method_ast)

        def fill_extraction_opportunity(node: Union[Block, Statement]):
            nonlocal extraction_opportunity_list
            if isinstance(node, Statement) and node.node.line in statements_lines:
                extraction_opportunity_list.append(node.node)

        block_statement_graph.traverse(fill_extraction_opportunity)
        return tuple(extraction_opportunity_list)

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
        filepath = current_directory / "ReturnTypeUseless.java"
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
