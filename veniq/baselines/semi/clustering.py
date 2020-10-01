from collections import Counter
from typing import List, Union, Dict
from collections import OrderedDict

from veniq.baselines.semi.extract_semantic import \
    extract_method_statements_semantic, StatementSemantic
from veniq.ast_framework import ASTNode, AST
from veniq.baselines.semi.common_cli import common_cli


def _check_is_common(
    dict_file: Dict,
    statement_1: Union[int, ASTNode],
    statement_2: Union[int, ASTNode]
) -> bool:
    '''
    This function obtain two statements and check whether
    they have common variables or method invocations or not.
    '''
    joined_names: Counter = Counter(dict_file[statement_1] + dict_file[statement_2])
    duplicates = {element: count for element, count in joined_names.items() if count > 1}.keys()
    return len(list(duplicates)) >= 1


def _is_in_range(elem: int, values: List[int]) -> bool:
    '''
    here we check whether considered element is between
    the gap of values or not.
    '''
    return elem >= values[0] and elem <= values[1]


def _process_statement(
    dict_file: Dict,
    step: int
) -> List[List[int]]:
    '''
    This function is aimed to process all statements
    for clustering: parwise checking of statements  in order to find
    common variables and form the list of clusters for a given step.
    '''
    clusters: List[List[int]] = []
    list_statements = list(dict_file.keys())
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
    '''
    Implementation of the original clustering method from the original
    article with some changes.
    Here we obtain length of the considered method and starting
    to apply algo for each step.
    '''
    opportunities = []
    first_statement_ = list(dict_file.keys())[0]
    last_statement_ = list(dict_file.keys())[-1]
    first_statement = first_statement_ if isinstance(first_statement_, int) else first_statement_.line
    last_statement = last_statement_ if isinstance(last_statement_, int) else last_statement_.line
    method_length = last_statement - first_statement + 1

    for step in range(1, method_length + 1):
        clusters = _process_statement(dict_file, step)
        opportunities += clusters
    unique_oppo = [list(oppo) for oppo in set(map(tuple, opportunities))]  # type: ignore
    return unique_oppo  # type: ignore


def _get_lines_to_node_dict(dict_file: Dict[ASTNode, List[str]]) -> Dict[int, ASTNode]:
    '''
    Here we form new dictionary, which consist of
    lines in code of statements and their ASTNode
    representation.
    '''
    lines_to_node_dict: Dict[int, ASTNode] = {}
    for node in dict_file:
        lines_to_node_dict[node.line] = node
    return lines_to_node_dict


def _transform_clusters(
    clusters_by_digits: List[List[int]],
    lines_to_node_dict: Dict[int, ASTNode]
) -> List[List[ASTNode]]:
    '''
    This method is aimed to represent clusters by
    digits to the clusters by ASTNodes.

    It means that we have clusters, such as:
    [[1,3], [4, 6]]
    But we want to represent it by ASTNodes. Also,
    each cluster should contain not only all elements 
    in the clusters.
    '''
    clusters_by_nodes: List[List[ASTNode]] = []
    for cluster in clusters_by_digits:
        lines_list = list(lines_to_node_dict.keys())
        nodes_list = list(lines_to_node_dict.values())
        start_index = lines_list.index(cluster[0])
        end_index = lines_list.index(cluster[1])
        clusters_by_nodes.append(nodes_list[start_index:end_index + 1])
    return clusters_by_nodes


def SEMI_ASTNodes(dict_file: Dict[ASTNode, List[str]]) -> List[List[ASTNode]]:
    '''
    This is the version of SEMI algoirthm with some changes:
    as the output we have clusters represented by all ASTNodes in them.
    '''
    clusters: List[List[int]] = SEMI(dict_file)
    lines_to_node_dict = _get_lines_to_node_dict(dict_file)
    return _transform_clusters(clusters, lines_to_node_dict)


def _reprocess_dict(method_semantic: Dict[ASTNode, StatementSemantic]) -> Dict[ASTNode, List[str]]:
    '''
    Since we have dictionary of inapropriate look,
    as it might be, we reprocess this dictionary.
    '''
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
    reprocessed_dict = _reprocess_dict(method_semantic)

    print('-' * 100)
    print(f'Starting algorithm for method: {method_name} in class: {class_name}')
    print('-' * 100)
    clusters = SEMI(reprocessed_dict)
    print(clusters)


if __name__ == '__main__':
    common_cli(_print_clusters, "Cluster statements in method.")
