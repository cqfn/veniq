from typing import Callable, Union
from networkx import DiGraph, dfs_labeled_edges

from .statement import Statement
from .block import Block
from ._constants import NodeType, NodeId

TraverseCallback = Callable[[Union[Block, Statement]], None]


class NodesFactory:
    @staticmethod
    def create_statement_node(graph: DiGraph, id: NodeId) -> Statement:
        return Statement(graph, id, NodesFactory.create_block_node)

    @staticmethod
    def create_block_node(graph: DiGraph, id: NodeId) -> Block:
        return Block(graph, id, NodesFactory.create_statement_node)

    @staticmethod
    def _detect_and_create_node(graph: DiGraph, id: NodeId) -> Union[Block, Statement]:
        node_type = NodeType.detect(graph, id)
        if node_type == NodeType.Block:
            return NodesFactory.create_block_node(graph, id)
        elif node_type == NodeType.Statement:
            return NodesFactory.create_statement_node(graph, id)
        else:
            raise ValueError(f"Unexpected node type {node_type}.")

    @staticmethod
    def _traverse_graph(
        graph: DiGraph,
        start_node_id: NodeId,
        on_node_entering: TraverseCallback,
        on_node_leaving: TraverseCallback = lambda _: None,
    ) -> None:
        for _, destination_id, edge_type in dfs_labeled_edges(graph, start_node_id):
            destination_node = NodesFactory._detect_and_create_node(graph, destination_id)
            if edge_type == "forward":
                on_node_entering(destination_node)
            elif edge_type == "reverse":
                on_node_leaving(destination_node)
            else:
                raise RuntimeError(f"Unexpected edge type {edge_type}.")
