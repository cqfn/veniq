from typing import Dict, Any, Optional, List

from javalang.parse import parse

from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.dataset_collection.dataflow.annotation import method_body_lines
from veniq.dataset_collection.types_identifier import AlgorithmFactory, InlineTypesAlgorithms


def get_ast_if_possible(text: str) -> Optional[AST]:
    """
    Processing file in order to check
    that its original version can be parsed
    """
    ast = None
    try:
        ast = AST.build_from_javalang(parse(text))
    except Exception:
        pass
    return ast


def find_lines_in_changed_file(
        lines_of_final_file: List[str],
        method_node: ASTNode,
        original_func: ASTNode,
        class_name: str) -> Dict[str, Any]:
    """
    Find start and end line of invocation for changed file
    """

    inlined_text = '\n'.join(lines_of_final_file)
    changed_ast = get_ast_if_possible(inlined_text)
    if changed_ast:
        class_node_of_changed_file = [
            x for x in changed_ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
            if x.name == class_name][0]
        class_subtree = changed_ast.get_subtree(class_node_of_changed_file)
        node = [x for x in class_subtree.get_proxy_nodes(
            ASTNodeType.METHOD_DECLARATION,
            ASTNodeType.CONSTRUCTOR_DECLARATION)
                if x.name == method_node.name][0]  # type: ignore
        original_func_changed = [x for x in class_subtree.get_proxy_nodes(
            ASTNodeType.METHOD_DECLARATION) if x.name == original_func.name][0]

        body_start_line, body_end_line = method_body_lines(original_func_changed, inlined_text)
        return {
            'invocation_method_start_line': body_start_line,
            'invocation_method_end_line': body_end_line,
            'start_line_of_function_where_invocation_occurred': node.line
        }
    else:
        return {}


def inline(dct: Dict[str, Any]):
    """
    If invocations of class methods were found,
    we process through all of them and for each
    substitution opportunity by method's body,
    we create new file.
    """
    extracted_method_decl = dct['extracted_method_decl']
    method_invoked = dct['method_invoked']
    target_node = dct['target_node']
    text = dct['text']
    text_lines = text.split('\n')
    algorithm_type = dct['algorithm_type']
    body_start_line = dct['extract_method_start_line']
    body_end_line = dct['extract_method_end_line']
    class_name = dct['class_name']
    algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)

    updated_dict = {
        'invocation_line_string': text_lines[method_invoked.line - 1].lstrip().encode('utf-8').decode('utf-8'),
        'target_method': target_node.name,
        'extract_method': extracted_method_decl.name,
        'target_method_start_line': target_node.line,
        'do_nothing': algorithm_type.name
    }
    updated_dict = {**updated_dict, **dct.update}

    if algorithm_type != InlineTypesAlgorithms.DO_NOTHING:
        lines_of_final_file, inline_method_bounds = algorithm_for_inlining().inline_function(
            method_invoked.line,
            body_start_line,
            body_end_line,
            text_lines
        )
        if inline_method_bounds is not None:
            dct['insertion_start'] = inline_method_bounds[0]
            dct['insertion_end'] = inline_method_bounds[1]

            if get_ast_if_possible(text):
                rest_of_csv_row_for_changed_file = find_lines_in_changed_file(
                    method_node=target_node,
                    class_name=class_name,
                    lines_of_final_file=lines_of_final_file,
                    original_func=extracted_method_decl)

                is_valid_ast = True
                updated_dict['is_valid_ast'] = is_valid_ast
                updated_dict = {**updated_dict, **rest_of_csv_row_for_changed_file}
            else:
                is_valid_ast = False
                updated_dict['is_valid_ast'] = is_valid_ast
    else:
        updated_dict['do_nothing'] = True

    yield updated_dict
