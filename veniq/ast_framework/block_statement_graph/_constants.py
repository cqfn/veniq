from enum import Enum

NodeId = int

# networkx field names
NODE = "node"
BLOCK_REASON = "block_reason"


class NodeType(Enum):
    Statement = "Statement"
    Block = "Block"


class BlockReason(Enum):
    SINGLE_BLOCK = "SINGLE_BLOCK"
    # This enum is going to grow soon
