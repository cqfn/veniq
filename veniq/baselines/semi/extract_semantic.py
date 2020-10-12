from collections import OrderedDict
from typing import Dict

from veniq.ast_framework import AST, ASTNode, ASTNodeType
from ._common_cli import common_cli
from ._common_types import Statement, StatementSemantic


def extract_method_statements_semantic(method_ast: AST) -> Dict[Statement, StatementSemantic]:
    statement_semantic: Dict[Statement, StatementSemantic] = OrderedDict()
    for statement in method_ast.get_root().body:
        statement_semantic.update(_extract_statement_semantic(statement, method_ast))

    return statement_semantic


def _extract_statement_semantic(statement: ASTNode, method_ast: AST) -> Dict[Statement, StatementSemantic]:
    if statement.node_type == ASTNodeType.BLOCK_STATEMENT:
        return _extract_block_semantic(statement, method_ast)
    elif statement.node_type == ASTNodeType.FOR_STATEMENT:
        return _extract_for_cycle_semantic(statement, method_ast)
    elif statement.node_type in {ASTNodeType.DO_STATEMENT, ASTNodeType.WHILE_STATEMENT}:
        return _extract_while_cycle_semantic(statement, method_ast)
    elif statement.node_type == ASTNodeType.IF_STATEMENT:
        return _extract_if_branching_sematic(statement, method_ast)
    elif statement.node_type == ASTNodeType.SYNCHRONIZED_STATEMENT:
        return _extract_synchronized_block_semantic(statement, method_ast)
    elif statement.node_type == ASTNodeType.SWITCH_STATEMENT:
        return _extract_switch_branching_semantic(statement, method_ast)
    elif statement.node_type == ASTNodeType.TRY_STATEMENT:
        return _extract_try_block_semantic(statement, method_ast)
    elif statement.node_type in {
        ASTNodeType.ASSERT_STATEMENT,
        ASTNodeType.RETURN_STATEMENT,
        ASTNodeType.STATEMENT_EXPRESSION,
        ASTNodeType.THROW_STATEMENT,
        ASTNodeType.LOCAL_VARIABLE_DECLARATION,
    }:
        return _extract_plain_statement_semantic(statement, method_ast)
    elif statement.node_type in {
        ASTNodeType.BREAK_STATEMENT,  # Single keyword statement has no semantic
        ASTNodeType.CONTINUE_STATEMENT,  # Single keyword statement has no semantic
        ASTNodeType.CLASS_DECLARATION,  # Inner class declarations are currently not supported
    }:
        return OrderedDict([(statement, StatementSemantic())])

    raise NotImplementedError(f"Extracting semantic from {statement.node_type} is not supported")


def _extract_for_cycle_semantic(statement: ASTNode, method_ast: AST) -> Dict[Statement, StatementSemantic]:
    control_subtree = method_ast.get_subtree(statement.control)
    statements_semantic: Dict[Statement, StatementSemantic] = OrderedDict(
        [(statement, _extract_semantic_from_ast(control_subtree))]
    )

    statements_semantic.update(_extract_statement_semantic(statement.body, method_ast))

    return statements_semantic


def _extract_block_semantic(statement: ASTNode, method_ast: AST) -> Dict[Statement, StatementSemantic]:
    statements_semantic: Dict[Statement, StatementSemantic] = OrderedDict()
    for node in statement.statements:
        statements_semantic.update(_extract_statement_semantic(node, method_ast))

    return statements_semantic


def _extract_while_cycle_semantic(statement: ASTNode, method_ast: AST) -> Dict[Statement, StatementSemantic]:
    condition_subtree = method_ast.get_subtree(statement.condition)
    statements_semantic: Dict[Statement, StatementSemantic] = OrderedDict(
        [(statement, _extract_semantic_from_ast(condition_subtree))]
    )

    statements_semantic.update(_extract_statement_semantic(statement.body, method_ast))

    return statements_semantic


def _extract_if_branching_sematic(statement: ASTNode, method_ast: AST) -> Dict[Statement, StatementSemantic]:
    condition_subtree = method_ast.get_subtree(statement.condition)
    statements_semantic: Dict[Statement, StatementSemantic] = OrderedDict(
        [(statement, _extract_semantic_from_ast(condition_subtree))]
    )

    statements_semantic.update(_extract_statement_semantic(statement.then_statement, method_ast))

    if statement.else_statement is not None:
        statements_semantic.update(_extract_statement_semantic(statement.else_statement, method_ast))

    return statements_semantic


def _extract_synchronized_block_semantic(
    statement: ASTNode, method_ast: AST
) -> Dict[Statement, StatementSemantic]:
    lock_subtree = method_ast.get_subtree(statement.lock)
    statements_semantic: Dict[Statement, StatementSemantic] = OrderedDict(
        [(statement, _extract_semantic_from_ast(lock_subtree))]
    )

    for inner_statement in statement.block:
        statements_semantic.update(_extract_statement_semantic(inner_statement, method_ast))
    return statements_semantic


def _extract_switch_branching_semantic(
    statement: ASTNode, method_ast: AST
) -> Dict[Statement, StatementSemantic]:
    expression_subtree = method_ast.get_subtree(statement.expression)
    statements_semantic: Dict[Statement, StatementSemantic] = OrderedDict(
        [(statement, _extract_semantic_from_ast(expression_subtree))]
    )

    for case in statement.cases:
        for inner_statement in case.statements:
            statements_semantic.update(_extract_statement_semantic(inner_statement, method_ast))

    return statements_semantic


def _extract_try_block_semantic(statement: ASTNode, method_ast: AST) -> Dict[Statement, StatementSemantic]:
    statements_semantic: Dict[Statement, StatementSemantic] = OrderedDict()

    for resource in statement.resources or []:
        resource_ast = method_ast.get_subtree(resource)
        statements_semantic[resource] = _extract_semantic_from_ast(resource_ast)

    for node in statement.block:
        statements_semantic.update(_extract_statement_semantic(node, method_ast))

    for catch_clause in statement.catches or []:
        for inner_statement in catch_clause.block:
            statements_semantic.update(_extract_statement_semantic(inner_statement, method_ast))

    for node in statement.finally_block or []:
        statements_semantic.update(_extract_statement_semantic(node, method_ast))

    return statements_semantic


def _extract_plain_statement_semantic(
    statement: ASTNode, method_ast: AST
) -> Dict[Statement, StatementSemantic]:
    statement_ast = method_ast.get_subtree(statement)
    return OrderedDict([(statement, _extract_semantic_from_ast(statement_ast))])


def _extract_semantic_from_ast(statement_ast: AST) -> StatementSemantic:
    statement_semantic = StatementSemantic()
    for node in statement_ast.get_proxy_nodes(
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
