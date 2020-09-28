from typing import TYPE_CHECKING, NamedTuple, List
from networkx import DiGraph

from veniq.ast_framework import AST, ASTNode
from ._nodes_factory import NodesFactory
from ._constants import BlockReason, NODE, BLOCK_REASON

if TYPE_CHECKING:
    from .block import Block


class _BlockInfo(NamedTuple):
    reason: BlockReason
    statements: List[ASTNode]


_NodeId = int


def build_block_statement_graph(method_ast: AST) -> "Block":
    graph = DiGraph()
    root_index = _build_graph_from_statement(method_ast.get_root(), graph)
    return NodesFactory.create_block_node(graph, root_index)


def _build_graph_from_statement(statement: ASTNode, graph: DiGraph) -> _NodeId:
    new_statement_index = len(graph)
    new_statement_attributes = {NODE: statement}
    graph.add_node(new_statement_index, **new_statement_attributes)

    blocks = _extract_blocks_from_statement(statement)
    for block in blocks:
        new_block_index = _build_graph_from_block(block, graph)
        graph.add_edge(new_statement_index, new_block_index)

    return new_statement_index


def _build_graph_from_block(block_info: _BlockInfo, graph: DiGraph) -> _NodeId:
    new_block_index = len(graph)
    new_block_attributes = {BLOCK_REASON: block_info.reason}
    graph.add_node(new_block_index, **new_block_attributes)

    for statement in block_info.statements:
        new_statement_index = _build_graph_from_statement(statement, graph)
        graph.add_edge(new_block_index, new_statement_index)

    return new_block_index


def _extract_blocks_from_statement(statement: ASTNode) -> List[_BlockInfo]:
    pass
