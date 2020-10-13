import csv
import uuid
from argparse import ArgumentParser
import os
from collections import defaultdict
from functools import partial
from typing import Tuple, Dict, List, Any
from pathlib import Path

import typing
from pebble import ProcessPool
from tqdm import tqdm

from veniq.utils.encoding_detector import read_text_with_autodetected_encoding
from veniq.dataset_collection.types_identifier import AlgorithmFactory, InlineTypesAlgorithms
from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.utils.ast_builder import build_ast


def _get_last_return_line(child_statement: ASTNode) -> int:
    """
    This function is aimed to find the last line of
    the all children and children of children
    for a chosen statement.
    Main goal is to get the last line of return in method.
    """
    last_line = child_statement.line
    if hasattr(child_statement, 'children'):
        for children in child_statement.children:
            if children.line >= last_line:
                last_line = _get_last_return_line(children)
    return last_line


def _get_last_line(file_path: Path, last_return_line: int) -> int:
    """
    Here we reprocess obtained the list line of return statement
    in order to get the line of the last case '}' of method
    declaration statement. This step is crucial for the
    correct inline part!
    """
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()[last_return_line:]
        for i, file_line in enumerate(lines, last_return_line):
            last_case_line = file_line.replace('\n', '').replace(' ', '')
            if len(last_case_line) == 0:
                return i - 1
        return -1


def method_body_lines(method_node: ASTNode, file_path: Path) -> Tuple[int, int]:
    """
    Ger start and end of method's body
    """
    method_all_children = list(method_node.children)[-1]
    if len(method_node.body):
        start_line = method_node.body[0].line
        last_return_line = _get_last_return_line(method_all_children)
        end_line = _get_last_line(file_path, last_return_line)
    else:
        start_line = end_line = -1
    return start_line, end_line


@typing.no_type_check
def is_match_to_the_conditions(
        ast: AST,
        method_invoked: ASTNode,
        found_method_decl=None) -> bool:
    if method_invoked.parent.node_type == ASTNodeType.THIS:
        parent = method_invoked.parent.parent
        class_names = [x for x in method_invoked.parent.children if hasattr(x, 'string')]
        member_references = [x for x in method_invoked.parent.children if hasattr(x, 'member')]
        lst = [x for x in member_references if x.member != method_invoked.member] + class_names
        no_children = not lst
    else:
        parent = method_invoked.parent
        no_children = True

    maybe_if = parent.parent
    is_not_method_inv_single_statement_in_if = True
    if maybe_if.node_type == ASTNodeType.IF_STATEMENT:
        if hasattr(maybe_if.then_statement, 'expression'):
            if maybe_if.then_statement.expression.node_type == ASTNodeType.METHOD_INVOCATION:
                is_not_method_inv_single_statement_in_if = False

    is_not_assign_value_with_return_type = True
    is_not_several_returns = True
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
    is_not_class_creator = not (parent.node_type == ASTNodeType.CLASS_CREATOR)
    is_not_cast = not (parent.node_type == ASTNodeType.CAST)
    is_not_array_creator = not (parent.node_type == ASTNodeType.ARRAY_CREATOR)
    is_not_lambda = not (parent.node_type == ASTNodeType.LAMBDA_EXPRESSION)
    other_requirements = all([
        is_not_chain_before,
        is_actual_parameter_simple,
        is_not_chain_after,
        is_not_inside_if,
        is_not_inside_while,
        is_not_binary_operation,
        is_not_ternary,
        is_not_class_creator,
        is_not_cast,
        is_not_array_creator,
        is_not_parent_member_ref,
        is_not_inside_for,
        is_not_enhanced_for_control,
        is_not_lambda,
        is_not_method_inv_single_statement_in_if,
        is_not_assign_value_with_return_type,
        is_not_several_returns,
        not method_invoked.arguments])

    if (not method_invoked.qualifier and other_requirements) or \
            (method_invoked.qualifier == 'this' and other_requirements):
        return True
    else:
        return False


def check_whether_method_has_return_type(
        method_decl: AST,
        var_decls: typing.Set[str]) -> InlineTypesAlgorithms:
    """
    Run function to check whether Method declaration can be inlined
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
        dict_original_nodes: Dict[str, List[ASTNode]]
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
        if not original_method.parameters:
            if not original_method.return_type:
                # Find the original method declaration by the name of method invocation
                var_decls = set(get_variables_decl_in_node(ast.get_subtree(original_method)))
                return check_whether_method_has_return_type(
                    ast.get_subtree(method_node),
                    var_decls
                )
            else:
                return InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS
        else:
            return InlineTypesAlgorithms.DO_NOTHING


def insert_code_with_new_file_creation(
        class_name: str,
        ast: AST,
        method_node: ASTNode,
        invocation_node: ASTNode,
        file_path: Path,
        output_path: Path,
        dict_original_invocations: Dict[str, List[ASTNode]]
) -> List[Any]:
    """
    If invocations of class methods were found,
    we process through all of them and for each
    substitution opportunity by method's body,
    we create new file.
    """
    file_name = file_path.stem
    if not os.path.exists(output_path):
        output_path.mkdir(parents=True)

    id = uuid.uuid1()
    new_full_filename = Path(output_path, f'{file_name}_{invocation_node.name}_{method_node.name}{id}.java')
    original_func = dict_original_invocations.get(invocation_node.member)[0]  # type: ignore
    body_start_line, body_end_line = method_body_lines(original_func, file_path)
    text_lines = read_text_with_autodetected_encoding(str(file_path)).split('\n')

    line_to_csv = [
        str(file_path),
        class_name,
        text_lines[invocation_node.line - 1].strip(' '),
        invocation_node.line,
        original_func.line,
        method_node.name,
        id,
    ]

    algorithm_for_inlining = AlgorithmFactory().create_obj(
        determine_algorithm_insertion_type(ast, method_node, invocation_node, dict_original_invocations))

    algorithm_for_inlining().inline_function(
        file_path,
        invocation_node.line,
        body_start_line,
        body_end_line,
        new_full_filename,
    )

    return line_to_csv


def analyze_file(file_path: Path, output_path: Path) -> List[Any]:
    try:
        AST.build_from_javalang(build_ast(str(file_path)))
    except Exception:
        print('JavaSyntaxError while parsing ', file_path)

    ast = AST.build_from_javalang(build_ast(str(file_path)))
    method_declarations = defaultdict(list)
    classes_declaration = [
        ast.get_subtree(node)
        for node in ast.get_root().types
        if node.node_type == ASTNodeType.CLASS_DECLARATION
    ]
    results = []
    for class_ast in classes_declaration:
        class_declaration = class_ast.get_root()
        for method in class_declaration.methods:
            if not method.parameters:
                method_declarations[method.name].append(method)

        methods_list = list(class_declaration.methods) + list(class_declaration.constructors)
        for method_node in methods_list:
            method_decl = ast.get_subtree(method_node)
            for method_invoked in method_decl.get_proxy_nodes(
                    ASTNodeType.METHOD_INVOCATION):
                found_method_decl = method_declarations.get(method_invoked.member, [])
                # ignore overloaded functions
                if len(found_method_decl) == 1:
                    is_matched = is_match_to_the_conditions(ast, method_invoked, found_method_decl[0])

                    if is_matched:
                        results.append(
                            insert_code_with_new_file_creation(
                                class_declaration.name,
                                ast,
                                method_node,
                                method_invoked,
                                file_path,
                                output_path,
                                method_declarations
                            ))

    return results


if __name__ == '__main__':
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--dir", required=True, help="File path to JAVA source code for methods augmentations"
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
    args = parser.parse_args()

    test_files = set(Path(args.dir).glob('**/*Test*.java'))
    not_test_files = set(Path(args.dir).glob('**/*.java'))
    files_without_tests = list(not_test_files.difference(test_files))

    output_dir = Path(args.output)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    with open(Path(output_dir, 'out.csv'), 'w', newline='\n') as csvfile, ProcessPool(1) as executor:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            'Filename',
            'ClassName',
            'String where to replace',
            'line where to replace',
            'line of original function',
            'invocation function name',
            'unique id'])

        p_analyze = partial(analyze_file, output_path=output_dir.absolute())
        future = executor.map(p_analyze, files_without_tests, timeout=1000, )
        result = future.result()

        for filename in tqdm(files_without_tests):
            try:
                single_file_features = next(result)
                if single_file_features:
                    for i in single_file_features:
                        writer.writerow(i)
                csvfile.flush()
            except TimeoutError:
                print(f"Processing {filename} is aborted due to timeout in {args.timeout} seconds.")
            except Exception as e:
                print(str(e))
