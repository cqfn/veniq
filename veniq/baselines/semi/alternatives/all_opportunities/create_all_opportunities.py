from typing import Dict, List

from veniq.ast_framework import AST
from ...extract_semantic import extract_method_statements_semantic
from ..._common_cli import common_cli
from ..._common_types import Statement, StatementSemantic, ExtractionOpportunity


def create_extraction_opportunities(
    statements_semantic: Dict[Statement, StatementSemantic]
) -> List[ExtractionOpportunity]:
    statements = list(statements_semantic.keys())
    extraction_opportunities: List[ExtractionOpportunity] = []
    for first in range(len(statements)):
        for last in range(first, len(statements)):
            extraction_opportunities.append(tuple(statements[first: last + 1]))
    return extraction_opportunities


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