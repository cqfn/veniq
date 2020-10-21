from typing import Dict, Union, Set, List

from ._common_types import StatementSemantic, ExtractionOpportunity, Statement as ExtractionStatement
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
    method_block_statement_graph.traverse(
        symantic_filter_callbacks.on_node_entering, symantic_filter_callbacks.on_node_leaving
    )
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

        # If control breaking statement among statements, then its coresponding
        # cycle must be also among statements, otherwise statements are not extractable
        self._cycles_stack: List[ExtractionStatement] = []
        self._is_control_flow_breaking_statement_out_of_cycle = False

    @property
    def is_statements_extractable(self):
        return (
            not self._is_control_flow_breaking_statement_out_of_cycle
            and len(self._variable_needed_to_return) <= 1
        )

    def on_node_entering(self, node: Union[Block, Statement]) -> None:
        if isinstance(node, Statement):
            self._on_statement_entering(node)
        elif isinstance(node, Block):
            pass
        else:
            raise ValueError(f"Unknown node type {node}.")

    def on_node_leaving(self, node: Union[Block, Statement]) -> None:
        if isinstance(node, Statement):
            self._on_statement_leaving(node)
        elif isinstance(node, Block):
            pass
        else:
            raise ValueError(f"Unknown node type {node}.")

    def _on_statement_entering(self, statement: Statement) -> None:
        if statement.node in self._statements:
            if statement.node == self._statements[-1]:
                self._is_all_statements_has_been_visited = True

            if statement.node.node_type == ASTNodeType.LOCAL_VARIABLE_DECLARATION:
                self._variables_names_in_statements.update(statement.node.names)
            elif statement.node.node_type in _SymanticFilterCallbacks._cycles_statements:
                self._cycles_stack.append(statement.node)
            elif (
                len(self._cycles_stack) == 0
                and statement.node.node_type in _SymanticFilterCallbacks._control_flow_breaking_statements
            ):
                self._is_control_flow_breaking_statement_out_of_cycle = True

        elif self._is_all_statements_has_been_visited and statement.node in self._statements_semantic:
            statement_semantic = self._statements_semantic[statement.node]
            used_based_objects = statement_semantic.used_based_objects
            self._variable_needed_to_return.update(used_based_objects & self._variables_names_in_statements)

    def _on_statement_leaving(self, statement: Statement) -> None:
        if len(self._cycles_stack) > 0 and statement.node == self._cycles_stack[-1]:
            self._cycles_stack.pop()

    # following statements are closely tight with control flow and cannot be extracted easily
    _control_flow_breaking_statements = {ASTNodeType.BREAK_STATEMENT, ASTNodeType.CONTINUE_STATEMENT}

    # only cycles may have _control_flow_breaking_statements in subtrees
    _cycles_statements = {
        ASTNodeType.DO_STATEMENT,
        ASTNodeType.FOR_STATEMENT,
        ASTNodeType.WHILE_STATEMENT,
    }
