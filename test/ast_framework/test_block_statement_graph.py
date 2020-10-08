from typing import List, Union, Dict
from pathlib import Path
from unittest import TestCase

from veniq.ast_framework.block_statement_graph import build_block_statement_graph, Block, Statement
from veniq.ast_framework import ASTNodeType, build_ast


class BlockStatementTestCase(TestCase):
    def test_simple_examples(self):
        filepath = self._current_directory / "BlockStatementGraphExamples.java"
        ast = build_ast(filepath)

        try:
            class_declaration = next(
                node
                for node in ast.get_root().types
                if node.node_type == ASTNodeType.CLASS_DECLARATION and node.name == "BlockStatementGraphExamples"
            )
        except StopIteration:
            raise RuntimeError(f"Can't find class BlockStatementGraphExamples in file {filepath}")

        for method_declaration in class_declaration.methods:
            with self.subTest(
                f"Testing method {method_declaration.name} in class {class_declaration.name} in file {filepath}"
            ):
                block_statement_graph = build_block_statement_graph(ast.get_subtree(method_declaration))
                self.assertEqual(
                    BlockStatementTestCase.flatten_block_statement_graph(block_statement_graph),
                    BlockStatementTestCase._expected_flattened_graphs[method_declaration.name],
                )

    @staticmethod
    def flatten_block_statement_graph(root: Union[Block, Statement]) -> List[str]:
        flattened_graph: List[str] = []

        def on_node_entering(node: Union[Block, Statement]) -> None:
            if isinstance(node, Block):
                flattened_graph.append(str(node.reason))
            elif isinstance(node, Statement):
                flattened_graph.append(str(node.node.node_type))
            else:
                raise ValueError(f"Unknown node {node}")

        root.traverse(on_node_entering)
        return flattened_graph

    _current_directory = Path(__file__).absolute().parent

    _expected_flattened_graphs: Dict[str, List[str]] = {
        "singleAssertStatement": ["Method declaration", "BlockReason.SINGLE_BLOCK", "Assert statement"],
        "singleReturnStatement": ["Method declaration", "BlockReason.SINGLE_BLOCK", "Return statement"],
        "singleStatementExpression": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
        ],
        "singleThrowStatement": ["Method declaration", "BlockReason.SINGLE_BLOCK", "Throw statement"],
        "singleVariableDeclarationStatement": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Local variable declaration",
        ],
        "singleBlockStatement": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Block statement",
            "BlockReason.SINGLE_BLOCK",
            "Return statement",
        ],
        "singleDoStatement": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Do statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
        ],
        "singleForStatement": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "For statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
        ],
        "singleSynchronizeStatement": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Synchronized statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
        ],
        "singleWhileStatement": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "While statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
        ],
        "cycleWithBreak": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "While statement",
            "BlockReason.SINGLE_BLOCK",
            "Break statement",
        ],
        "cycleWithContinue": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "While statement",
            "BlockReason.SINGLE_BLOCK",
            "Continue statement",
        ],
        "singleIfThenBranch": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "If statement",
            "BlockReason.THEN_BRANCH",
            "Statement expression",
        ],
        "singleIfTheElseBranches": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "If statement",
            "BlockReason.THEN_BRANCH",
            "Statement expression",
            "BlockReason.ELSE_BRANCH",
            "Statement expression",
        ],
        "severalElseIfBranches": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "If statement",
            "BlockReason.THEN_BRANCH",
            "Statement expression",
            "BlockReason.THEN_BRANCH",
            "Statement expression",
            "BlockReason.ELSE_BRANCH",
            "Statement expression",
        ],
        "switchBranches": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Switch statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
            "Statement expression",
            "Block statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
            "Statement expression",
            "Statement expression",
        ],
        "singleTryBlock": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Try statement",
            "BlockReason.TRY_BLOCK",
            "Throw statement",
            "BlockReason.CATCH_BLOCK",
            "Statement expression",
        ],
        "fullTryBlock": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Try statement",
            "BlockReason.TRY_RESOURCES",
            "Try resource",
            "BlockReason.TRY_BLOCK",
            "Throw statement",
            "BlockReason.CATCH_BLOCK",
            "Statement expression",
            "BlockReason.CATCH_BLOCK",
            "Statement expression",
            "BlockReason.FINALLY_BLOCK",
            "Statement expression",
        ],
        "complexExample1": [
            "Method declaration",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
            "For statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
            "While statement",
            "BlockReason.SINGLE_BLOCK",
            "Statement expression",
            "Return statement",
        ],
    }
