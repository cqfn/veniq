from itertools import zip_longest
from typing import List, Optional
from unittest import TestCase

from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.baselines.semi.alternatives.all_opportunities.create_all_opportunities import (
    create_extraction_opportunities,
)
from veniq.ast_framework import ASTNodeType
from ...utils import get_method_ast


class AllOpportunitiesCreationTestCase(TestCase):
    def test_all_opportunities_creation(self):
        ast = get_method_ast("./alternatives/all_opportunities/TestAllOpportunitiesCreation.java", "Test", "test")
        statements_semantic = extract_method_statements_semantic(ast)
        actual_extraction_opportunities = create_extraction_opportunities(statements_semantic)
        for opportunity_index, (actual_opportunity, expected_opportunity_node_types) in enumerate(
            zip_longest(actual_extraction_opportunities, self._expected_opportunities_nodes_types)
        ):
            actual_opportunity_node_types = list(map(lambda node: node.node_type, actual_opportunity))
            self.assertEqual(
                actual_opportunity_node_types,
                expected_opportunity_node_types,
                f"Failed comparing {opportunity_index}th opportunity "
                f"starting at line {actual_opportunity[0].line} and "
                f"ending on line {actual_opportunity[-1].line}."
            )

    _expected_opportunities_nodes_types: List[List[Optional[ASTNodeType]]] = [
        [ASTNodeType.LOCAL_VARIABLE_DECLARATION],
        [ASTNodeType.LOCAL_VARIABLE_DECLARATION, ASTNodeType.FOR_STATEMENT],
        [ASTNodeType.LOCAL_VARIABLE_DECLARATION, ASTNodeType.FOR_STATEMENT, ASTNodeType.STATEMENT_EXPRESSION],
        [ASTNodeType.LOCAL_VARIABLE_DECLARATION, ASTNodeType.FOR_STATEMENT, ASTNodeType.STATEMENT_EXPRESSION, None],
        [ASTNodeType.FOR_STATEMENT],
        [ASTNodeType.FOR_STATEMENT, ASTNodeType.STATEMENT_EXPRESSION],
        [ASTNodeType.FOR_STATEMENT, ASTNodeType.STATEMENT_EXPRESSION, None],
        [ASTNodeType.STATEMENT_EXPRESSION],
        [ASTNodeType.STATEMENT_EXPRESSION, None],
        [None],
    ]
