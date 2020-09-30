from enum import Enum

from networkx import DiGraph

NodeId = int

# networkx field names
NODE = "node"
BLOCK_REASON = "block_reason"


class NodeType(Enum):
    Statement = "Statement"
    Block = "Block"

    @staticmethod
    def detect(graph: DiGraph, node_id: NodeId) -> "NodeType":
        node_attributes = graph.nodes(data=True)[node_id]
        if NODE in node_attributes:
            return NodeType.Statement
        elif BLOCK_REASON in node_attributes:
            return NodeType.Block
        else:
            raise ValueError(f"Cannot identify node with attributes {node_attributes}")


class BlockReason(Enum):
    SINGLE_BLOCK = "SINGLE_BLOCK"
    # This enum is going to grow soon
