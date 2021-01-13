from collections import defaultdict
from typing import Dict, List, Optional, NamedTuple

from veniq.ast_framework import AST
from .extract_semantic import extract_method_statements_semantic
from ._common_cli import common_cli
from ._common_types import Statement, StatementSemantic, ExtractionOpportunity


def create_extraction_opportunities(
    statements_semantic: Dict[Statement, StatementSemantic]
) -> List[ExtractionOpportunity]:
    statements = list(statements_semantic.keys())
    semantics = list(statements_semantic.values())

    statements_similarity_provider = _StatementsSimilarityProvider(semantics)
    statements_ranges = _StatementsRanges(statements)

    extraction_opportunities = statements_ranges.create_initial_ranges(statements_similarity_provider)

    similarity_gaps = statements_similarity_provider.get_similarity_gaps()
    for gap in sorted(similarity_gaps.keys()):
        # Create a separate list for new extraction opportunities
        # created during merge of statements ranges with **fixed** similarity gap
        # due to the possible overwrites of those new extraction opportunities
        new_extraction_opportunities: List[ExtractionOpportunity] = []
        for statement_index in similarity_gaps[gap]:
            new_opportunity = statements_ranges.merge_ranges(statement_index, statement_index + gap)

            # If, for a fixed similarity gap, a new extraction opportunity starts with the same statements
            # as previous one, this means, that the last range of first similarity gap is the first range
            # of next similarity gap, i.e. those gaps are overlapping, and in the final result the both
            # must be in same extraction opportunity. Notice that the resulting opportunity of second merge
            # is simply extending the previous one, so we can take it insted of previous opportunity.
            if new_extraction_opportunities and new_extraction_opportunities[-1][0] == new_opportunity[0]:
                new_extraction_opportunities[-1] = new_opportunity
            else:
                new_extraction_opportunities.append(new_opportunity)
        extraction_opportunities.extend(new_extraction_opportunities)

    extraction_opportunities = [
        tuple(filter(lambda node: not node.is_fake, extraction_opportunity))
        for extraction_opportunity in extraction_opportunities
        if any(not node.is_fake for node in extraction_opportunity)
    ]

    return extraction_opportunities


class _StatementsSimilarityProvider:
    def __init__(self, statements_semantic: List[StatementSemantic]):
        self._steps_to_next_similar: List[Optional[int]] = [
            self._calculate_steps_to_next_similar(statements_semantic, statement_index)
            for statement_index in range(len(statements_semantic))
        ]

    def has_next_similar_statement(self, statement_index: int) -> bool:
        return self._steps_to_next_similar[statement_index] is not None

    def get_steps_to_next_similar_statement(self, statement_index: int) -> int:
        step = self._steps_to_next_similar[statement_index]
        if step is None:
            raise ValueError(f"All statements after {statement_index}th are not similar to it.")

        return step

    def get_similarity_gaps(self) -> Dict[int, List[int]]:
        """
        Finds all statements, that next similar statement is not following them directly.
        Returns dict with steps as keys and list of coresponding statement indexes as values.
        Fo example, if next similar statement to 1st is 3rd, to 2nd is 4th and for 5th is 8th,
        then the output will be: {2: [1, 2], 3: [5]}.
        NOTICE: all statement indexes lists are sorted.
        """
        similarity_gaps_by_size: Dict[int, List[int]] = defaultdict(list)
        for statement_index, step in enumerate(self._steps_to_next_similar):
            if step and step > 1:
                similarity_gaps_by_size[step].append(statement_index)

        return similarity_gaps_by_size

    @staticmethod
    def _calculate_steps_to_next_similar(
        statements_semantic: List[StatementSemantic], statement_index: int
    ) -> Optional[int]:
        step = 1
        current_statement = statements_semantic[statement_index]
        while statement_index + step < len(statements_semantic):
            if current_statement.is_similar(statements_semantic[statement_index + step]):
                return step
            step += 1

        return None


class _StatementsRanges:
    """
    Represents a division of a sequence of statements by non overlapping sorted ranges.
    """

    class _Range(NamedTuple):
        begin: int
        end: int  # ! NOTICE: Index past the last element in a range.

    def __init__(self, statements: List[Statement]):
        self._statements = statements
        self._ranges: List[_StatementsRanges._Range] = []

    def create_initial_ranges(
        self, statements_similarity: _StatementsSimilarityProvider
    ) -> List[ExtractionOpportunity]:
        """
        A initial statements range is a continuos range of statements, where each statement,
        except the first one, is similar to previous.
        """

        extraction_opportunities: List[ExtractionOpportunity] = []

        range_begin = 0
        range_end = 1  # ! NOTICE: Index past the last element in a range.

        for index, statement in enumerate(self._statements):
            if (
                statements_similarity.has_next_similar_statement(index)
                and statements_similarity.get_steps_to_next_similar_statement(index) == 1
            ):
                range_end += 1
            else:
                self._ranges.append(self._Range(range_begin, range_end))
                extraction_opportunities.append(tuple(self._statements[range_begin:range_end]))
                range_begin = range_end
                range_end += 1

        if range_begin < len(self._statements):
            self._ranges.append(self._Range(range_begin, len(self._statements)))
            extraction_opportunities.append(tuple(self._statements[range_begin:]))

        return extraction_opportunities

    def merge_ranges(
        self, first_range_statement_index: int, last_range_statement_index
    ) -> ExtractionOpportunity:
        """
        Identifies first and last ranges by given statements indexes and
        merge them two and all other ranges between them.
        Returns statements from newly created range.
        """
        first_range_index = self._get_range_index(first_range_statement_index)
        last_range_index = self._get_range_index(last_range_statement_index)

        first_range = self._ranges[first_range_index]
        last_range = self._ranges[last_range_index]

        new_range = self._Range(first_range.begin, last_range.end)
        self._ranges[first_range_index:last_range_index + 1] = [new_range]

        return tuple(self._statements[new_range.begin:new_range.end])

    def _get_range_index(self, statement_index: int) -> int:
        if not self._ranges:
            raise ValueError("No ranges was created.")

        smallest_index_in_ranges = self._ranges[0].begin
        if statement_index < smallest_index_in_ranges:
            raise ValueError(
                f"Element is before all the ranges. Element index = {statement_index}, "
                f"smallest index among elements in ranges = {smallest_index_in_ranges}."
            )

        for range_index, range in enumerate(self._ranges):
            if statement_index < range.end:
                return range_index

        largets_index_in_ranges = self._ranges[-1].end - 1
        raise ValueError(
            f"Element is past all the ranges. Element index = {statement_index}, "
            f"greatest index among elements in ranges = {largets_index_in_ranges}."
        )


def _print_extraction_opportunities(method_ast: AST, filepath: str, class_name: str, method_name: str):
    statements_semantic = extract_method_statements_semantic(method_ast)
    extraction_opportunities = create_extraction_opportunities(statements_semantic)
    print(
        f"{len(extraction_opportunities)} opportunities found in method {method_name} "
        f"in class {class_name} in file {filepath}:"
    )

    for index, extraction_opportunity in enumerate(extraction_opportunities):
        first_statement = extraction_opportunity[0]
        last_statement = extraction_opportunity[-1]
        print(
            f"{index}th extraction opportunity:\n"
            f"\tFirst statement: {first_statement.node_type} on line {first_statement.line}\n"
            f"\tLast statement: {last_statement.node_type} on line {last_statement.line}\n"
        )


if __name__ == "__main__":
    common_cli(
        _print_extraction_opportunities, "Creates extraction opportunities based on statements semantic."
    )
