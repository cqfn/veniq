from typing import Any, Dict, Set, List, Tuple, Union, cast
from pathlib import Path

from networkx import DiGraph

from javalang.tree import Node
from javalang.parse import parse

from veniq.utils.encoding_detector import read_text_with_autodetected_encoding

from .ast import AST
from .ast_node_type import ASTNodeType
from ._auxiliary_data import javalang_to_ast_node_type, attributes_by_node_type, ASTNodeReference


def build_ast(filepath: Union[str, Path]) -> AST:
    tree = DiGraph()
    javalang_node_to_index_map: Dict[Node, int] = {}
    javalang_ast = parse(read_text_with_autodetected_encoding(filepath))

    root = _add_subtree_from_javalang_node(tree, javalang_ast, javalang_node_to_index_map)
    _replace_javalang_nodes_in_attributes(tree, javalang_node_to_index_map)

    return AST(tree, root)


_UNKNOWN_NODE_TYPE = -1


def _add_subtree_from_javalang_node(
    tree: DiGraph, javalang_node: Union[Node, Set[str], str], javalang_node_to_index_map: Dict[Node, int]
) -> int:
    node_index, node_type = _add_javalang_node(tree, javalang_node)
    if node_index != _UNKNOWN_NODE_TYPE and node_type not in {ASTNodeType.COLLECTION, ASTNodeType.STRING}:
        javalang_standard_node = cast(Node, javalang_node)
        javalang_node_to_index_map[javalang_standard_node] = node_index
        _add_javalang_children(tree, javalang_standard_node.children, node_index, javalang_node_to_index_map)
    return node_index


# NOTICE: We use here List[Any] because mypy does not support recursive type,
#         while children may have quite large depth of nested lists.
def _add_javalang_children(
    tree: DiGraph, children: List[Any], parent_index: int, javalang_node_to_index_map: Dict[Node, int]
) -> None:
    for child in children:
        if isinstance(child, list):
            _add_javalang_children(tree, child, parent_index, javalang_node_to_index_map)
        else:
            child_index = _add_subtree_from_javalang_node(tree, child, javalang_node_to_index_map)
            if child_index != _UNKNOWN_NODE_TYPE:
                tree.add_edge(parent_index, child_index)


def _add_javalang_node(tree: DiGraph, javalang_node: Union[Node, Set[str], str]) -> Tuple[int, ASTNodeType]:
    node_index = _UNKNOWN_NODE_TYPE
    node_type = ASTNodeType.UNKNOWN
    if isinstance(javalang_node, Node):
        node_index, node_type = _add_javalang_standard_node(tree, javalang_node)
    elif isinstance(javalang_node, set):
        node_index = _add_javalang_collection_node(tree, javalang_node)
        node_type = ASTNodeType.COLLECTION
    elif isinstance(javalang_node, str):
        node_index = _add_javalang_string_node(tree, javalang_node)
        node_type = ASTNodeType.STRING

    return node_index, node_type


def _add_javalang_standard_node(tree: DiGraph, javalang_node: Node) -> Tuple[int, ASTNodeType]:
    node_index = len(tree) + 1
    node_type = javalang_to_ast_node_type[type(javalang_node)]

    attr_names = attributes_by_node_type[node_type]
    attributes = {attr_name: getattr(javalang_node, attr_name) for attr_name in attr_names}

    attributes["node_type"] = node_type
    attributes["line"] = javalang_node.position.line if javalang_node.position is not None else None

    _post_process_javalang_attributes(tree, node_type, attributes)

    tree.add_node(node_index, **attributes)
    return node_index, node_type


def _post_process_javalang_attributes(
    tree: DiGraph, node_type: ASTNodeType, attributes: Dict[str, Any]
) -> None:
    """
    Replace some attributes with more appropriate values for convenient work
    """

    if node_type == ASTNodeType.METHOD_DECLARATION and attributes["body"] is None:
        attributes["body"] = []

    if node_type == ASTNodeType.LAMBDA_EXPRESSION and isinstance(attributes["body"], Node):
        attributes["body"] = [attributes["body"]]

    if (
        node_type in {ASTNodeType.METHOD_INVOCATION, ASTNodeType.MEMBER_REFERENCE}
        and attributes["qualifier"] == ""
    ):
        attributes["qualifier"] = None


def _add_javalang_collection_node(tree: DiGraph, collection_node: Set[str]) -> int:
    node_index = len(tree) + 1
    tree.add_node(node_index, node_type=ASTNodeType.COLLECTION, line=None)

    for item in collection_node:
        string_node_index = _add_javalang_string_node(tree, item)
        tree.add_edge(node_index, string_node_index)

    return node_index


def _add_javalang_string_node(tree: DiGraph, string_node: str) -> int:
    node_index = len(tree) + 1
    tree.add_node(node_index, node_type=ASTNodeType.STRING, string=string_node, line=None)
    return node_index


def _replace_javalang_nodes_in_attributes(tree: DiGraph, javalang_node_to_index_map: Dict[Node, int]) -> None:
    """
    All javalang nodes found in networkx nodes attributes are replaced
    with references to according networkx nodes.
    Supported attributes types:
        - just javalang Node
        - list of javalang Nodes and other such lists (with any depth)
    """
    for node, attributes in tree.nodes.items():
        for attribute_name in attributes:
            attribute_value = attributes[attribute_name]
            if isinstance(attribute_value, Node):
                node_reference = _create_reference_to_node(attribute_value, javalang_node_to_index_map)
                tree.add_node(node, **{attribute_name: node_reference})
            elif isinstance(attribute_value, list):
                node_references = _replace_javalang_nodes_in_list(attribute_value, javalang_node_to_index_map)
                tree.add_node(node, **{attribute_name: node_references})


# NOTICE: We use here List[Any] because mypy does not support recursive type,
#         while javalang_nodes_list may have quite large depth of nested lists.
def _replace_javalang_nodes_in_list(
    javalang_nodes_list: List[Any], javalang_node_to_index_map: Dict[Node, int]
) -> List[Any]:
    """
    javalang_nodes_list: list of javalang Nodes or other such lists (with any depth)
    All javalang nodes are replaces with according references
    """
    node_references_list: List[Any] = []
    for item in javalang_nodes_list:
        if isinstance(item, Node):
            node_references_list.append(_create_reference_to_node(item, javalang_node_to_index_map))
        elif isinstance(item, list):
            node_references_list.append(_replace_javalang_nodes_in_list(item, javalang_node_to_index_map))
        elif isinstance(item, (int, str)) or item is None:
            node_references_list.append(item)
        else:
            raise RuntimeError(
                'Cannot parse "Javalang" attribute:\n'
                f"{item}\n"
                "Expected: Node, list of Nodes, integer or string"
            )

    return node_references_list


def _create_reference_to_node(
    javalang_node: Node, javalang_node_to_index_map: Dict[Node, int]
) -> ASTNodeReference:
    return ASTNodeReference(javalang_node_to_index_map[javalang_node])
