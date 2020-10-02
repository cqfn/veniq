from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from veniq.ast_framework import AST, ASTNode
from veniq.baselines.semi.extract_semantic import StatementSemantic, extract_method_statements_semantic
from veniq.baselines.semi.common_cli import common_cli

Cluster = List[ASTNode]


@dataclass
class Range:
    first: int
    last: int


def find_clusters(statements_semantic: Dict[ASTNode, StatementSemantic]) -> List[Cluster]:
    clusters: List[Cluster] = []
    for step in range(1, len(statements_semantic) + 1):
        new_clusters = _find_clusters_with_step(statements_semantic, step)
        clusters.extend([cluster for cluster in new_clusters if cluster not in clusters])

    return clusters


def _find_clusters_with_step(
    statements_semantic: Dict[ASTNode, StatementSemantic], step: int
) -> List[Cluster]:
    fails_qty = 0
    statement_index = 0

    statements_semantic_flat: List[Tuple[ASTNode, StatementSemantic]] = list(statements_semantic.items())

    clusters: List[Cluster] = []
    statements_range: Optional[Range] = None

    while statement_index < len(statements_semantic_flat):
        statement, semantic = statements_semantic_flat[statement_index]
        if statements_range is None:
            statements_range = Range(statement_index, statement_index)
            statement_index += 1
        else:
            previous_statement, previous_semantic = statements_semantic_flat[statements_range.last]
            if previous_semantic.is_similar(semantic):
                statements_range.last = statement_index
                statement_index += 1
                fails_qty = 0
            else:
                fails_qty += 1
                if fails_qty == step:
                    clusters.append(
                        _convert_indexes_to_statements(statements_semantic_flat, statements_range)
                    )
                    statements_range = None
                    statement_index -= step - 1
                    fails_qty = 0
                else:
                    statement_index += 1

    if statements_range is not None:
        clusters.append(_convert_indexes_to_statements(statements_semantic_flat, statements_range))

    return clusters


def _convert_indexes_to_statements(
    statements_semantic_flat: List[Tuple[ASTNode, StatementSemantic]], statements_range: Range
) -> Cluster:
    return [statements_semantic_flat[i][0] for i in range(statements_range.first, statements_range.last + 1)]


def _print_clusters(method_ast: AST, filepath: str, class_name: str, method_name: str):
    statements_semantic = extract_method_statements_semantic(method_ast)
    statement_clusters = find_clusters(statements_semantic)
    print(
        f"{len(statement_clusters)} clusters found in method {method_name} "
        f"in class {class_name} in file {filepath}:"
    )

    for index, cluster in enumerate(statement_clusters):
        first_statement = cluster[0]
        last_statement = cluster[-1]
        print(
            f"{index}th cluster:\n"
            f"\tFirst statement: {first_statement.node_type} on line {first_statement.line}\n"
            f"\tLast statement: {last_statement.node_type} on line {last_statement.line}\n"
        )


if __name__ == "__main__":
    common_cli(_print_clusters, "Clusters statements based on their semantic.")
