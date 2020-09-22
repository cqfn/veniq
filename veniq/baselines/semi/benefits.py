from typing import Tuple, Dict
from aibolit.ast_framework import AST, ASTNodeType
from aibolit.utils.ast_builder import build_ast
from aibolit.extract_method_baseline.extract_semantic import extract_method_statements_semantic


def _LCOM2(filepath, range=[]):
    pass


def _LCOM2_after_ref(filepath, range):
    pass


def _reprocess_dict(method_semantic: Dict):
    reprocessed_dict = dict()
    for statement in method_semantic.keys():
        new_values = []
        new_values += list(method_semantic[statement].used_variables)
        new_values += list(method_semantic[statement].used_objects)
        new_values += list(method_semantic[statement].used_methods)
        reprocessed_dict[statement.line] = new_values
    return reprocessed_dict


def _get_dict(filepath: str):
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


def _get_benefit(filepath: str, range: Tuple[int, int]):
    original_value = _LCOM2(filepath)
    opportunity_value = _LCOM2(filepath, range)
    original_after_ref_value = _LCOM2_after_ref(filepath, range)

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
    diff_between_benefits = abs(first_benefit - second_benefit) / max(first_benefit, second_benefit)
    return diff_between_benefits >= difference_threshold
