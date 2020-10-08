from networkx import DiGraph, dfs_labeled_edges, dfs_preorder_nodes  # type: ignore
from typing import Callable, List, Iterator, Optional

from veniq.ast_framework.ast_node_type import ASTNodeType
from veniq.ast_framework.ast_node import ASTNode


TraverseCallback = Callable[[ASTNode], None]


class AST:
    def __init__(self, networkx_tree: DiGraph, root: int):
        self.tree = networkx_tree
        self.root = root

    def __str__(self) -> str:
        printed_graph = ''
        depth = 0
        for _, destination, edge_type in dfs_labeled_edges(self.tree, self.root):
            if edge_type == 'forward':
                printed_graph += '|   ' * depth
                node_type = self.tree.nodes[destination]['node_type']
                printed_graph += str(node_type) + ': '
                if node_type == ASTNodeType.STRING:
                    printed_graph += self.tree.nodes[destination]['string'] + ', '
                printed_graph += f'node index = {destination}'
                node_line = self.tree.nodes[destination]['line']
                if node_line is not None:
                    printed_graph += f', line = {node_line}'
                printed_graph += '\n'
                depth += 1
            elif edge_type == 'reverse':
                depth -= 1
        return printed_graph

    def get_root(self) -> ASTNode:
        return ASTNode(self.tree, self.root)

    def __iter__(self) -> Iterator[ASTNode]:
        for node_index in self.tree.nodes:
            yield ASTNode(self.tree, node_index)

    def get_subtrees(self, *root_type: ASTNodeType) -> Iterator['AST']:
        '''
        Yields subtrees with given type of the root.
        If such subtrees are one including the other, only the larger one is
        going to be in resulted sequence.
        '''
        is_inside_subtree = False
        current_subtree_root = -1  # all node indexes are positive
        subtree: List[int] = []
        for _, destination, edge_type in dfs_labeled_edges(self.tree, self.root):
            if edge_type == 'forward':
                if is_inside_subtree:
                    subtree.append(destination)
                elif self.tree.nodes[destination]['node_type'] in root_type:
                    subtree.append(destination)
                    is_inside_subtree = True
                    current_subtree_root = destination
            elif edge_type == 'reverse' and destination == current_subtree_root:
                is_inside_subtree = False
                yield AST(self.tree.subgraph(subtree), current_subtree_root)
                subtree = []
                current_subtree_root = -1

    def get_subtree(self, node: ASTNode) -> 'AST':
        subtree_nodes_indexes = dfs_preorder_nodes(self.tree, node.node_index)
        subtree = self.tree.subgraph(subtree_nodes_indexes)
        return AST(subtree, node.node_index)

    def traverse(
        self,
        on_node_entering: TraverseCallback,
        on_node_leaving: TraverseCallback = lambda node: None,
        source_node: Optional[ASTNode] = None,
        undirected=False
    ):
        traverse_graph = self.tree.to_undirected(as_view=True) if undirected else self.tree
        if source_node is None:
            source_node = self.get_root()

        for _, destination, edge_type in dfs_labeled_edges(traverse_graph, source_node.node_index):
            if edge_type == "forward":
                on_node_entering(ASTNode(self.tree, destination))
            elif edge_type == "reverse":
                on_node_leaving(ASTNode(self.tree, destination))

    def get_proxy_nodes(self, *types: ASTNodeType) -> Iterator[ASTNode]:
        for node in self.tree.nodes:
            if len(types) == 0 or self.tree.nodes[node]['node_type'] in types:
                yield ASTNode(self.tree, node)
