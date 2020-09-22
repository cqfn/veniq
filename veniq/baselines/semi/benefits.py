from typing import Tuple, Dict, List
from aibolit.ast_framework import AST, ASTNodeType
from aibolit.utils.ast_builder import build_ast
from aibolit.extract_method_baseline.extract_semantic import extract_method_statements_semantic
from collections import Counter


def _check_is_common(
    dict_file: Dict,
    statement_1: int,
    statement_2: int
) -> bool:
    joined_names: Counter = Counter(dict_file[statement_1] + dict_file[statement_2])
    duplicates = {element: count for element, count in joined_names.items() if count > 1}.keys()
    return len(list(duplicates)) >= 1


def _reprocess_dict(method_semantic: Dict) -> Dict[int, List[str]]:
    reprocessed_dict = dict()
    for statement in method_semantic.keys():
        new_values = []
        new_values += list(method_semantic[statement].used_variables)
        new_values += list(method_semantic[statement].used_objects)
        new_values += list(method_semantic[statement].used_methods)
        reprocessed_dict[statement.line] = new_values
    return reprocessed_dict


def _get_dict(filepath: str) -> Dict[int, List[str]]:
    ast = AST.build_from_javalang(build_ast(filepath))
    classes_declarations = (
        node for node in ast.get_root().types
        if node.node_type == ASTNodeType.CLASS_DECLARATION
    )

    methods_declarations = (
        method_declaration for class_declaration in classes_declarations
        for method_declaration in class_declaration.methods
    )

    methods_ast_and_class_name = (
        (ast.get_subtree(method_declaration), method_declaration.parent.name)
        for method_declaration in methods_declarations
    )

    for method_ast, class_name in methods_ast_and_class_name:
        # method_name = method_ast.get_root().name
        original_method_semantic = extract_method_statements_semantic(method_ast)
    reprocessed_dict = _reprocess_dict(original_method_semantic)
    return reprocessed_dict


def _LCOM2(file_dict: Dict, range_stats = [], mode = 'original') -> int:
    '''
    LCOM_2 = P - Q;
    P is the number of pairs of statements 
    that do not share variables and Q is the number 
    of pairs of lines that share variables
    '''
    P = 0
    Q = 0
    list_statements = []

    if mode == 'after_ref':
        list_statements = [i for i in file_dict if i < range_stats[0] or i > range_stats[1]]
    elif mode == 'opporturnity':
        list_statements = [i for i in range(range_stats[0], range_stats[1] + 1)]
    else:
        list_statements = file_dict.keys()

    for stat_1 in list_statements:
        for stat_2 in list_statements:
            if stat_1 < stat_2:
                if _check_is_common(file_dict, stat_1, stat_2):
                    Q += 1
                else:
                    P += 1
    return P - Q


def _get_benefit(filepath: str, range_stats: Tuple[int, int]) -> int:
    dict_semantic = _get_dict(filepath)
    original_value = _LCOM2(dict_semantic)
    opportunity_value = _LCOM2(dict_semantic, range_stats, 'opportunity')
    original_after_ref_value = _LCOM2(dict_semantic, range_stats, 'after_ref')
    return original_value - max(opportunity_value, original_after_ref_value)


def is_first_more_benefit(
    path_original_code: str,
    range_1: Tuple[int, int],
    range_2: Tuple[int, int],
    difference_threshold: float = 0.01
) -> bool:
    """
    Takes two opportunities and check if first opportunity
    is more benefit than the second one.
    """
    first_benefit = _get_benefit(path_original_code, range_1)
    second_benefit = _get_benefit(path_original_code, range_2)
    diff_between_benefits = abs(first_benefit - second_benefit) 
    diff_between_benefits /= max(first_benefit, second_benefit)
    return diff_between_benefits >= difference_threshold
