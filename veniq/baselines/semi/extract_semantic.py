from collections import OrderedDict
from typing import Callable, Dict, Union

from veniq.ast_framework import AST, ASTNode, ASTNodeType
from veniq.ast_framework.block_statement_graph import build_block_statement_graph, Block, Statement
from veniq.ast_framework.block_statement_graph.constants import BlockReason
from ._common_cli import common_cli
from ._common_types import Statement as ExtractionStatement, StatementSemantic


def extract_method_statements_semantic(method_ast: AST) -> Dict[ExtractionStatement, StatementSemantic]:
    block_statement_graph = build_block_statement_graph(method_ast)
    semantic_extractor = _SemanticExtractor(method_ast)
    block_statement_graph.traverse(semantic_extractor.on_node_entering, semantic_extractor.on_node_leaving)
    return semantic_extractor.statements_semantic


class _SemanticExtractor:
    def __init__(self, method_ast: AST):
        self.statements_semantic: Dict[ExtractionStatement, StatementSemantic] = OrderedDict()
        self._ast = method_ast

        self._semantic_extractors: Dict[ASTNodeType, Callable[[ExtractionStatement], StatementSemantic]] = {
            ASTNodeType.FOR_STATEMENT: self._extract_semantic_from_field_factory("control"),
            ASTNodeType.DO_STATEMENT: self._extract_semantic_from_field_factory("condition"),
            ASTNodeType.WHILE_STATEMENT: self._extract_semantic_from_field_factory("condition"),
            ASTNodeType.SYNCHRONIZED_STATEMENT: self._extract_semantic_from_field_factory("lock"),
            ASTNodeType.SWITCH_STATEMENT: self._extract_semantic_from_field_factory("expression"),
            # plain statements
            ASTNodeType.ASSERT_STATEMENT: self._extract_semantic_from_ast,
            ASTNodeType.RETURN_STATEMENT: self._extract_semantic_from_ast,
            ASTNodeType.STATEMENT_EXPRESSION: self._extract_semantic_from_ast,
            ASTNodeType.THROW_STATEMENT: self._extract_semantic_from_ast,
            ASTNodeType.TRY_RESOURCE: self._extract_semantic_from_ast,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION: self._extract_semantic_from_ast,
            # Single keyword statement has no semantic
            ASTNodeType.BREAK_STATEMENT: lambda _: StatementSemantic(),
            ASTNodeType.CONTINUE_STATEMENT: lambda _: StatementSemantic(),
            # Inner class declarations are currently not supported
            ASTNodeType.CLASS_DECLARATION: lambda _: StatementSemantic(),
        }

    def on_node_entering(self, node: Union[Block, Statement]) -> None:
        if isinstance(node, Block):
            self._on_block_entering(node)
        elif isinstance(node, Statement):
            self._on_statement_entering(node)
        else:
            raise ValueError(f"Unexpected node type {type(node)}.")

    def on_node_leaving(self, node: Union[Block, Statement]) -> None:
        if isinstance(node, Block):
            self._on_block_leaving(node)
        elif isinstance(node, Statement):
            pass
        else:
            raise ValueError(f"Unexpected node type {type(node)}.")

    def _on_statement_entering(self, statement: Statement) -> None:
        extraction_statement: ExtractionStatement = statement.node

        # Statements that does not bring any semantic are skiped
        # "If" statements is handled separately in _on_block_entering due to "else if" construction
        if extraction_statement.node_type in {
            ASTNodeType.METHOD_DECLARATION,
            ASTNodeType.BLOCK_STATEMENT,
            ASTNodeType.TRY_STATEMENT,
            ASTNodeType.IF_STATEMENT,
        }:
            return

        try:
            semantic_extractor = self._semantic_extractors[extraction_statement.node_type]
        except KeyError:
            raise ValueError(f"Unexpected statement type {extraction_statement.node_type}.")

        self.statements_semantic[extraction_statement] = semantic_extractor(extraction_statement)

    def _on_block_entering(self, block: Block) -> None:
        statement = block.origin_statement
        assert statement is not None
        if block.reason == BlockReason.THEN_BRANCH:
            self.statements_semantic[statement] = self._extract_semantic_from_ast(statement.condition)
        elif block.reason == BlockReason.ELSE_BRANCH:
            parent_if_statement = self._get_parent_if_statement(statement)
            self.statements_semantic[self._ast.create_fake_node()] = self._extract_semantic_from_ast(
                parent_if_statement.condition
            )
        elif block.reason in {
            BlockReason.TRY_BLOCK,
            BlockReason.TRY_RESOURCES,
        }:
            self.statements_semantic[self._ast.create_fake_node()] = StatementSemantic()
        elif statement.node_type in {
            ASTNodeType.BLOCK_STATEMENT,
        }:
            self.statements_semantic[statement] = StatementSemantic()

    def _on_block_leaving(self, block: Block) -> None:
        statement = block.origin_statement
        assert statement is not None
        if (
            statement.node_type
            in {
                ASTNodeType.BLOCK_STATEMENT,
                ASTNodeType.DO_STATEMENT,
                ASTNodeType.FOR_STATEMENT,
                ASTNodeType.SYNCHRONIZED_STATEMENT,
                ASTNodeType.WHILE_STATEMENT,
                ASTNodeType.SWITCH_STATEMENT,
            }
            or block.reason
            in {
                BlockReason.TRY_BLOCK,
                BlockReason.TRY_RESOURCES,
                BlockReason.CATCH_BLOCK,
                BlockReason.FINALLY_BLOCK,
                BlockReason.ELSE_BRANCH,
            }
            or (statement.node_type == ASTNodeType.IF_STATEMENT and statement.else_statement is None)
        ):
            self.statements_semantic[self._ast.create_fake_node()] = StatementSemantic()

    def _extract_semantic_from_ast(self, ast_root: ASTNode) -> StatementSemantic:
        statement_semantic = StatementSemantic()
        for node in self._ast.get_subtree(ast_root).get_proxy_nodes(
            ASTNodeType.MEMBER_REFERENCE, ASTNodeType.METHOD_INVOCATION, ASTNodeType.VARIABLE_DECLARATOR
        ):
            if node.node_type == ASTNodeType.MEMBER_REFERENCE:
                used_object_name = node.member
                if node.qualifier is not None:
                    used_object_name = node.qualifier + "." + used_object_name
                statement_semantic.used_objects.add(used_object_name)
            elif node.node_type == ASTNodeType.METHOD_INVOCATION:
                statement_semantic.used_methods.add(node.member)
                if node.qualifier is not None:
                    statement_semantic.used_objects.add(node.qualifier)
            elif node.node_type == ASTNodeType.VARIABLE_DECLARATOR:
                statement_semantic.used_objects.add(node.name)

        return statement_semantic

    def _extract_semantic_from_field_factory(self, field_name) -> Callable[[ASTNode], StatementSemantic]:
        return lambda node: self._extract_semantic_from_ast(getattr(node, field_name))

    @staticmethod
    def _get_parent_if_statement(node: ASTNode) -> ASTNode:
        while node.node_type != ASTNodeType.IF_STATEMENT and node.parent is not None:
            node = node.parent

        if node.node_type == ASTNodeType.IF_STATEMENT:
            return node

        raise RuntimeError(f"There is no If statement above given node {node}.")


def _print_semantic(method_ast: AST, filepath: str, class_name: str, method_name: str) -> None:
    print(f"{method_name} method in {class_name} class \nin file {filepath}:")
    method_semantic = extract_method_statements_semantic(method_ast)
    for statement, semantic in method_semantic.items():
        print(f"\t{statement.node_type} on line {statement.line} uses:")

        if len(semantic.used_objects) != 0:
            print("\t\tObjects:")
            for object_name in semantic.used_objects:
                print("\t\t\t- " + object_name)

        if len(semantic.used_methods) != 0:
            print("\t\tMethods:")
            for method_name in semantic.used_methods:
                print("\t\t\t- " + method_name)


if __name__ == "__main__":
    common_cli(_print_semantic, "Extracts semantic from methods.")
