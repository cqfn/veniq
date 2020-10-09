from typing import Dict, List, Optional

from veniq.ast_framework import AST
from .extract_semantic import extract_method_statements_semantic
from ._common_cli import common_cli
from ._common_types import Statement, StatementSemantic, ExtractionOpportunity


def cluster_statements(statements_semantic: Dict[Statement, StatementSemantic]) -> List[ExtractionOpportunity]:
    clusters: List[ExtractionOpportunity] = []
    for step in range(1, len(statements_semantic) + 1):
        for extraction_opportunity in _StatementsClusterIterator(statements_semantic, step):
            if extraction_opportunity not in clusters:
                clusters.append(extraction_opportunity)

    return clusters


class _StatementsClusterIterator:
    def __init__(self, statements_semantic: Dict[Statement, StatementSemantic], step: int):
        self._statements_semantic = statements_semantic
        self._statements = list(statements_semantic.keys())
        self._step = step

        self._statement_index = 0

    def __iter__(self):
        return self

    def __next__(self) -> ExtractionOpportunity:
        if self._statement_index >= len(self._statements_semantic):
            raise StopIteration

        fails_qty = 0
        first_statement_index = self._statement_index
        last_statement_index: Optional[int] = None

        self._statement_index += 1

        while self._statement_index < len(self._statements) and last_statement_index is None:
            previous_statement_semantic = self._get_statement_semantic(self._statement_index - fails_qty - 1)
            current_statement_semantic = self._get_statement_semantic(self._statement_index)

            if current_statement_semantic.is_similar(previous_statement_semantic):
                fails_qty = 0
                self._statement_index += 1
            else:
                fails_qty += 1
                if fails_qty == self._step:
                    self._statement_index -= self._step - 1
                    last_statement_index = self._statement_index - 1
                else:
                    self._statement_index += 1

        # self._statement_index has passed over self._statements
        # put last_statement_index to the last statement before sequence of failures
        if last_statement_index is None:
            last_statement_index = len(self._statements) - fails_qty - 1

        return tuple(self._statements[i] for i in range(first_statement_index, last_statement_index + 1))

    def _get_statement_semantic(self, statement_index: int) -> StatementSemantic:
        current_statement = self._statements[statement_index]
        return self._statements_semantic[current_statement]


def _print_clusters(method_ast: AST, filepath: str, class_name: str, method_name: str):
    statements_semantic = extract_method_statements_semantic(method_ast)
    statement_clusters = cluster_statements(statements_semantic)
    print(
        f"{len(statement_clusters)} clusters found in method {method_name} "
        f"in class {class_name} in file {filepath}:"
    )

    for index, extraction_opportunity in enumerate(statement_clusters):
        first_statement = extraction_opportunity[0]
        last_statement = extraction_opportunity[-1]
        print(
            f"{index}th extraction opportunity:\n"
            f"\tFirst statement: {first_statement.node_type} on line {first_statement.line}\n"
            f"\tLast statement: {last_statement.node_type} on line {last_statement.line}\n"
        )


if __name__ == "__main__":
    common_cli(_print_clusters, "Clusters statements based on their semantic.")
