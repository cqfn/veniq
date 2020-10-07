from typing import List
from unittest import TestCase

from veniq.baselines.semi._semantic_filter import semantic_filter
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from .utils import get_method_ast, create_extraction_opportunity


class SemanticFilterTestCase(TestCase):
    def test_no_local_variables_method(self):
        self._opportunity_test_helper("noLocalVariablesMethod", [3, 4, 5], True)

    def test_local_unused_variables_method(self):
        self._opportunity_test_helper("localUnusedVariables", [11, 12], True)

    def test_local_used_variables_method(self):
        self._opportunity_test_helper("localUsedVariable", [17, 18], True)

    def test_two_used_variables_variables_method(self):
        self._opportunity_test_helper("twoUsedVariables", [23], False)

    def _opportunity_test_helper(
        self,
        method_name: str,
        extraction_opportunity_statements_lines: List[int],
        is_opportunity_correct: bool,
    ):
        method_ast = get_method_ast("SemanticFilterTest.java", "Test", method_name)
        statements_semantic = extract_method_statements_semantic(method_ast)
        extraction_opportunity, block_statement_graph = create_extraction_opportunity(
            method_ast, extraction_opportunity_statements_lines
        )

        self.assertEqual(
            semantic_filter(extraction_opportunity, statements_semantic, block_statement_graph),
            is_opportunity_correct,
        )
