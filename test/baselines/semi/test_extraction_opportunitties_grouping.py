from typing import Dict, Tuple
from unittest import TestCase

from networkx import DiGraph

from veniq.baselines.semi._common_types import Statement, StatementSemantic, ExtractionOpportunity
from veniq.baselines.semi.rank_extraction_opportunities import (
    ExtractionOpportunityGroupSettings,
    ExtractionOpportunityGroup,
)
from veniq.ast_framework import ASTNode


class ExtractionOpportunitiesGroupingTestCase(TestCase):
    def test_groupable_extraction_opportunity(self):
        (
            extraction_opportunity1,
            extraction_opportunity2,
            statements_semantic,
        ) = self._create_extraction_opportunities_stubs(7, 7, 10)

        extraction_opportunity_group = ExtractionOpportunityGroup(
            extraction_opportunity1, statements_semantic, self._settings
        )

        self.assertTrue(extraction_opportunity_group.is_allowed_to_add_opportunity(extraction_opportunity2))

    def test_oversized_extraction_opportunity(self):
        (
            extraction_opportunity1,
            extraction_opportunity2,
            statements_semantic,
        ) = self._create_extraction_opportunities_stubs(3, 9, 10)

        extraction_opportunity_group = ExtractionOpportunityGroup(
            extraction_opportunity1, statements_semantic, self._settings
        )

        self.assertFalse(extraction_opportunity_group.is_allowed_to_add_opportunity(extraction_opportunity2))

    def test_distinct_extraction_opportunity(self):
        (
            extraction_opportunity1,
            extraction_opportunity2,
            statements_semantic,
        ) = self._create_extraction_opportunities_stubs(3, 3, 10)

        extraction_opportunity_group = ExtractionOpportunityGroup(
            extraction_opportunity1, statements_semantic, self._settings
        )

        self.assertFalse(extraction_opportunity_group.is_allowed_to_add_opportunity(extraction_opportunity2))

    @staticmethod
    def _create_extraction_opportunities_stubs(
        first_opportunity_size: int, second_opportunity_size: int, total_statements_size: int
    ) -> Tuple[ExtractionOpportunity, ExtractionOpportunity, Dict[Statement, StatementSemantic]]:
        statements_semantic = ExtractionOpportunitiesGroupingTestCase._create_statement_semantic_stub(
            total_statements_size
        )
        statements = list(statements_semantic.keys())
        extraction_opportunity1 = tuple(statements[:first_opportunity_size])
        extraction_opportunity2 = tuple(statements[-second_opportunity_size:])
        return extraction_opportunity1, extraction_opportunity2, statements_semantic

    @staticmethod
    def _create_statement_semantic_stub(statements_qty: int) -> Dict[Statement, StatementSemantic]:
        graph = DiGraph()
        return {ASTNode(graph, id): StatementSemantic() for id in range(statements_qty)}

    _settings = ExtractionOpportunityGroupSettings(max_size_difference=0.5, min_overlap=0.5)
