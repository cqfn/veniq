from pathlib import Path
from unittest import TestCase

from dataset_collection.validation import find_extraction_opportunities, fix_start_end_lines_for_opportunity
from veniq.ast_framework import AST, ASTNodeType
from veniq.utils.ast_builder import build_ast


class TestValidation(TestCase):
    folder = Path(__file__).absolute().parent

    def test_validation_semi_2_closing_brackets(self):
        file = self.folder / "DynaMenuModel.java"
        lines_extracted_by_semi = list(range(91, 107))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual(range(91, 109), fixed_lines)

    def test_semi_no_need_to_find_closing_brackets(self):
        file = self.folder / "User.java"
        lines_extracted_by_semi = list(range(17, 22))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual(range(17, 22), fixed_lines)

    def test_validation_semi_1_closing_brackets(self):
        file = self.folder / "NameNodeRpcServer.java"
        lines_extracted_by_semi = list(range(231, 234))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual(range(231, 235), fixed_lines)

    # def test_1_open_bracket(self):
