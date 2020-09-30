from networkx import DiGraph

from .statement import Statement
from .block import Block


class NodesFactory:
    @staticmethod
    def create_statement_node(graph: DiGraph, id: int) -> Statement:
        return Statement(graph, id, NodesFactory.create_block_node)

    @staticmethod
    def create_block_node(graph: DiGraph, id: int) -> Block:
        return Block(graph, id, NodesFactory.create_statement_node)
