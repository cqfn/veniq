from veniq.ast_framework import AST
from ...extract_semantic import extract_method_statements_semantic
from .create_all_opportunities import create_extraction_opportunities
from ...filter_extraction_opportunities import filter_extraction_opportunities
from ...rank_extraction_opportunities import rank_extraction_opportunities
from ..._common_cli import common_cli


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
        print(f"\tExtraction opportunities group with scope {extraction_opportunity_group.benifit}:")
        for extraction_opportunity, benifit in extraction_opportunity_group.opportunities:
            print(f"\t\tExtraction opportunity with score {benifit}:")
            for statement in extraction_opportunity:
                print(f"\t\t\t{statement.node_type} on line {statement.line}")


if __name__ == "__main__":
    common_cli(_print_extraction_opportunities, "Find extraction opportunities and rank them.")
