from pathlib import Path
from unittest import TestCase

from veniq.dataset_collection.validation import fix_start_end_lines_for_opportunity, \
    percent_matched


class TestValidation(TestCase):
    folder = Path(__file__).absolute().parent

    def test_validation_semi_2_closing_brackets_with_2_lines_before_block(self):
        file = self.folder / "DynaMenuModel.java"
        # range doesn't include the last item
        # also, add it as it would be numbered starting at 1
        lines_extracted_by_semi = list(range(91, 109))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual((91, 108), fixed_lines)

    def test_validation_semi_2_closing_brackets_without_lines_before_block(self):
        file = self.folder / "BaseTextEditor.java"
        # range doesn't include the last item
        # also, add it as it would be numbered starting at 1
        lines_extracted_by_semi = list(range(58, 62))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual((58, 63), fixed_lines)

    def test_semi_no_need_to_find_closing_brackets(self):
        file = self.folder / "User.java"
        lines_extracted_by_semi = list(range(17, 22))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual((17, 21), fixed_lines)

    def test_validation_semi_closing_brackets_with_2_blocks(self):
        file = self.folder / "CssPreprocessors.java"
        lines_extracted_by_semi = list(range(32, 38))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual((32, 39), fixed_lines)

    def test_validation_semi_1_closing_brackets(self):
        file = self.folder / "NameNodeRpcServer.java"
        lines_extracted_by_semi = list(range(232, 235))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual((232, 235), fixed_lines)

        file = self.folder / "MetadataEncoder.java"
        lines_extracted_by_semi = list(range(51, 55))
        fixed_lines = fix_start_end_lines_for_opportunity(
            lines_extracted_by_semi,
            str(file)
        )
        self.assertEqual((51, 55), fixed_lines)

    def test_get_percent_matched(self):
        semi_lines = list(range(50, 58))
        dataset_lines = list(range(50, 58))
        percent = percent_matched(dataset_lines, semi_lines)
        self.assertEqual(percent, 1.0)

    def test_percent_partially_matched(self):
        semi_lines = list(range(65, 81))
        dataset_lines = list(range(69, 82))
        percent = percent_matched(dataset_lines, semi_lines)
        self.assertEqual(percent, 12 / 13)

    def test_percent_not_matched(self):
        semi_lines = list(range(65, 68))
        dataset_lines = list(range(69, 82))
        percent = percent_matched(dataset_lines, semi_lines)
        self.assertEqual(percent, 0)
