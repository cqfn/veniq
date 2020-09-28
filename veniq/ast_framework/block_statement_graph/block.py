from networkx import DiGraph
from typing import Callable, Iterator, Optional, TYPE_CHECKING

from ._constants import BLOCK_REASON, BlockReason, NodeId

if TYPE_CHECKING:
    from .statement import Statement  # noqa: F401


class Block:
    def __init__(self, graph: DiGraph, id: NodeId, statement_factory: Callable[[DiGraph, NodeId], "Statement"]):
        self._graph = graph
        self._id = id
        self._statement_factory = statement_factory

    @property
    def reason(self) -> BlockReason:
        return self._graph.nodes[self._id][BLOCK_REASON]

    @property
    def statements(self) -> Iterator["Statement"]:
        for statement_id in self._graph.successors(self._id):
            yield self._statement_factory(self._graph, statement_id)

    @property
    def origin_statement(self) -> Optional["Statement"]:
        try:
            statement_id = next(self._graph.predecessors(self._id))
            return self._statement_factory(self._graph, statement_id)
        except StopIteration:
            return None
