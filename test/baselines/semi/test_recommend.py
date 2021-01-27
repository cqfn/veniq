from unittest import TestCase
from tempfile import NamedTemporaryFile
import os

from veniq.utils.ast_builder import build_ast
from veniq.ast_framework import AST
from veniq.baselines.semi.recommend import _add_class_decl_wrap,\
    _convert_ExtractionOpportunity_to_EMO, _get_method_subtree


class TestRecommend(TestCase):
    _method = ["public int method() {",
               "int x = 0;",
               "x = x + 1;",
               "int y = x + 2;",
               "return y;",
               "}"]
    _class = ["class FakeClass {",
              "public int method() {",
              "int x = 0;",
              "x = x + 1;",
              "int y = x + 2;",
              "return y;",
              "}",
              "}"]
    _method_2 = ["public int method() {",
                 "int x = 0;",
                 "if (x == 1) {",
                 "x = x + 1;",
                 "}",
                 "x = x + 1;",
                 "int y = x + 2;",
                 "return y;",
                 "}"]
    _class_2 = ["class FakeClass {",
                "public int method() {",
                "int x = 0;",
                "if (x == 1) {",
                "x = x + 1;",
                "}",
                "x = x + 1;",
                "int y = x + 2;",
                "return y;",
                "} }"]

    def test_add_class_decl_wrap(self):
        class_decl = _add_class_decl_wrap(self._method)
        self.assertEqual(class_decl, self._class)

    def test_get_method_subtree(self):
        with NamedTemporaryFile(delete=False) as f:
            _name = f.name
            f.write('\n'.join(self._class).encode())
        ast = AST.build_from_javalang(build_ast(_name))
        os.unlink(_name)

        nodes = list(ast)
        _method_decl = ast.get_subtree(nodes[4])
        self.assertEqual(str(_method_decl),
                         str(_get_method_subtree(self._class)))

    def test_convert_ExtractionOpportunity_to_EMO_1(self):
        with NamedTemporaryFile(delete=False) as f:
            _name = f.name
            f.write('\n'.join(self._class).encode())

        ast = AST.build_from_javalang(build_ast(_name))
        os.unlink(_name)
        _ast = ast.get_subtree(list(ast)[4])
        extr_opport_nodes = [list(_ast)[18], list(_ast)[10]]

        object_ExtractionOpportunity = tuple(extr_opport_nodes)
        expect_EMO = (2, 3)
        result_EMO = _convert_ExtractionOpportunity_to_EMO(
            object_ExtractionOpportunity, self._class)
        self.assertEqual(expect_EMO, result_EMO)

    def test_convert_ExtractionOpportunity_to_EMO_2(self):
        with NamedTemporaryFile(delete=False) as f:
            _name = f.name
            f.write('\n'.join(self._class_2).encode())

        ast = AST.build_from_javalang(build_ast(_name))
        os.unlink(_name)
        extr_opport_nodes = [list(ast)[18], list(ast)[26]]

        object_ExtractionOpportunity = tuple(extr_opport_nodes)
        expect_EMO = (3, 5)
        result_EMO = _convert_ExtractionOpportunity_to_EMO(
            object_ExtractionOpportunity, self._class_2)
        self.assertEqual(expect_EMO, result_EMO)
