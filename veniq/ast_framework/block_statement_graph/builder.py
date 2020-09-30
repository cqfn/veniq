from typing import TYPE_CHECKING
from networkx import DiGraph

from veniq.ast_framework import AST
from ._nodes_factory import NodesFactory

if TYPE_CHECKING:
    from .block import Block


def build_block_statement_graph(method_ast: AST) -> "Block":
    graph = DiGraph()
    return NodesFactory.create_block_node(graph, 0)
