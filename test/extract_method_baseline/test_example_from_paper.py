from itertools import zip_longest
from pathlib import Path
from unittest import TestCase

from veniq.ast_framework import AST, ASTNodeType
from veniq.utils.ast_builder import build_ast
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic, StatementSemantic
from veniq.baselines.semi.cluster_statements import cluster_statements


def objects_semantic(*objects_names: str) -> StatementSemantic:
    return StatementSemantic(used_objects=set(objects_names))


class PaperExampleTestCase(TestCase):
    def test_semantic_extraction(self):
        semantic = extract_method_statements_semantic(self.method_ast)
        for comparison_index, (statement, actual_semantic, expected_semantic) in enumerate(
            zip_longest(semantic.keys(), semantic.values(), self.method_semantic)
        ):
            self.assertEqual(
                actual_semantic,
                expected_semantic,
                f"Failed on {statement.node_type} statement on line {statement.line}. "
                f"Comparison index is {comparison_index}.",
            )

    def test_statements_clustering(self):
        self.maxDiff = None
        semantic = extract_method_statements_semantic(self.method_ast)
        clusters = cluster_statements(semantic)

        for cluster_index, (actual_cluster, expected_cluster) in enumerate(
            zip_longest(clusters, self.expected_clusters)
        ):
            actual_cluster_statement_types = [statement.node_type for statement in actual_cluster]
            self.assertEqual(
                actual_cluster_statement_types,
                expected_cluster,
                f"Failed on {cluster_index}th cluster comparison",
            )

    @classmethod
    def setUpClass(cls):
        current_directory = Path(__file__).absolute().parent
        filepath = current_directory / "ExampleFromPaper.java"

        ast = AST.build_from_javalang(build_ast(filepath))
        try:
            class_declaration = next(
                node
                for node in ast.get_root().types
                if node.node_type == ASTNodeType.CLASS_DECLARATION and node.name == "ExampleFromPaper"
            )

            method_declaration = next(
                node for node in class_declaration.methods if node.name == "grabManifests"
            )
        except StopIteration as e:
            raise RuntimeError(
                f"Failed to find method grabManifests in class ExampleFromPaper in file {filepath}."
            ) from e

        cls.method_ast = ast.get_subtree(method_declaration)

    method_semantic = [
        objects_semantic("rcs", "manifests", "length"),  # line 7
        objects_semantic("i", "length", "rcs"),  # line 8
        objects_semantic("rec"),  # line 9
        objects_semantic("i", "rcs"),  # line 10
        StatementSemantic(used_objects={"rec", "rcs", "i"}, used_methods={"grabRes"}),  # line 11
        StatementSemantic(used_objects={"rec", "rcs", "i"}, used_methods={"grabNonFileSetRes"}),  # line 13
        objects_semantic("rec", "j", "length"),  # line 15
        StatementSemantic(used_objects={"name", "rec", "j"}, used_methods={"getName", "replace"}),  # line 16
        objects_semantic("rcs", "i"),  # line 17
        objects_semantic("afs", "rcs", "i"),  # line 18
        StatementSemantic(used_objects={"afs"}, used_methods={"equals", "getFullpath", "getProj"}),  # line 19
        StatementSemantic(used_objects={"name", "afs"}, used_methods={"getFullpath", "getProj"}),  # line 20
        StatementSemantic(used_objects={"afs"}, used_methods={"equals", "getPref", "getProj"}),  # line 21
        StatementSemantic(used_objects={"afs", "pr"}, used_methods={"getPref", "getProj"}),  # line 22
        StatementSemantic(used_objects={"pr"}, used_methods={"endsWith"}),  # line 23
        objects_semantic("pr"),  # line 24
        objects_semantic("pr", "name"),  # line 26
        StatementSemantic(
            used_objects={"name", "MANIFEST_NAME"}, used_methods={"equalsIgnoreCase"}
        ),  # line 29
        objects_semantic("manifests", "i", "rec", "j"),  # line 30
        StatementSemantic(),  # line 31
        objects_semantic("manifests", "i"),  # line 34
        objects_semantic("manifests", "i"),  # line 35
        objects_semantic("manifests"),  # line 38
    ]

    expected_clusters = [
        [ASTNodeType.LOCAL_VARIABLE_DECLARATION, ASTNodeType.FOR_STATEMENT],  # lines 7-8
        [ASTNodeType.LOCAL_VARIABLE_DECLARATION],  # line 9
        [
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.FOR_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
        ],  # lines 10-16
        [
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.IF_STATEMENT,
        ],  # lines 17-29
        [ASTNodeType.STATEMENT_EXPRESSION],  # line 30
        [ASTNodeType.BREAK_STATEMENT],  # line 31
        [
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.RETURN_STATEMENT,
        ],  # lines 34-38
        [
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.FOR_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.FOR_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
        ],  # lines 7-16
        [
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.BREAK_STATEMENT,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.RETURN_STATEMENT,
        ],  # lines 30-38
        [
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.FOR_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.FOR_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.LOCAL_VARIABLE_DECLARATION,
            ASTNodeType.IF_STATEMENT,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.STATEMENT_EXPRESSION,
            ASTNodeType.IF_STATEMENT,
        ],  # lines 7-29
    ]
