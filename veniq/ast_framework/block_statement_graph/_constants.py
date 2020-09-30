from enum import Enum

# networkx field names
NODE = "node"
BLOCK_REASON = "block_reason"


class BlockReason(Enum):
    SINGLE_BLOCK = "SINGLE_BLOCK"
    # Thi enum is going to grow soon
