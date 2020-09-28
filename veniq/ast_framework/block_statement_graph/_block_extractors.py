from typing import Callable, Dict, List, NamedTuple

from veniq.ast_framework import ASTNode, ASTNodeType
from ._constants import BlockReason


class BlockInfo(NamedTuple):
    reason: BlockReason
    statements: List[ASTNode]


def extract_blocks_from_statement(statement: ASTNode) -> List[BlockInfo]:
    try:
        return _block_extractors[statement.node_type](statement)
    except KeyError:
        raise NotImplementedError(f"Node {statement.node_type} is not supported.")


_block_extractors: Dict[ASTNodeType, Callable[[ASTNode], List[BlockInfo]]] = {

}
