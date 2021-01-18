import hashlib
import os
import os.path
import re
import shutil
import tarfile
import typing
from argparse import ArgumentParser
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Tuple, Dict, List, Any, Set, Optional
from enum import Enum

import javalang
import pandas as pd
from pebble import ProcessPool
from tqdm import tqdm

from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.dataset_collection.types_identifier import AlgorithmFactory, InlineTypesAlgorithms
from veniq.metrics.ncss.ncss import NCSSMetric
from veniq.utils.ast_builder import build_ast
from veniq.utils.encoding_detector import read_text_with_autodetected_encoding


def _get_last_line(file_path: Path, start_line: int) -> int:
    """
    This function is aimed to find the last body line of
    considered method. It work by counting the difference
    in number of openning brackets '{' and closing brackets
    '}'. It's start with the method declaration line and going
    to the line where the difference is equal to 0. Which means
    that we found closind bracket of method declaration.
    """
    with open(file_path, encoding='utf-8') as f:
        file_lines = list(f)
        # to start counting opening brackets
        difference_cases = 0

        processed_declaration_line = file_lines[start_line - 1].split('//')[0]
        difference_cases += processed_declaration_line.count('{')
        difference_cases -= processed_declaration_line.count('}')
        for i, line in enumerate(file_lines[start_line:], start_line):
            if difference_cases:
                line_without_comments = line.split('//')[0]
                difference_cases += line_without_comments.count('{')
                difference_cases -= line_without_comments.count('}')
            else:
                # process comments to the last line of method
                if line.strip() == '*/':
                    return i + 2
                else:
                    return i

        return -1


def get_line_with_first_open_bracket(
        file_path: Path,
        method_decl_start_line: int
) -> int:
    with open(file_path, encoding='utf-8') as f:
        file_lines = f.read().split('\n')
        for i, line in enumerate(file_lines[method_decl_start_line - 2:], method_decl_start_line - 2):
            if '{' in line:
                return i + 1
        return method_decl_start_line + 1


def method_body_lines(method_node: ASTNode, file_path: Path) -> Tuple[int, int]:
    """
    Get start and end of method's body
    """
    if len(method_node.body):
        m_decl_start_line = start_line = method_node.line + 1
        start_line = get_line_with_first_open_bracket(file_path, m_decl_start_line)
        end_line = _get_last_line(file_path, start_line)
    else:
        start_line = end_line = -1
    return start_line, end_line


def check_nesting_statements(
        method_invoked: ASTNode
) -> bool:
    """
    Check that the considered method invocation is not
    at the same line as prohibited statements.
    """
    prohibited_statements = [
        # ASTNodeType.IF_STATEMENT,
        # ASTNodeType.WHILE_STATEMENT,
        # ASTNodeType.FOR_STATEMENT,
        ASTNodeType.SYNCHRONIZED_STATEMENT,
        ASTNodeType.CATCH_CLAUSE,
        ASTNodeType.SUPER_CONSTRUCTOR_INVOCATION,
        ASTNodeType.TRY_STATEMENT
    ]
    if method_invoked.parent is not None:
        if (method_invoked.parent.node_type in prohibited_statements) \
                and (method_invoked.parent.line == method_invoked.line):
            return False

        if method_invoked.parent.parent is not None:
            if (method_invoked.parent.parent.node_type in prohibited_statements) \
                    and (method_invoked.parent.parent.line == method_invoked.line):
                return False

            if method_invoked.parent.parent.parent is not None:
                if (method_invoked.parent.parent.parent.node_type in prohibited_statements) \
                        and (method_invoked.parent.parent.parent.line == method_invoked.line):
                    return False

    return True


class InvocationType(Enum):

    # OK = 0
    METHOD_CHAIN_BEFORE = 1
    NOT_SIMPLE_ACTUAL_PARAMETER = 2
    METHOD_CHAIN_AFTER = 3
    INSIDE_IF = 4
    INSIDE_WHILE = 5
    INSIDE_FOR = 6
    INSIDE_FOREACH = 7
    INSIDE_BINARY_OPERATION = 8
    INSIDE_TERNARY = 9
    INSIDE_CLASS_CREATOR = 10
    CAST_OF_RETURN_TYPE = 11
    INSIDE_ARRAY_CREATOR = 12
    SINGLE_STATEMENT_IN_IF = 13
    INSIDE_LAMBDA = 14
    #ALREADY_ASSIGNED_VALUE_IN_INVOCATION = 15
    SEVERAL_RETURNS = 16
    IS_NOT_AT_THE_SAME_LINE_AS_PROHIBITED_STATS = 17
    IS_NOT_PARENT_MEMBER_REF = 18
    # EXTRACTED_NCSS_SMALL = 19
    #CROSSED_VAR_NAMES_INSIDE_FUNCTION = 20
    CAST_IN_ACTUAL_PARAMS = 21
    ABSTRACT_METHOD = 22
    #CROSSED_FUNC_NAMES = 23
    #METHOD_WITH_ARGUMENTS_VAR_CROSSED = 999


    @classmethod
    def list_types(cls):
        types = [member.name for role, member in cls.__members__.items()]
        return types


@typing.no_type_check
def is_match_to_the_conditions(
        ast: AST,
        method_invoked: ASTNode,
        found_method_decl=None) -> List[str]:
    if method_invoked.parent.node_type == ASTNodeType.THIS:
        parent = method_invoked.parent.parent
        class_names = [x for x in method_invoked.parent.children if hasattr(x, 'string')]
        member_references = [x for x in method_invoked.parent.children if hasattr(x, 'member')]
        lst = [x for x in member_references if x.member != method_invoked.member] + class_names
        no_children = not lst
    else:
        parent = method_invoked.parent
        no_children = True

    is_not_is_extract_method_abstract = True
    if 'abstract' in found_method_decl.modifiers:
        is_not_is_extract_method_abstract = False

    maybe_if = parent.parent
    is_not_method_inv_single_statement_in_if = True
    if maybe_if.node_type == ASTNodeType.IF_STATEMENT:
        if hasattr(maybe_if.then_statement, 'expression'):
            if maybe_if.then_statement.expression.node_type == ASTNodeType.METHOD_INVOCATION:
                is_not_method_inv_single_statement_in_if = False

    is_not_assign_value_with_return_type = True
    is_not_several_returns = True
    if hasattr(found_method_decl, 'return_type'):
        if found_method_decl.return_type:
            if parent.node_type == ASTNodeType.VARIABLE_DECLARATOR:
                is_not_assign_value_with_return_type = False

            ast_subtree = ast.get_subtree(found_method_decl)
            stats = [x for x in ast_subtree.get_proxy_nodes(ASTNodeType.RETURN_STATEMENT)]
            if len(stats) > 1:
                is_not_several_returns = False

    is_not_parent_member_ref = not (method_invoked.parent.node_type == ASTNodeType.MEMBER_REFERENCE)
    is_not_chain_before = not (parent.node_type == ASTNodeType.METHOD_INVOCATION) and no_children
    chains_after = [x for x in method_invoked.children if x.node_type == ASTNodeType.METHOD_INVOCATION]
    is_not_chain_after = not chains_after
    is_not_inside_if = not (parent.node_type == ASTNodeType.IF_STATEMENT)
    is_not_inside_while = not (parent.node_type == ASTNodeType.WHILE_STATEMENT)
    is_not_inside_for = not (parent.node_type == ASTNodeType.FOR_STATEMENT)
    is_not_enhanced_for_control = not (parent.node_type == ASTNodeType.ENHANCED_FOR_CONTROL)
    # ignore case else if (getServiceInterface() != null) {
    is_not_binary_operation = not (parent.node_type == ASTNodeType.BINARY_OPERATION)
    is_not_ternary = not (parent.node_type == ASTNodeType.TERNARY_EXPRESSION)
    # if a parameter is any expression, we ignore it,
    # since it is difficult to extract with AST
    is_actual_parameter_simple = all([hasattr(x, 'member') for x in method_invoked.arguments])
    is_not_actual_param_cast = True
    if not is_actual_parameter_simple:
        found_casts = [x for x in method_invoked.arguments if x.node_type == ASTNodeType.CAST]
        if len(found_casts) > 0:
            is_not_actual_param_cast = False

    is_not_class_creator = not (parent.node_type == ASTNodeType.CLASS_CREATOR)
    is_not_cast_of_return_type = not (parent.node_type == ASTNodeType.CAST)
    is_not_array_creator = not (parent.node_type == ASTNodeType.ARRAY_CREATOR)
    is_not_lambda = not (parent.node_type == ASTNodeType.LAMBDA_EXPRESSION)
    is_not_at_the_same_line_as_prohibited_stats = check_nesting_statements(method_invoked)

    are_crossed_func_params = True
    if is_actual_parameter_simple:
        if are_not_params_crossed(method_invoked, found_method_decl):
            are_crossed_func_params = False

    ignored_cases = get_stats_for_pruned_cases(
        is_actual_parameter_simple,
        is_not_array_creator,
        is_not_assign_value_with_return_type,
        is_not_at_the_same_line_as_prohibited_stats,
        is_not_binary_operation,
        is_not_cast_of_return_type,
        is_not_chain_after,
        is_not_chain_before,
        is_not_class_creator,
        is_not_enhanced_for_control,
        is_not_inside_for,
        is_not_inside_if,
        is_not_inside_while,
        is_not_lambda,
        is_not_method_inv_single_statement_in_if,
        is_not_parent_member_ref,
        is_not_several_returns,
        is_not_ternary,
        is_not_actual_param_cast,
        is_not_is_extract_method_abstract,
        are_crossed_func_params,
        method_invoked
    )

    return ignored_cases


def are_not_params_crossed(
        invocaton_node: ASTNode,
        method_declaration: ASTNode) -> bool:
    """
    Check if names of params of invocation are matched with
    params of method declaration:

    Matched:
    func(a, b);
    public void func(int a, int b)

    Not matched
    func(a, e);
    public void func(int a, int b)

    :param invocaton_node: invocation of function
    :param method_declaration: method declaration of invoked function
    :return:
    """
    m_decl_names = set([x.name for x in method_declaration.parameters])
    m_inv_names = set([x.member for x in invocaton_node.arguments])
    intersection = m_inv_names.difference(m_decl_names)
    if not intersection:
        return True
    else:
        return False


def get_stats_for_pruned_cases(
        is_actual_parameter_simple, is_not_array_creator, is_not_assign_value_with_return_type,
        is_not_at_the_same_line_as_prohibited_stats, is_not_binary_operation,
        is_not_cast_of_return_type, is_not_chain_after, is_not_chain_before,
        is_not_class_creator, is_not_enhanced_for_control, is_not_inside_for,
        is_not_inside_if, is_not_inside_while, is_not_lambda,
        is_not_method_inv_single_statement_in_if, is_not_parent_member_ref,
        is_not_several_returns, is_not_ternary, is_not_actual_param_cast,
        is_not_is_extract_method_abstract, are_crossed_func_params, method_invoked) -> List[str]:
    invocation_types_to_ignore: List[str] = []

    if not is_not_is_extract_method_abstract:
        invocation_types_to_ignore.append(InvocationType.ABSTRACT_METHOD.name)
    if not is_not_chain_before:
        invocation_types_to_ignore.append(InvocationType.METHOD_CHAIN_BEFORE.name)
    if not is_actual_parameter_simple:
        invocation_types_to_ignore.append(InvocationType.NOT_SIMPLE_ACTUAL_PARAMETER.name)
    if not is_not_actual_param_cast:
        invocation_types_to_ignore.append(InvocationType.CAST_IN_ACTUAL_PARAMS.name)
    if not is_not_chain_after:
        invocation_types_to_ignore.append(InvocationType.METHOD_CHAIN_AFTER.name)
    if not is_not_inside_if:
        invocation_types_to_ignore.append(InvocationType.INSIDE_IF.name)
    if not is_not_inside_while:
        invocation_types_to_ignore.append(InvocationType.INSIDE_WHILE.name)
    if not is_not_binary_operation:
        invocation_types_to_ignore.append(InvocationType.INSIDE_BINARY_OPERATION.name)
    if not is_not_ternary:
        invocation_types_to_ignore.append(InvocationType.INSIDE_TERNARY.name)
    if not is_not_class_creator:
        invocation_types_to_ignore.append(InvocationType.INSIDE_CLASS_CREATOR.name)
    if not is_not_cast_of_return_type:
        invocation_types_to_ignore.append(InvocationType.CAST_OF_RETURN_TYPE.name)
    if not is_not_array_creator:
        invocation_types_to_ignore.append(InvocationType.INSIDE_ARRAY_CREATOR.name)
    if not is_not_parent_member_ref:
        invocation_types_to_ignore.append(InvocationType.IS_NOT_PARENT_MEMBER_REF.name)
    if not is_not_inside_for:
        invocation_types_to_ignore.append(InvocationType.INSIDE_FOR.name)
    if not is_not_enhanced_for_control:
        invocation_types_to_ignore.append(InvocationType.INSIDE_FOREACH.name)
    if not is_not_lambda:
        invocation_types_to_ignore.append(InvocationType.INSIDE_LAMBDA.name)
    if not is_not_method_inv_single_statement_in_if:
        invocation_types_to_ignore.append(InvocationType.SINGLE_STATEMENT_IN_IF.name)
    # if not is_not_assign_value_with_return_type:
    #     invocation_types_to_ignore.append(InvocationType.ALREADY_ASSIGNED_VALUE_IN_INVOCATION.name)
    if not is_not_several_returns:
        invocation_types_to_ignore.append(InvocationType.SEVERAL_RETURNS.name)
    if not is_not_at_the_same_line_as_prohibited_stats:
        invocation_types_to_ignore.append(InvocationType.IS_NOT_AT_THE_SAME_LINE_AS_PROHIBITED_STATS.name)

    return invocation_types_to_ignore


def check_whether_method_has_return_type(
        method_decl: AST,
        var_decls: Set[str],
        line_to_csv: Dict[str, Any]) -> InlineTypesAlgorithms:
    """
    Run function to check whether Method declaration can be inlined
    :param line_to_csv: dict of insertion result as row for DataFrame
    :param method_decl: method, where invocation occurred
    :param var_decls: set of variables for found invoked method
    :return: enum InlineTypesAlgorithms
    """
    names = get_variables_decl_in_node(method_decl)

    var_decls_original = set(names)
    intersected_names = var_decls & var_decls_original
    # if we do not have intersected name in target method and inlined method
    # and if we do not have var declarations at all
    if not var_decls or not intersected_names:
        return InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS

    if intersected_names:
        line_to_csv[InvocationType.CROSSED_VAR_NAMES_INSIDE_FUNCTION.name] = True

    return InlineTypesAlgorithms.DO_NOTHING


def get_variables_decl_in_node(
        method_decl: AST) -> List[str]:
    names = []
    for x in method_decl.get_proxy_nodes(ASTNodeType.VARIABLE_DECLARATOR):
        if hasattr(x, 'name'):
            names.append(x.name)
        elif hasattr(x, 'names'):
            names.extend(x.names)

    for x in method_decl.get_proxy_nodes(ASTNodeType.VARIABLE_DECLARATION):
        if hasattr(x, 'name'):
            names.append(x.name)
        elif hasattr(x, 'names'):
            names.extend(x.names)

    for x in method_decl.get_proxy_nodes(ASTNodeType.TRY_RESOURCE):
        names.append(x.name)

    return names


def determine_algorithm_insertion_type(
        ast: AST,
        method_node: ASTNode,
        invocation_node: ASTNode,
        dict_original_nodes: Dict[str, List[ASTNode]],
        line_to_csv
) -> InlineTypesAlgorithms:
    """

    :param ast: ast tree
    :param dict_original_nodes: dict with names of function as key
    and list of ASTNode as values
    :param method_node: Method declaration. In this method invocation occurred
    :param invocation_node: invocation node
    :return: InlineTypesAlgorithms enum
    """

    original_invoked_method = dict_original_nodes.get(invocation_node.member, [])
    # ignore overridden functions
    if (len(original_invoked_method) == 0) or (len(original_invoked_method) > 1):
        return InlineTypesAlgorithms.DO_NOTHING
    else:
        original_method = original_invoked_method[0]
        has_attr_return_type = hasattr(original_method, 'return_type')
        if has_attr_return_type:
            if not original_method.return_type:
                return InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS
            else:
                return InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS
        #  Else if we have constructor, it doesn't have return type
        else:
            return InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS


def run_var_crossing_check(ast, line_to_csv, method_node, original_method):
    # Find the original method declaration by the name of method invocation
    var_decls = set(get_variables_decl_in_node(ast.get_subtree(original_method)))
    return check_whether_method_has_return_type(
        ast.get_subtree(method_node),
        var_decls,
        line_to_csv
    )


def insert_code_with_new_file_creation(
        class_name: str,
        ast: AST,
        method_node: ASTNode,
        invocation_node: ASTNode,
        file_path: Path,
        output_path: Path,
        dict_original_invocations: Dict[str, List[ASTNode]],
        row_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    If invocations of class methods were found,
    we process through all of them and for each
    substitution opportunity by method's body,
    we create new file.
    """
    file_name = file_path.stem
    if not os.path.exists(output_path):
        output_path.mkdir(parents=True)

    new_full_filename = Path(output_path, f'{file_name}_{method_node.name}_{invocation_node.line}.java')
    original_func = dict_original_invocations.get(invocation_node.member)[0]  # type: ignore
    # ncss_extracted = NCSSMetric().value(ast.get_subtree(original_func))
    # line_to_csv = {}
    # @acheshkov asked to consider only methods with ncss > 3, that's all.
    # ncss_target = NCSSMetric().value(ast.get_subtree(method_node))
    body_start_line, body_end_line = method_body_lines(original_func, file_path)
    text_lines = read_text_with_autodetected_encoding(str(file_path)).split('\n')
    # we do not inline one-line methods like
    # public String getRemainingString() {return str.substring(index);}
    if body_start_line != body_end_line:
        algorithm_type = determine_algorithm_insertion_type(
            ast,
            method_node,
            invocation_node,
            dict_original_invocations,
            row_dict
        )
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        if algorithm_type != InlineTypesAlgorithms.DO_NOTHING:
            row_dict.update({
                'original_filename': file_path,
                'class_name': class_name,
                'invocation_line_string': text_lines[invocation_node.line - 1].lstrip().encode('utf-8').decode('utf-8'),
                'target_method': method_node.name,
                'extract_method': original_func.name,
                'output_filename': Path(new_full_filename).name,
                'target_method_start_line': method_node.line,
                'do_nothing': False,
                # 'ncss_extracted': ncss_extracted,
                # 'ncss_target': ncss_target
            })

            inline_method_bounds = algorithm_for_inlining().inline_function(
                file_path,
                invocation_node.line,
                body_start_line,
                body_end_line,
                new_full_filename,
            )
            if inline_method_bounds is not None:
                row_dict['insertion_start'] = inline_method_bounds[0]
                row_dict['insertion_end'] = inline_method_bounds[1]

                if get_ast_if_possible(new_full_filename):
                    rest_of_csv_row_for_changed_file = find_lines_in_changed_file(
                        class_name=class_name,
                        new_full_filename=new_full_filename,
                        original_func=original_func)
                    is_valid_ast = True
                    row_dict.update(rest_of_csv_row_for_changed_file)
                else:
                    is_valid_ast = False

                row_dict['is_valid_ast'] = is_valid_ast
        else:
            row_dict['do_nothing'] = True
    else:
        row_dict['ONE_LINE_FUNCTION'] = True
    return row_dict


# type: ignore
def find_lines_in_changed_file(
        new_full_filename: Path,
        original_func: ASTNode,
        class_name: str) -> Dict[str, Any]:
    """
    Find start and end line of invocation for changed file
    :param class_name: class name of old file
    :param new_full_filename: name of new file
    :param method_node: method declaration of old file
    :param original_func: method declaration of invoked function in old file
    :return:
    """
    changed_ast = get_ast_if_possible(new_full_filename)
    if changed_ast:
        class_node_of_changed_file = [
            x for x in changed_ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
            if x.name == class_name][0]
        original_func_changed = [
            x for x in class_node_of_changed_file.methods
            if x.name == original_func.name][0]

        body_start_line, body_end_line = method_body_lines(original_func_changed, new_full_filename)
        return {
            'extract_method_start_line': body_start_line,
            'extract_method_end_line': body_end_line
        }
    else:
        return {}


def get_ast_if_possible(file_path: Path, res=None) -> Optional[AST]:
    """
    Processing file in order to check
    that its original version can be parsed
    """
    ast = None
    try:
        ast = AST.build_from_javalang(build_ast(str(file_path)))
    except javalang.parser.JavaSyntaxError:
        if res:
            res.error = 'JavaSyntaxError'
    except Exception as e:
        if res:
            res.error = str(e)

    return ast


def remove_comments(string):
    pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
    # first group captures quoted strings (double or single)
    # second group captures comments (//single-line or /* multi-line */)
    regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            # so we will return empty to remove the comment
            return ""
        else:  # otherwise, we will return the 1st group
            return match.group(1)  # captured quoted-string

    return regex.sub(_replacer, string)


# flake8: noqa: C901
def analyze_file(
        file_path: Path,
        output_path: Path,
        input_dir: Path,
        dataset_dir: str
) -> List[Any]:
    """
    In this function we process each file.
    For each file we find each invocation inside,
    which can be inlined.
    """
    # print(file_path)
    results: List[Any] = []
    original_text = read_text_with_autodetected_encoding(str(file_path))
    # remove comments
    text_without_comments = remove_comments(original_text)
    # remove whitespaces
    text = "\n".join([ll.rstrip() for ll in text_without_comments.splitlines() if ll.strip()])
    dst_filename = save_text_to_new_file(input_dir, text, file_path)

    ast = get_ast_if_possible(dst_filename)
    if ast is None:
        dst_filename.unlink()
        return results

    method_declarations: Dict[str, List[ASTNode]] = defaultdict(list)
    classes_declaration = [
        ast.get_subtree(node)
        for node in ast.get_root().types
        if node.node_type == ASTNodeType.CLASS_DECLARATION
    ]
    for class_ast in classes_declaration:
        class_declaration = class_ast.get_root()
        methods_list: List[ASTNode] = \
            list(class_declaration.methods) \
            + list(class_declaration.constructors)
        collect_info_about_functions_without_params(method_declarations, methods_list)

        for method_node in methods_list:
            method_decl = ast.get_subtree(method_node)
            found_functions = method_declarations.get(method_node.name, [])
            # we do not consider overloaded constructors and functions
            # as target functions
            if len(found_functions) == 1:
                for invocation_node in method_decl.get_proxy_nodes(
                        ASTNodeType.METHOD_INVOCATION):
                    # print(f'Method: {method_node.name} inv: {invocation_node.member}')

                    extracted_function_method_decl = method_declarations.get(invocation_node.member, [])
                    # ignore overloaded extracted functions
                    if len(extracted_function_method_decl) == 1:
                        try:
                            # print(f'Method: {method_node.name} inv: {invocation_node.member}')
                            make_insertion(
                                ast,
                                class_declaration,
                                dst_filename,
                                extracted_function_method_decl,
                                method_declarations,
                                invocation_node,
                                method_node,
                                output_path,
                                file_path,
                                results,
                                dataset_dir
                            )
                        except Exception as e:
                            print('Error has happened during file analyze: ' + str(e))

    if not results:
        dst_filename.unlink()

    return results


def make_insertion(
        ast, class_declaration, dst_filename,
        found_method_decl, method_declarations, method_invoked,
        method_node, output_path, source_filepath, results,
        dataset_dir):

    if (not method_invoked.qualifier) or (method_invoked.qualifier == 'this'):
        ignored_cases = is_match_to_the_conditions(
            ast,
            method_invoked,
            found_method_decl[0])

        original_func = method_declarations.get(method_invoked.member)[0]  # type: ignore
        ncss_extracted = NCSSMetric().value(ast.get_subtree(original_func))
        ncss_target = NCSSMetric().value(ast.get_subtree(method_node))

        if ncss_extracted > 3:
            log_of_inline = {
                'extract_method': method_invoked.member,
                'target_method': method_node.name,
                'ncss_extracted': ncss_extracted,
                'ncss_target': ncss_target,
                'invocation_line_number_in_original_file': method_invoked.line
            }
            # default init
            for case_name in InvocationType.list_types():
                log_of_inline[case_name] = False

            if not ignored_cases:
                insert_code_with_new_file_creation(
                    class_declaration.name,
                    ast,
                    method_node,
                    method_invoked,
                    dst_filename,
                    output_path,
                    method_declarations,
                    log_of_inline)
                log_of_inline['NO_IGNORED_CASES'] = True
            else:
                log_of_inline['NO_IGNORED_CASES'] = False

            # found ignored cases
            for case_name in ignored_cases:
                log_of_inline[case_name] = True

            # change source filename, since it will be changed
            log_of_inline['original_filename'] = dst_filename.name
            # remove full_dataset/input prefix
            # real_input_dataset_path = Path('/'.join(Path(input_dir).absolute().parts[:-2]))
            project_id = '/'.join(Path(source_filepath.absolute()).relative_to(Path(dataset_dir).absolute()).parts[:2])
            # print(dst_filename.absolute(), input_dir.absolute(), project_id)
            log_of_inline['project_id'] = project_id
            results.append(log_of_inline)


def collect_info_about_functions_without_params(
        method_declarations: Dict[str, List[ASTNode]],
        list_of_considered_nodes: List[ASTNode]) -> None:
    for node in list_of_considered_nodes:
        method_declarations[node.name].append(node)


def save_text_to_new_file(input_dir: Path, text: str, filename: Path) -> Path:
    # need to avoid situation when filenames are the same
    hash_path = hashlib.sha256(str(filename.parent).encode('utf-8')).hexdigest()
    dst_filename = input_dir / f'{filename.stem}_{hash_path}.java'
    if not dst_filename.parent.exists():
        dst_filename.parent.mkdir(parents=True)
    if not dst_filename.exists():
        with open(dst_filename, 'w', encoding='utf-8') as w:
            w.write(text)

    return dst_filename


if __name__ == '__main__':  # noqa: C901
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dir",
        required=True,
        help="File path to JAVA source code for methods augmentations"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path for file with output results",
        default='augmented_data'
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=system_cores_qty - 1,
        help="Number of processes to spawn. "
             "By default one less than number of cores. "
             "Be careful to raise it above, machine may stop responding while creating dataset.",
    )
    parser.add_argument(
        "-z", "--zip",
        action='store_true',
        help="To zip input and output files."
    )
    parser.add_argument(
        "-s", "--small_dataset_size",
        help="Number of files in small dataset",
        default=100,
        type=int,
    )

    args = parser.parse_args()

    test_files = set(Path(args.dir).glob('**/*Test*.java'))
    not_test_files = set(Path(args.dir).glob('**/*.java'))
    files_without_tests = list(not_test_files.difference(test_files))

    full_dataset_folder = Path(args.output) / 'full_dataset'
    output_dir = full_dataset_folder / 'output_files'
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    input_dir = full_dataset_folder / 'input_files'
    if not input_dir.exists():
        input_dir.mkdir(parents=True)
    csv_output = Path(full_dataset_folder, 'out.csv')

    columns = [
        'project_id',
        'original_filename',
        'class_name',
        'invocation_line_string',
        'invocation_line_number_in_original_file',
        'target_method',
        'target_method_start_line',
        'extract_method',
        'extract_method_start_line',
        'extract_method_end_line',
        'output_filename',
        'is_valid_ast',
        'insertion_start',
        'insertion_end',
        'ncss_target',
        'ncss_extracted',
        'do_nothing',
        'ONE_LINE_FUNCTION',
        'NO_IGNORED_CASES'
    ] + [x for x in InvocationType.list_types()]
    df = pd.DataFrame(columns=columns)

    with ProcessPool(system_cores_qty) as executor:
        p_analyze = partial(
            analyze_file,
            output_path=output_dir.absolute(),
            input_dir=input_dir,
            dataset_dir=args.dir
        )
        future = executor.map(p_analyze, files_without_tests, timeout=1000, )
        result = future.result()

        # each 100 cycles we dump the results
        iteration_cycle = 100
        iteration_number = 0
        for filename in tqdm(files_without_tests):
            try:
                single_file_features = next(result)
                if single_file_features:
                    for i in single_file_features:
                        #  get local path for inlined filename
                        # i['output_filename'] = i['output_filename'].relative_to(os.getcwd()).as_posix()
                        # print(i['output_filename'], filename)
                        df = df.append(i, ignore_index=True)

                if (iteration_number % iteration_cycle) == 0:
                    df.to_csv(csv_output)
                iteration_number += 1
            except Exception as e:
                print(str(e))
                import traceback
                traceback.print_exc()

    df.to_csv(csv_output)
    if args.zip:
        samples = pd.read_csv(csv_output).sample(args.small_dataset_size, random_state=41)
        small_dataset_folder = Path(args.output) / 'small_dataset'
        if not small_dataset_folder.exists():
            small_dataset_folder.mkdir(parents=True)
        small_input_dir = small_dataset_folder / 'input_files'
        if not small_input_dir.exists():
            small_input_dir.mkdir(parents=True)
        small_output_dir = small_dataset_folder / 'output_files'
        if not small_output_dir.exists():
            small_output_dir.mkdir(parents=True)

        samples.to_csv(small_dataset_folder / 'out.csv')
        for index, row in samples.iterrows():
            original_filename = row['original_filename']
            dst_filename = small_input_dir / Path(original_filename).name
            shutil.copyfile(original_filename, dst_filename)
            output_filename = row['output_filename']
            dst_filename = small_output_dir / Path(output_filename).name
            shutil.copyfile(output_filename, dst_filename)

        with tarfile.open(Path(args.output) / 'small_dataset.tar.gz', "w:gz") as tar:
            tar.add(str(small_dataset_folder), arcname=str(small_dataset_folder))

        with tarfile.open(Path(args.output) / 'full_dataset.tar.gz', "w:gz") as tar:
            tar.add(str(full_dataset_folder), arcname=str(full_dataset_folder))

        if input_dir.exists():
            shutil.rmtree(full_dataset_folder)

        if small_dataset_folder.exists():
            shutil.rmtree(small_dataset_folder)
