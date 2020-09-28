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


def _extract_blocks_from_plain_statement(statement: ASTNode) -> List[BlockInfo]:
    return []


_block_extractors: Dict[ASTNodeType, Callable[[ASTNode], List[BlockInfo]]] = {
    ASTNodeType.ASSERT_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.BREAK_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.CONTINUE_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.RETURN_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.STATEMENT_EXPRESSION: _extract_blocks_from_plain_statement,
    ASTNodeType.THROW_STATEMENT: _extract_blocks_from_plain_statement,
}
