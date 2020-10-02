from itertools import zip_longest
from pathlib import Path
from unittest import TestCase

from veniq.ast_framework import AST, ASTNodeType
from veniq.utils.ast_builder import build_ast
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic, StatementSemantic


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

    ]
