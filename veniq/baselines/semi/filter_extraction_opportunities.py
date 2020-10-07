from typing import Dict, List

from .extract_semantic import extract_method_statements_semantic
from .create_extraction_opportunities import create_extraction_opportunities
from ._syntactic_filter import syntactic_filter
from ._semantic_filter import semantic_filter
from ._common_types import Statement, StatementSemantic, ExtractionOpportunity
from ._common_cli import common_cli
from veniq.ast_framework import AST
from veniq.ast_framework.block_statement_graph import build_block_statement_graph


def filter_extraction_opportunities(
    extraction_opportunities: List[ExtractionOpportunity],
    statements_semantic: Dict[Statement, StatementSemantic],
    method_ast: AST,
) -> List[ExtractionOpportunity]:
    block_statement_graph = build_block_statement_graph(method_ast)
    extraction_opportunities_filtered = filter(
        lambda extraction_opportunity: syntactic_filter(extraction_opportunity, block_statement_graph)
        and semantic_filter(extraction_opportunity, statements_semantic, block_statement_graph),
        extraction_opportunities,
    )
    return list(extraction_opportunities_filtered)


def _print_extraction_opportunities(method_ast: AST, filepath: str, class_name: str, method_name: str):
    statements_semantic = extract_method_statements_semantic(method_ast)
    extraction_opportunities = create_extraction_opportunities(statements_semantic)
    filtered_extraction_opportunities = filter_extraction_opportunities(
        extraction_opportunities, statements_semantic, method_ast
    )
    print(
        f"{len(filtered_extraction_opportunities)} opportunities found in method {method_name} "
        f"in class {class_name} in file {filepath}:"
    )

    for index, extraction_opportunity in enumerate(filtered_extraction_opportunities):
        first_statement = extraction_opportunity[0]
        last_statement = extraction_opportunity[-1]
        print(
            f"{index}th extraction opportunity:\n"
            f"\tFirst statement: {first_statement.node_type} on line {first_statement.line}\n"
            f"\tLast statement: {last_statement.node_type} on line {last_statement.line}\n"
        )


if __name__ == "__main__":
    common_cli(
        _print_extraction_opportunities,
        "Creates extraction opportunities and filter them based on syntactic and semantic conditions",
    )
