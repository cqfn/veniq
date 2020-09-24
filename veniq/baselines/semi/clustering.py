from collections import Counter
from typing import Iterator, Tuple, List, Dict, Set
from collections import OrderedDict
from argparse import ArgumentParser
from veniq.utils.ast_builder import build_ast
from veniq.extract_method_baseline.extract_semantic import extract_method_statements_semantic  # type: ignore
from veniq.ast_framework import ASTNode, AST, ASTNodeType
from veniq.baselines.semi.methods_names_ast import methods_ast_and_name
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic


def _check_is_common(
    dict_file: Dict,
    statement_1: ASTNode,
    statement_2: ASTNode
) -> bool:
    joined_names: Counter = Counter(dict_file[statement_1] + dict_file[statement_2])
    duplicates = {element: count for element, count in joined_names.items() if count > 1}.keys()
    return len(list(duplicates)) >= 1


def _is_in_range(elem: int, values: List[ASTNode]) -> bool:
    return elem >= values[0].line and elem <= values[-1].line


def _process_statement(
    dict_file: Dict,
    list_statements: List[ASTNode],
    step: int
) -> Set[List[ASTNode]]:
    set_clusters = set()
    clusters: List[List[int]] = []
    for stat_1 in list_statements:
        for stat_2 in list_statements[:stat_1.line + step]:
            if stat_1.line < stat_2.line and _check_is_common(dict_file, stat_1, stat_2):
                if len(clusters) != 0 and _is_in_range(stat_1.line, clusters[-1]):
                    if not _is_in_range(stat_2.line, clusters[-1]):
                        clusters[-1][-1] = stat_2
                else:
                    clusters.append([stat_1, stat_2])
    return clusters


def SEMI_beta(dict_file: Dict, method_len: int) -> Dict[int, List[List[int]]]:
    all_clusters = {}
    statements = list(dict_file.keys())
    for step in range(1, method_len + 1):
        clusters = _process_statement(dict_file, statements, step)
        all_clusters[step] = clusters
    return all_clusters


def _reprocess_dict(method_semantic: Dict) -> Dict[ASTNode, List[str]]:
    reprocessed_dict = OrderedDict([])
    for statement in method_semantic.keys():
        new_values = []
        new_values += list(method_semantic[statement].used_variables)
        new_values += list(method_semantic[statement].used_objects)
        new_values += list(method_semantic[statement].used_methods)
        reprocessed_dict.update({statement: new_values})
    return reprocessed_dict


def _get_clusters(
    methods_ast_and_method_name: Iterator[Tuple[AST, str]]
) -> None:

    for method_ast, class_name in methods_ast_and_method_name:
        method_clusters = []
        method_name = method_ast.get_root().name
        method_semantic = extract_method_statements_semantic(method_ast)
        reporcessed_dict = _reprocess_dict(method_semantic)

        first_statement_ = list(reporcessed_dict.keys())[0]
        last_statement_ = list(reporcessed_dict.keys())[-1]
        first_statement = first_statement_ if isinstance(first_statement_, int) else first_statement_.line
        last_statement = last_statement_ if isinstance(last_statement_, int) else last_statement_.line

        method_length = last_statement - first_statement
        print('-' * 60)
        print(f'Starting algorithm for method: {method_name} in Class: {class_name}')
        print('-' * 60)
        clusters = SEMI_beta(reporcessed_dict, method_length)
        method_clusters.append((method_name, clusters))
        print(method_clusters)


if __name__ == '__main__':
    parser = ArgumentParser(description="Extracts semantic from specified methods")
    parser.add_argument("-f", "--file", required=True,
                        help="File path to JAVA source code for extracting semantic")
    parser.add_argument("-c", "--class", default=None, dest="class_name",
                        help="Class name of method to parse, if omitted all classes are considered")
    parser.add_argument("-m", "--method", default=None, dest="method_name",
                        help="Method name to parse, if omitted all method are considered")
    parser.add_argument("-v", "--verbose", default=None, dest="verbose_mode",
                        help="Mode to print clusters for each step")

    args = parser.parse_args()

    iterator_ast_and_name = methods_ast_and_name(args.file, args.class_name, args.method_name)
    _get_clusters(iterator_ast_and_name)
