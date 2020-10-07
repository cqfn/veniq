from typing import Dict, Union, Set

from ._common_types import StatementSemantic, ExtractionOpportunity
from veniq.ast_framework.block_statement_graph import Block, Statement
from veniq.ast_framework import ASTNode, ASTNodeType


def semantic_filter(
    statements: ExtractionOpportunity,
    statements_semantic: Dict[ASTNode, StatementSemantic],
    method_block_statement_graph: Block,
) -> bool:
    symantic_filter_callbacks = _SymanticFilterCallbacks(
        statements, statements_semantic, method_block_statement_graph
    )
    method_block_statement_graph.traverse(symantic_filter_callbacks.on_node_entering)
    return symantic_filter_callbacks.is_statements_extractable


class _SymanticFilterCallbacks:
    def __init__(
        self,
        statements: ExtractionOpportunity,
        statements_semantic: Dict[ASTNode, StatementSemantic],
        method_block_statement_graph: Block,
    ):
        self._statements = statements
        self._statements_semantic = statements_semantic

        self._variables_names_in_statements: Set[str] = set()
        self._is_all_statements_has_been_visited = False

        self._variable_needed_to_return: Set[str] = set()

    @property
    def is_statements_extractable(self):
        return len(self._variable_needed_to_return) <= 1

    def on_node_entering(self, node: Union[Block, Statement]) -> None:
        if isinstance(node, Statement):
            self._on_statement_entering(node)
        elif isinstance(node, Block):
            pass
        else:
            raise ValueError(f"Unknown node type {node}.")

    def _on_statement_entering(self, statement: Statement) -> None:
        if (
            statement.node in self._statements
            and statement.node.node_type == ASTNodeType.LOCAL_VARIABLE_DECLARATION
        ):
            self._variables_names_in_statements.update(statement.node.names)
            if statement.node == self._statements[-1]:
                self._is_all_statements_has_been_visited = True
        elif self._is_all_statements_has_been_visited:
            statement_semantic = self._statements_semantic[statement.node]
            used_based_objects = statement_semantic.used_based_objects
            self._variable_needed_to_return.update(used_based_objects & self._variables_names_in_statements)
