from networkx import DiGraph  # type: ignore
from typing import Callable, Iterator, Optional, TYPE_CHECKING

from ._constants import BLOCK_REASON, BlockReason

if TYPE_CHECKING:
    from .statement import Statement  # noqa: F401


class Block:
    def __init__(self, graph: DiGraph, id: int, statement_factory: Callable[[DiGraph, int], "Statement"]):
        self.graph = graph
        self.id = id
        self.statement_factory = statement_factory

    @property
    def reason(self) -> BlockReason:
        return self.graph.nodes[self.id][BLOCK_REASON]

    @property
    def statements(self) -> Iterator["Statement"]:
        for statement_id in self.graph.successors(self.id):
            yield self.statement_factory(self.graph, statement_id)

    @property
    def origin_statement(self) -> Optional["Statement"]:
        try:
            statement_id = next(self.graph.predecessors(self.id))
            return self.statement_factory(self.graph, statement_id)
        except StopIteration:
            return None
