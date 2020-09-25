from collections import Counter
from typing import List, Union, Dict
from collections import OrderedDict

from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.ast_framework import ASTNode, AST
from veniq.baselines.semi.common_cli import common_cli


def check_is_common(
    dict_file: Dict,
    statement_1: Union[int, ASTNode],
    statement_2: Union[int, ASTNode]
) -> bool:
    joined_names: Counter = Counter(dict_file[statement_1] + dict_file[statement_2])
    duplicates = {element: count for element, count in joined_names.items() if count > 1}.keys()
    return len(list(duplicates)) >= 1


def is_in_range(elem: int, values: List[int]) -> bool:
    return elem >= values[0] and elem <= values[1]


def process_statement(
    dict_file: Dict,
    list_statements: List[Union[int, ASTNode]],
    step: int
) -> List[List[int]]:
    clusters: List[List[int]] = []
    for stat_1 in list_statements:
        stat_1_line = stat_1 if isinstance(stat_1, int) else stat_1.line
        for stat_2 in list_statements[:stat_1_line + step]:
            stat_2_line = stat_2 if isinstance(stat_2, int) else stat_2.line
            if stat_1_line < stat_2_line and check_is_common(dict_file, stat_1, stat_2):
                if len(clusters) != 0 and is_in_range(stat_1_line, clusters[-1]):
                    if not is_in_range(stat_2_line, clusters[-1]):
                        clusters[-1][1] = stat_2_line
                else:
                    clusters.append([stat_1_line, stat_2_line])
    return clusters


def SEMI_beta(dict_file: Dict, method_len: int) -> Dict[int, List[List[int]]]:
    algo_step = {}
    statements = list(dict_file.keys())
    for step in range(1, method_len + 1):
        clusters = process_statement(dict_file, statements, step)
        algo_step[step] = clusters
    return algo_step


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

    first_statement_ = list(reporcessed_dict.keys())[0]
    last_statement_ = list(reporcessed_dict.keys())[-1]
    first_statement = first_statement_ if isinstance(first_statement_, int) else first_statement_.line
    last_statement = last_statement_ if isinstance(last_statement_, int) else last_statement_.line

    method_length = last_statement - first_statement

    print('-' * 50)
    print('Starting algorithm for method: ', method_name)
    print('-' * 50)
    clusters = SEMI_beta(reporcessed_dict, method_length)
    print(clusters)


if __name__ == '__main__':
    common_cli(_print_clusters, "Cluster statements in method.")
