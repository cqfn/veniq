from typing import Dict, List
from unittest import TestCase

from networkx import DiGraph

from veniq.baselines.semi.extract_semantic import StatementSemantic
from veniq.baselines.semi.cluster_statements import cluster_statements
from veniq.ast_framework import ASTNode


class StatementsClusteringTestCase(TestCase):
    def test_single_cluster(self):
        statements_semantic = self._create_statements_semantic_stub(
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"x"}),
        )

        actual_clusters_indexes = self._get_clusters_nodes_indexes(statements_semantic)
        expected_clusters_indexes = [[0, 1, 2]]
        self.assertEqual(expected_clusters_indexes, actual_clusters_indexes)

    def test_two_cluster(self):
        statements_semantic = self._create_statements_semantic_stub(
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"y"}),
            StatementSemantic(used_objects={"x"}),
        )

        actual_clusters_indexes = self._get_clusters_nodes_indexes(statements_semantic)
        expected_clusters_indexes = [[0], [1], [2], [0, 1, 2]]
        self.assertEqual(expected_clusters_indexes, actual_clusters_indexes)

    def test_similarity(self):
        statements_semantic = self._create_statements_semantic_stub(
            StatementSemantic(used_objects={"x"}),
            StatementSemantic(used_objects={"y"}),
            StatementSemantic(used_methods={"y"}),
        )

        actual_clusters_indexes = self._get_clusters_nodes_indexes(statements_semantic)
        expected_clusters_indexes = [[0], [1], [2]]
        self.assertEqual(expected_clusters_indexes, actual_clusters_indexes)

    @staticmethod
    def _get_clusters_nodes_indexes(statements_semantic: Dict[ASTNode, StatementSemantic]) -> List[List[int]]:
        clusters = cluster_statements(statements_semantic)
        return [[node.node_index for node in cluster] for cluster in clusters]

    @staticmethod
    def _create_statements_semantic_stub(*semantics: StatementSemantic) -> Dict[ASTNode, StatementSemantic]:
        stub_graph = DiGraph()
        return {ASTNode(stub_graph, index): semantic for index, semantic in enumerate(semantics)}
