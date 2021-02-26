from unittest import TestCase
from tempfile import NamedTemporaryFile
import os

from javalang.parser import JavaSyntaxError

from veniq.utils.ast_builder import build_ast
from veniq.ast_framework import AST
from veniq.baselines.semi.recommend import _add_class_decl_wrap,\
    _convert_ExtractionOpportunity_to_EMO, _get_method_subtree,\
    recommend_for_method
from test.baselines.semi.utils import create_extraction_opportunity


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
                 "x = x + 1; }",
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
    _class_2_close_bracket = ["class FakeClass {",
                              "public int method() {",
                              "int x = 0;",
                              "if (x == 1) {",
                              "x = x + 1; }",
                              "x = x + 1;",
                              "int y = x + 2;",
                              "return y; } }"]

    def _get_method_ast(self, class_decl):
        with NamedTemporaryFile(delete=False) as f:
            _name = f.name
            f.write('\n'.join(class_decl).encode())
        ast = AST.build_from_javalang(build_ast(_name))
        os.unlink(_name)

        nodes = list(ast)
        _method_decl = ast.get_subtree(nodes[4])
        return _method_decl

    def test_add_class_decl_wrap(self):
        class_decl = _add_class_decl_wrap(self._method)
        self.assertEqual(class_decl, self._class)

    def test_get_method_subtree(self):
        _method_decl = self._get_method_ast(self._class)
        self.assertEqual(str(_method_decl),
                         str(_get_method_subtree(self._class)))

    def test_convert_ExtractionOpportunity_to_EMO_1(self):
        _ast = self._get_method_ast(self._class)
        object_ExtractionOpportunity, _ = create_extraction_opportunity(_ast,
                                                                        [3, 4])
        expect_EMO = (2, 3)
        result_EMO = _convert_ExtractionOpportunity_to_EMO(
            object_ExtractionOpportunity, self._class)
        self.assertEqual(expect_EMO, result_EMO)

    def test_convert_ExtractionOpportunity_to_EMO_2(self):
        _ast = self._get_method_ast(self._class_2)
        object_ExtractionOpportunity, _ = create_extraction_opportunity(
            _ast, [4, 5, 6])
        expect_EMO = (3, 5)
        result_EMO = _convert_ExtractionOpportunity_to_EMO(
            object_ExtractionOpportunity, self._class_2)
        self.assertEqual(expect_EMO, result_EMO)

    def test_EMO_no_open_bracket(self):
        _ast = self._get_method_ast(self._class_2_close_bracket)
        object_ExtractionOpportunity, _ = create_extraction_opportunity(_ast,
                                                                        [5])
        expect_EMO = (4, 4)
        result_EMO = _convert_ExtractionOpportunity_to_EMO(
            object_ExtractionOpportunity, self._class_2_close_bracket)
        self.assertEqual(expect_EMO, result_EMO)

    def test_EMO_no_open_bracket_2(self):
        """
        Case where ExtractionOpportunity is Local Variable Decl
        and return statement:
        "int y = x + 2;",
        "return y; } }"
        Should return just these two lines.
        """
        _ast = self._get_method_ast(self._class_2_close_bracket)
        object_ExtractionOpportunity, _ = create_extraction_opportunity(_ast,
                                                                        [7, 8])
        expect_EMO = (6, 7)
        result_EMO = _convert_ExtractionOpportunity_to_EMO(
            object_ExtractionOpportunity, self._class_2_close_bracket)
        self.assertEqual(expect_EMO, result_EMO)

    def test_recommend_for_method(self):
        result_emos = recommend_for_method('\n'.join(self._method))
        all_possible_emos = {(1, 4)}
        self.assertEqual(set(result_emos), all_possible_emos, str(result_emos))

    def test_javasyntaxerror(self):
        """
        Invalid java syntax
        """
        with self.assertRaises(JavaSyntaxError):
            recommend_for_method('\n'.join(self._method[1:]))

        with self.assertRaises(JavaSyntaxError):
            recommend_for_method('\n'.join(self._method[:-1]))
