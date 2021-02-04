from typing import List, Dict, Tuple, Iterator, NamedTuple

from veniq.ast_framework import AST
from .extract_semantic import extract_method_statements_semantic
from .create_extraction_opportunities import create_extraction_opportunities
from .filter_extraction_opportunities import filter_extraction_opportunities
from ._common_types import Statement, StatementSemantic, ExtractionOpportunity, OpportunityBenefit
from ._common_cli import common_cli
from ._lcom2 import LCOM2


class ExtractionOpportunityGroupSettings(NamedTuple):
    max_size_difference: float = 0.2
    min_overlap: float = 0.1
    significant_difference_threshold: float = 0.01


class ExtractionOpportunityGroup:
    def __init__(
        self,
        extraction_opportunity: ExtractionOpportunity,
        statements_semantic: Dict[Statement, StatementSemantic],
        settings: ExtractionOpportunityGroupSettings = ExtractionOpportunityGroupSettings(),
    ):
        self._optimal_opportunity = extraction_opportunity
        self._statements_semantic = statements_semantic
        self._all_statements_benefit = LCOM2(statements_semantic)

        self._opportunities_to_benefit: Dict[ExtractionOpportunity, OpportunityBenefit] = {
            extraction_opportunity: self._calculate_benefit(extraction_opportunity)
        }

        self._settings = settings

    def is_allowed_to_add_opportunity(self, extraction_opportunity: ExtractionOpportunity) -> bool:
        return self._is_similar_size(
            self._optimal_opportunity, extraction_opportunity
        ) and self._is_significantly_overlapping(self._optimal_opportunity, extraction_opportunity)

    def add_extraction_opportunity(self, extraction_opportunity: ExtractionOpportunity) -> None:
        new_opportunity_benefit = self._calculate_benefit(extraction_opportunity)
        self._opportunities_to_benefit[extraction_opportunity] = new_opportunity_benefit

        benefit_difference = abs(new_opportunity_benefit - self.benefit)
        max_benefit = max(new_opportunity_benefit, self.benefit)
        is_new_opportunity_optimal: bool
        if (
            max_benefit > 0
            and benefit_difference / max_benefit >= self._settings.significant_difference_threshold
        ):
            is_new_opportunity_optimal = new_opportunity_benefit > self.benefit
        else:
            is_new_opportunity_optimal = len(extraction_opportunity) > len(self._optimal_opportunity)

        if is_new_opportunity_optimal:
            self._optimal_opportunity = extraction_opportunity

    @property
    def benefit(self) -> OpportunityBenefit:
        return self._opportunities_to_benefit[self._optimal_opportunity]

    @property
    def opportunities(self) -> Iterator[Tuple[ExtractionOpportunity, OpportunityBenefit]]:
        for opportunity, benefit in self._opportunities_to_benefit.items():
            yield opportunity, benefit

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

    def _calculate_benefit(self, extraction_opportunity: ExtractionOpportunity) -> OpportunityBenefit:
        opportunity_semantic = {
            statement: self._statements_semantic[statement] for statement in extraction_opportunity
        }
        opportunity_benefit = LCOM2(opportunity_semantic)

        rest_statements_semantic = {
            statement: self._statements_semantic[statement]
            for statement in self._statements_semantic
            if statement not in extraction_opportunity
        }
        rest_statements_benefit = LCOM2(rest_statements_semantic)

        return self._all_statements_benefit - max(opportunity_benefit, rest_statements_benefit)


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
        key=lambda extraction_opportunity_group: extraction_opportunity_group.benefit,
        reverse=True,
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


def _print_extraction_opportunities(
    method_ast: AST, filepath: str, class_name: str, method_name: str
) -> None:
    statements_semantic = extract_method_statements_semantic(method_ast)
    extraction_opportunities = create_extraction_opportunities(statements_semantic)
    filtered_extraction_opportunities = filter_extraction_opportunities(
        extraction_opportunities, statements_semantic, method_ast
    )
    extraction_opportunities_groups = rank_extraction_opportunities(
        statements_semantic, filtered_extraction_opportunities
    )

    print(
        f"Extraction opportunities groups of method {method_name} in class {class_name} in file {filepath}:"
    )

    for extraction_opportunity_group in extraction_opportunities_groups:
        print(f"\tExtraction opportunities group with scope {extraction_opportunity_group.benefit}:")
        for extraction_opportunity, benefit in extraction_opportunity_group.opportunities:
            print(f"\t\tExtraction opportunity with score {benefit}:")
            for statement in extraction_opportunity:
                print(f"\t\t\t{statement.node_type} on line {statement.line}")


if __name__ == "__main__":
    common_cli(_print_extraction_opportunities, "Find extraction opportunities and rank them.")
