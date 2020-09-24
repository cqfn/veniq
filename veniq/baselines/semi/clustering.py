from collections import Counter
from typing import List, Union, Dict
from collections import OrderedDict

from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.ast_framework import ASTNode, AST
from veniq.baselines.semi.common_cli import common_cli


def _check_is_common(
    dict_file: Dict,
    statement_1: Union[int, ASTNode],
    statement_2: Union[int, ASTNode]
) -> bool:
    joined_names: Counter = Counter(dict_file[statement_1] + dict_file[statement_2])
    duplicates = {element: count for element, count in joined_names.items() if count > 1}.keys()
    return len(list(duplicates)) >= 1


def _is_in_range(elem: int, values: List[int]) -> bool:
    return elem >= values[0] and elem <= values[1]


def _process_statement(
    dict_file: Dict,
    list_statements: List[Union[int, ASTNode]],
    step: int
) -> List[List[int]]:
    clusters: List[List[int]] = []
    for stat_1 in list_statements:
        stat_1_line = stat_1 if isinstance(stat_1, int) else stat_1.line
        for stat_2 in list_statements[:stat_1_line + step]:
            stat_2_line = stat_2 if isinstance(stat_2, int) else stat_2.line
            if stat_1_line < stat_2_line and _check_is_common(dict_file, stat_1, stat_2):
                if len(clusters) != 0 and _is_in_range(stat_1_line, clusters[-1]):
                    if not _is_in_range(stat_2_line, clusters[-1]):
                        clusters[-1][1] = stat_2_line
                else:
                    clusters.append([stat_1_line, stat_2_line])
    return clusters


def SEMI(dict_file: Dict[ASTNode, List[str]]) -> List[List[int]]:
    opportunities = []
    statements = list(dict_file.keys())

    first_statement_ = list(dict_file.keys())[0]
    last_statement_ = list(dict_file.keys())[-1]
    first_statement = first_statement_ if isinstance(first_statement_, int) else first_statement_.line
    last_statement = last_statement_ if isinstance(last_statement_, int) else last_statement_.line
    method_length = last_statement - first_statement

    for step in range(1, method_length + 1):
        clusters = _process_statement(dict_file, statements, step)
        opportunities += clusters
    unique_oppo = [list(oppo) for oppo in set(map(tuple, opportunities))]
    return unique_oppo


def _get_lines_to_node_dict(dict_file: Dict[ASTNode, List[str]]) -> Dict[int, ASTNode]:
    lines_to_node_dict: Dict[int, ASTNode] = {}
    for node in dict_file:
        lines_to_node_dict[node.line] = node
    return lines_to_node_dict


def _transform_clusters(
    clusters_by_digits: List[List[int]],
    lines_to_node_dict: Dict[int, ASTNode]
) -> List[List[ASTNode]]:

    clusters_by_nodes: List[List[ASTNode]] = []
    for cluster in clusters_by_digits:
        lines_list = list(lines_to_node_dict.keys())
        nodes_list = list(lines_to_node_dict.values())
        start_index = lines_list.index(cluster[0])
        end_index = lines_list.index(cluster[1])
        clusters_by_nodes.append(nodes_list[start_index:end_index + 1])
    return clusters_by_nodes


def SEMI_ASTNodes(dict_file: Dict[ASTNode, List[str]]) -> List[List[ASTNode]]:
    clusters: List[List[int]] = SEMI(dict_file)
    lines_to_node_dict = _get_lines_to_node_dict(dict_file)
    return _transform_clusters(clusters, lines_to_node_dict)


def _reprocess_dict(method_semantic: Dict) -> Dict[ASTNode, List[str]]:
    reprocessed_dict = OrderedDict([])
    for statement in method_semantic.keys():
        new_values = []
        new_values += list(method_semantic[statement].used_variables)
        new_values += list(method_semantic[statement].used_objects)
        new_values += list(method_semantic[statement].used_methods)
        reprocessed_dict.update({statement: new_values})
    return reprocessed_dict


def _print_clusters(
    method_ast: AST, filepath: str, class_name: str, method_name: str
):
    method_semantic = extract_method_statements_semantic(method_ast)
    reporcessed_dict = _reprocess_dict(method_semantic)

    print('-' * 100)
    print(f'Starting algorithm for method: {method_name} in class: {class_name}')
    print('-' * 100)
    clusters = SEMI(reporcessed_dict)
    print(clusters)


if __name__ == '__main__':
    common_cli(_print_clusters, "Cluster statements in method.")