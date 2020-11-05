from itertools import islice
from pathlib import Path
from typing import List, Tuple, Union

from veniq.ast_framework import AST, ASTNodeType
from veniq.ast_framework.block_statement_graph import Block, Statement, build_block_statement_graph
from veniq.baselines.semi._common_types import (
    ExtractionOpportunity,
    Statement as ExtractionStatement,
    StatementSemantic,
)
from veniq.utils.ast_builder import build_ast


def objects_semantic(*objects_names: str) -> StatementSemantic:
    return StatementSemantic(used_objects=set(objects_names))


def create_extraction_opportunity(
    method_ast: AST, statements_lines: List[int]
) -> Tuple[ExtractionOpportunity, Block]:
    extraction_opportunity_list: List[ExtractionStatement] = []
    block_statement_graph = build_block_statement_graph(method_ast)

    def fill_extraction_opportunity(node: Union[Block, Statement]):
        nonlocal extraction_opportunity_list
        if isinstance(node, Statement) and node.node.line in statements_lines:
            extraction_opportunity_list.append(node.node)

    block_statement_graph.traverse(fill_extraction_opportunity)
    return tuple(extraction_opportunity_list), block_statement_graph


def get_class_ast(filename: str, class_name: str) -> Tuple[AST, Path]:
    current_directory = Path(__file__).absolute().parent
    filepath = current_directory / filename
    ast = AST.build_from_javalang(build_ast(str(filepath)))

    try:
        class_declaration = next(
            node
            for node in ast.get_root().types
            if node.node_type == ASTNodeType.CLASS_DECLARATION and node.name == class_name
        )
    except StopIteration:
        raise RuntimeError(f"Failed to find class {class_name} in file {filepath}")

    return ast.get_subtree(class_declaration), filepath


def get_method_ast(filename: str, class_name: str, method_name: str) -> AST:
    class_ast, filepath = get_class_ast(filename, class_name)

    try:
        method_declaration = next(node for node in class_ast.get_root().methods if node.name == method_name)
    except StopIteration:
        raise RuntimeError(f"Failed to find method {method_name} in class {class_name} in file {filepath}")

    return class_ast.get_subtree(method_declaration)


def get_constructor_ast(filename: str, class_name: str, constructor_index: int) -> AST:
    class_ast, filepath = get_class_ast(filename, class_name)

    try:
        constructor_declaration = next(islice(class_ast.get_root().constructors, constructor_index - 1, None))
    except StopIteration:
        raise RuntimeError(
            f"Failed to find {constructor_index}th constructor in class {class_name} in file {filepath}"
        )

    return class_ast.get_subtree(constructor_declaration)
