from typing import Dict, Union, Set
from unittest import TestCase

from networkx import DiGraph

from veniq.baselines.semi._common_types import Statement, StatementSemantic
from veniq.baselines.semi.rank_extraction_opportunities import (
    ExtractionOpportunityGroupSettings,
    ExtractionOpportunityGroup,
)
from veniq.ast_framework import ASTNode


class ExtractionOpportunitiesRanking(TestCase):
    def test_primary_metric(self):
        statements_semantic = self._create_statements_semantic("x", "y", "x", "y")
        statements = list(statements_semantic.keys())

        extraction_opportunity1 = tuple(statements[:3])
        extraction_opportunity2 = (statements[0], statements[2])

        extraction_opportunity_group = ExtractionOpportunityGroup(
            extraction_opportunity1, statements_semantic
        )
        self.assertEqual(extraction_opportunity_group.benefit, 1)

        extraction_opportunity_group.add_extraction_opportunity(extraction_opportunity2)
        self.assertEqual(extraction_opportunity_group.benefit, 2)

    def test_secondary_metric(self):
        statements_semantic = self._create_statements_semantic("x", "y", "x", "y")
        statements = list(statements_semantic.keys())

        extraction_opportunity1 = tuple(statements[:3])
        extraction_opportunity2 = (statements[0], statements[2])

        extraction_opportunity_group = ExtractionOpportunityGroup(
            extraction_opportunity1, statements_semantic,
            ExtractionOpportunityGroupSettings(significant_difference_threshold=0.6)
        )
        self.assertEqual(extraction_opportunity_group.benefit, 1)

        extraction_opportunity_group.add_extraction_opportunity(extraction_opportunity2)
        self.assertEqual(extraction_opportunity_group.benefit, 1)

    @staticmethod
    def _create_statements_semantic(
        *used_object_name: Union[str, Set[str]]
    ) -> Dict[Statement, StatementSemantic]:
        graph = DiGraph()
        return {
            ASTNode(graph, id): StatementSemantic(
                used_objects=object_name if isinstance(object_name, set) else {object_name}
            )
            for id, object_name in enumerate(used_object_name)
        }
