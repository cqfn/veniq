from itertools import zip_longest
from typing import List
from unittest import TestCase

from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.baselines.semi.alternatives.all_opportunities.create_all_opportunities import (
    create_extraction_opportunities,
)
from veniq.baselines.semi.filter_extraction_opportunities import filter_extraction_opportunities
from veniq.ast_framework import ASTNodeType
from ...utils import get_method_ast


class AllOpportunitiesFilteringTestCase(TestCase):
    def test_all_opportunities_filtering(self):
        ast = get_method_ast(
            "./alternatives/all_opportunities/TestAllOpportunitiesFiltering.java", "Test", "activatePart"
        )
        statements_semantic = extract_method_statements_semantic(ast)
        extraction_opportunities = create_extraction_opportunities(statements_semantic)
        extraction_opportunities = filter_extraction_opportunities(
            extraction_opportunities, statements_semantic, ast
        )

        for opportunity_index, (actual_opportunity, expected_opportunity_node_types) in enumerate(
            zip_longest(extraction_opportunities, self._expected_opportunities_nodes_types)
        ):
            actual_opportunity_node_types = list(map(lambda node: node.node_type, actual_opportunity))
            self.assertEqual(
                actual_opportunity_node_types,
                expected_opportunity_node_types,
                f"Failed comparing {opportunity_index}th opportunity "
                f"starting at line {actual_opportunity[0].line} and "
                f"ending on line {actual_opportunity[-1].line}.",
            )

    _expected_opportunities_nodes_types: List[List[ASTNodeType]] = [
        [ASTNodeType.STATEMENT_EXPRESSION],
        [
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [ASTNodeType.STATEMENT_EXPRESSION],
        [ASTNodeType.STATEMENT_EXPRESSION, ASTNodeType.LOCAL_VARIABLE_DECLARATION],
        [
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [ASTNodeType.LOCAL_VARIABLE_DECLARATION],
        [
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
        ],
        [ASTNodeType.STATEMENT_EXPRESSION],
        [ASTNodeType.STATEMENT_EXPRESSION],
        [ASTNodeType.STATEMENT_EXPRESSION],
    ]
