from typing import Callable, Dict, List, NamedTuple, Union

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


def _extract_blocks_from_single_block_statement_factory(
    field_name: str,
) -> Callable[[ASTNode], List[BlockInfo]]:
    def extract_blocks_from_single_block_statement(statement: ASTNode) -> List[BlockInfo]:
        return [
            BlockInfo(
                reason=BlockReason.SINGLE_BLOCK,
                statements=_unwrap_block_to_statements_list(getattr(statement, field_name)),
            )
        ]

    return extract_blocks_from_single_block_statement


def _unwrap_block_to_statements_list(
    block_statement_or_statement_list: Union[ASTNode, List[ASTNode]]
) -> List[ASTNode]:
    if isinstance(block_statement_or_statement_list, ASTNode):
        assert block_statement_or_statement_list.node_type == ASTNodeType.BLOCK_STATEMENT
        return block_statement_or_statement_list.statements

    return block_statement_or_statement_list


_block_extractors: Dict[ASTNodeType, Callable[[ASTNode], List[BlockInfo]]] = {
    # plain statements
    ASTNodeType.ASSERT_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.BREAK_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.CONTINUE_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.RETURN_STATEMENT: _extract_blocks_from_plain_statement,
    ASTNodeType.STATEMENT_EXPRESSION: _extract_blocks_from_plain_statement,
    ASTNodeType.THROW_STATEMENT: _extract_blocks_from_plain_statement,
    # single block statements
    ASTNodeType.BLOCK_STATEMENT: _extract_blocks_from_single_block_statement_factory("body"),
    ASTNodeType.DO_STATEMENT: _extract_blocks_from_single_block_statement_factory("statements"),
    ASTNodeType.FOR_STATEMENT: _extract_blocks_from_single_block_statement_factory("body"),
    ASTNodeType.METHOD_DECLARATION: _extract_blocks_from_single_block_statement_factory("body"),
    ASTNodeType.SYNCHRONIZED_STATEMENT: _extract_blocks_from_single_block_statement_factory("block"),
    ASTNodeType.WHILE_STATEMENT: _extract_blocks_from_single_block_statement_factory("body"),
}
