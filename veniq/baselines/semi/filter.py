from typing import List

from ._syntactic_filter import syntactic_filter
from veniq.ast_framework import AST, ASTNode
from veniq.ast_framework.block_statement_graph import build_block_statement_graph


ExtractionOpportunity = List[ASTNode]


def filter_extraction_opportunities(
    extraction_opportunities: List[ExtractionOpportunity], method_ast: AST
) -> List[ExtractionOpportunity]:
    block_statement_graph = build_block_statement_graph(method_ast)
    extraction_opportunities_filtered = filter(
        lambda extraction_opportunity: syntactic_filter(extraction_opportunity, block_statement_graph),
        extraction_opportunities,
    )
    return list(extraction_opportunities_filtered)
