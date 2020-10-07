from typing import Dict, Union, Set
from unittest import TestCase

from networkx import DiGraph

from veniq.baselines.semi._common_types import Statement, StatementSemantic
from veniq.baselines.semi._lcom2 import LCOM2

from veniq.ast_framework import ASTNode


class LCOM2TestCase(TestCase):
    def test_same_semantic(self):
        statements_semantic = self._create_statements_semantic("x", "x", "x", "x")
        self.assertEqual(LCOM2(statements_semantic), 0)

    def test_different_semantic(self):
        statements_semantic = self._create_statements_semantic("x", "y", "z", "a")
        self.assertEqual(LCOM2(statements_semantic), 6)

    def test_equal_pairs_quantity(self):
        statements_semantic = self._create_statements_semantic("x", {"x", "y"}, {"x", "z"}, {"x", "a"})
        self.assertEqual(LCOM2(statements_semantic), 0)

    @staticmethod
    def _create_statements_semantic(
        *used_object_name: Union[str, Set[str]]
    ) -> Dict[Statement, StatementSemantic]:
        graph = DiGraph()
        return {
            ASTNode(graph, id): StatementSemantic(
                used_objects=object_name if isinstance(object_name, set) else {object_name}
            )
            for id, object_name in enumerate(used_object_name)
        }
