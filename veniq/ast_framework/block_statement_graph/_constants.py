from enum import Enum, auto


class NodeType(Enum):
    Statement = auto()
    Block = auto()


# networkx field names
NODE = "node"
BLOCK_REASON = "block_reason"


class BlockReason(Enum):
    SINGLE_BLOCK = "SINGLE_BLOCK"
    # This enum is going to grow soon
