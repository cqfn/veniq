from networkx import DiGraph
from typing import Callable, Iterator, TYPE_CHECKING

from veniq.ast_framework import ASTNode
from ._constants import NODE, NodeId

if TYPE_CHECKING:
    from .block import Block


class Statement:
    def __init__(self, graph: DiGraph, id: NodeId, block_factory: Callable[[DiGraph, NodeId], "Block"]):
        self.graph = graph
        self.id = id
        self.block_factory = block_factory

    @property
    def node(self) -> ASTNode:
        return self.graph.nodes[self.id][NODE]

    @property
    def has_nested_blocks(self) -> bool:
        return self.graph.out_degree(self.id) > 0

    @property
    def nested_blocks(self) -> Iterator["Block"]:
        for block_id in self.graph.successors(self.id):
            yield self.block_factory(self.graph, block_id)

    @property
    def parent_block(self) -> "Block":
        block_id = next(self.graph.predecessors(self.id))
        return self.block_factory(self.graph, block_id)
