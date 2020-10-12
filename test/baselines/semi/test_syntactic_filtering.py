from typing import List
from unittest import TestCase

from veniq.baselines.semi._syntactic_filter import syntactic_filter
from .utils import get_method_ast, create_extraction_opportunity


class SyntacticFilteringTestCase(TestCase):
    def test_non_continuos_statements_range(self):
        self._opportunity_test_helper([9, 15], False)

    def test_not_whole_block_selected(self):
        self._opportunity_test_helper([8, 9, 11, 12], False)

    def test_non_continuos_high_level_nodes(self):
        self._opportunity_test_helper([3, 19, 20, 21, 22], False)

    def test_statement_out_of_parent_block(self):
        self._opportunity_test_helper([11, 15], False)

    def test_correct_simple_opportunity(self):
        self._opportunity_test_helper([6, 7, 8, 9, 11, 12, 15], True)

    def test_correct_large_opportunity(self):
        self._opportunity_test_helper([5, 6, 7, 8, 9, 11, 12, 15, 19, 20, 21, 22], True)

    def _opportunity_test_helper(
        self, extraction_opportunity_statements_lines: List[int], is_opportunity_correct: bool
    ):
        method_ast = get_method_ast("SyntacticFilterTest.java", "Test", "testMethod")
        extraction_opportunity, block_statement_graph = create_extraction_opportunity(
            method_ast, extraction_opportunity_statements_lines
        )

        self.assertEqual(
            syntactic_filter(extraction_opportunity, block_statement_graph),
            is_opportunity_correct,
        )
