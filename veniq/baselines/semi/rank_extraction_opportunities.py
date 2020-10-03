from typing import List, Dict, Tuple, Iterator, NamedTuple

from ._lcom2 import LCOM2
from ._common_types import Statement, StatementSemantic, ExtractionOpportunity, OpportunityBenifit


class ExtractionOpportunityGroupSettings(NamedTuple):
    max_size_difference: float = 0.2
    min_overlap: float = 0.1
    significant_difference_treshold: float = 0.01


class ExtractionOpportunityGroup:
    def __init__(
        self,
        extraction_opportunity: ExtractionOpportunity,
        statements_semantic: Dict[Statement, StatementSemantic],
        settings: ExtractionOpportunityGroupSettings = ExtractionOpportunityGroupSettings(),
    ):
        self._optimal_opportunity = extraction_opportunity
        self._statements_semantic = statements_semantic
        self._all_statements_benifit = LCOM2(statements_semantic)

        self._opportunities_to_benifit: Dict[ExtractionOpportunity, OpportunityBenifit] = {
            extraction_opportunity: self._calculate_benifit(extraction_opportunity)
        }

        self._settings = settings

    def is_allowed_to_add_opportunity(self, extraction_opportunity: ExtractionOpportunity) -> bool:
        return not self._is_similar_size(self._optimal_opportunity, extraction_opportunity) and \
            self._is_significantly_overlapping(self._optimal_opportunity, extraction_opportunity)

    def add_extraction_opportunity(self, extraction_opportunity: ExtractionOpportunity) -> None:
        new_opportunity_benifit = self._calculate_benifit(extraction_opportunity)
        self._opportunities_to_benifit[extraction_opportunity] = new_opportunity_benifit

        benifit_difference = abs(new_opportunity_benifit - self.benifit)
        max_benifit = max(new_opportunity_benifit, self.benifit)
        is_new_opportunity_optimal: bool
        if benifit_difference / max_benifit >= self._settings.significant_difference_treshold:
            is_new_opportunity_optimal = new_opportunity_benifit > self.benifit
        else:
            is_new_opportunity_optimal = len(extraction_opportunity) > len(self._optimal_opportunity)

        if is_new_opportunity_optimal:
            self._optimal_opportunity = extraction_opportunity

    @property
    def benifit(self) -> OpportunityBenifit:
        return self._opportunities_to_benifit[self._optimal_opportunity]

    @property
    def opportunities(self) -> Iterator[Tuple[ExtractionOpportunity, OpportunityBenifit]]:
        for opportunity, benifit in self._opportunities_to_benifit.items():
            yield opportunity, benifit

    def _is_similar_size(
        self, extraction_opportunity1: ExtractionOpportunity, extraction_opportunity2: ExtractionOpportunity
    ) -> bool:
        extraction_opportunity_size1 = len(extraction_opportunity1)
        extraction_opportunity_size2 = len(extraction_opportunity2)
        size_difference = abs(extraction_opportunity_size1 - extraction_opportunity_size2)
        min_size = min(extraction_opportunity_size1, extraction_opportunity_size2)
        return size_difference / min_size < self._settings.max_size_difference

    def _is_significantly_overlapping(
        self, extraction_opportunity1: ExtractionOpportunity, extraction_opportunity2: ExtractionOpportunity
    ) -> bool:
        shared_statements_qty = len(set(extraction_opportunity1) & set(extraction_opportunity2))
        max_size = max(len(extraction_opportunity1), len(extraction_opportunity2))
        return shared_statements_qty / max_size > self._settings.min_overlap

    def _calculate_benifit(self, extraction_opportunity: ExtractionOpportunity) -> OpportunityBenifit:
        opportunity_semantic = {
            statement: self._statements_semantic[statement] for statement in extraction_opportunity
        }
        opportunity_benifit = LCOM2(opportunity_semantic)

        rest_statements_semantic = {
            statement: self._statements_semantic[statement]
            for statement in self._statements_semantic
            if statement not in extraction_opportunity
        }
        rest_statements_benifit = LCOM2(rest_statements_semantic)

        return self._all_statements_benifit - max(opportunity_benifit, rest_statements_benifit)


def rank_extraction_opportunities(
    statements_semantic: Dict[Statement, StatementSemantic],
    extraction_opportunities: List[ExtractionOpportunity],
) -> List[ExtractionOpportunityGroup]:
    extraction_opportunities_groups: List[ExtractionOpportunityGroup] = []
    while len(extraction_opportunities) > 0:
        new_extraction_opportunity_group = _create_extraction_opportunities_group(
            statements_semantic, extraction_opportunities
        )
        extraction_opportunities_groups.append(new_extraction_opportunity_group)

        used_opportunities = {
            opportunity for opportunity, _ in new_extraction_opportunity_group.opportunities
        }
        extraction_opportunities = [
            opportunity for opportunity in extraction_opportunities if opportunity not in used_opportunities
        ]

    return sorted(
        extraction_opportunities_groups,
        key=lambda extraction_opportunity_group: extraction_opportunity_group.benifit,
    )


def _create_extraction_opportunities_group(
    statements_semantic: Dict[Statement, StatementSemantic],
    extraction_opportunities: List[ExtractionOpportunity],
) -> ExtractionOpportunityGroup:
    assert len(extraction_opportunities) > 0, "Cannot create a group from empty list of opportunities."

    extraction_opportunity_group = ExtractionOpportunityGroup(
        extraction_opportunities[0], statements_semantic
    )
    for extraction_opportunity in extraction_opportunities[1:]:
        if extraction_opportunity_group.is_allowed_to_add_opportunity(extraction_opportunity):
            extraction_opportunity_group.add_extraction_opportunity(extraction_opportunity)

    return extraction_opportunity_group
