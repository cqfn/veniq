from typing import Dict, List
from unittest import TestCase

from networkx import DiGraph

from veniq.baselines.semi.extract_semantic import StatementSemantic
from veniq.baselines.semi.create_extraction_opportunities import create_extraction_opportunities
from veniq.ast_framework import ASTNode


class ExtractionOpportunitiesCreationTestCase(TestCase):
    def test_single_opportunity(self):
        statements_semantic = self._create_statements_semantic_stub(
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"x"}),
        )

        actual_statements_indexes = self._get_opportunity_nodes_indexes(statements_semantic)
        expected_statement_indexes = [[0, 1, 2]]
        self.assertEqual(expected_statement_indexes, actual_statements_indexes)

    def test_single_statement_and_all_statements_opportunities(self):
        statements_semantic = self._create_statements_semantic_stub(
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"y"}),
            StatementSemantic(used_objects={"x"}),
        )

        actual_statements_indexes = self._get_opportunity_nodes_indexes(statements_semantic)
        expected_statement_indexes = [[0], [1], [2], [0, 1, 2]]
        self.assertEqual(expected_statement_indexes, actual_statements_indexes)

    def test_single_statement_opportunities(self):
        statements_semantic = self._create_statements_semantic_stub(
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"y"}),
            StatementSemantic(used_methods={"y"}),
        )

        actual_statements_indexes = self._get_opportunity_nodes_indexes(statements_semantic)
        expected_statement_indexes = [[0], [1], [2]]
        self.assertEqual(expected_statement_indexes, actual_statements_indexes)

    @staticmethod
    def _get_opportunity_nodes_indexes(
        statements_semantic: Dict[ASTNode, StatementSemantic]
    ) -> List[List[int]]:
        extraction_opportunities = create_extraction_opportunities(statements_semantic)
        return [[node.node_index for node in opportunity] for opportunity in extraction_opportunities]

    @staticmethod
    def _create_statements_semantic_stub(*semantics: StatementSemantic) -> Dict[ASTNode, StatementSemantic]:
        stub_graph = DiGraph()
        return {ASTNode(stub_graph, index): semantic for index, semantic in enumerate(semantics)}
