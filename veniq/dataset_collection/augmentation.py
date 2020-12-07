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
        ASTNodeType.IF_STATEMENT,
        ASTNodeType.WHILE_STATEMENT,
        ASTNodeType.FOR_STATEMENT,
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
    is_not_at_the_same_line_as_prohibited_stats = check_nesting_statements(method_invoked)
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
        is_not_at_the_same_line_as_prohibited_stats,
        not method_invoked.arguments])

    if (not method_invoked.qualifier and other_requirements) or \
            (method_invoked.qualifier == 'this' and other_requirements):
        return True
    else:
        return False


def check_whether_method_has_return_type(
        method_decl: AST,
        var_decls: Set[str]) -> InlineTypesAlgorithms:
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
        dict_original_invocations: Dict[str, List[ASTNode]],
        source_filepath: str
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
    ncss = NCSSMetric().value(ast.get_subtree(original_func))
    line_to_csv = {}
    # @acheshkov asked to consider only methods with ncss > 3, that's all.
    if ncss > 3:
        body_start_line, body_end_line = method_body_lines(original_func, file_path)
        text_lines = read_text_with_autodetected_encoding(str(file_path)).split('\n')
        # we do not inline one-line methods like
        # public String getRemainingString() {return str.substring(index);}
        if body_start_line != body_end_line:
            algorithm_type = determine_algorithm_insertion_type(
                ast,
                method_node,
                invocation_node,
                dict_original_invocations
            )
            algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
            if algorithm_type != InlineTypesAlgorithms.DO_NOTHING:
                line_to_csv = {
                    'project': source_filepath,
                    'input_filename': file_path,
                    'class_name': class_name,
                    'invocation_text_string': text_lines[invocation_node.line - 1].lstrip(),
                    'method_where_invocation_occurred': method_node.name,
                    'invocation_method_name': original_func.name,
                    'output_filename': new_full_filename
                }

                inline_method_bounds = algorithm_for_inlining().inline_function(
                    file_path,
                    invocation_node.line,
                    body_start_line,
                    body_end_line,
                    new_full_filename,
                )
                if inline_method_bounds is not None:
                    line_to_csv['inline_insertion_line_start'] = inline_method_bounds[0]
                    line_to_csv['inline_insertion_line_end'] = inline_method_bounds[1]

                    if get_ast_if_possible(new_full_filename):
                        rest_of_csv_row_for_changed_file = find_lines_in_changed_file(
                            class_name=class_name,
                            method_node=method_node,
                            new_full_filename=new_full_filename,
                            original_func=original_func)

                        can_be_parsed = True
                        line_to_csv.update(rest_of_csv_row_for_changed_file)
                    else:
                        can_be_parsed = False

                    line_to_csv['can_be_parsed'] = can_be_parsed

    return line_to_csv


# type: ignore
def find_lines_in_changed_file(
        new_full_filename: Path,
        method_node: ASTNode,
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
        class_subtree = changed_ast.get_subtree(class_node_of_changed_file)
        node = [x for x in class_subtree.get_proxy_nodes(
            ASTNodeType.METHOD_DECLARATION,
            ASTNodeType.CONSTRUCTOR_DECLARATION)
            if x.name == method_node.name][0]  # type: ignore
        original_func_changed = [x for x in class_subtree.get_proxy_nodes(
            ASTNodeType.METHOD_DECLARATION) if x.name == original_func.name][0]

        body_start_line, body_end_line = method_body_lines(original_func_changed, new_full_filename)
        return {
            'invocation_method_start_line': body_start_line,
            'invocation_method_end_line': body_end_line,
            'start_line_of_function_where_invocation_occurred': node.line
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


def analyze_file(
        file_path: Path,
        output_path: Path,
        input_dir: Path
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
        collect_info_about_functions_without_params(class_declaration, method_declarations)

        methods_list = list(class_declaration.methods) + list(class_declaration.constructors)
        for method_node in methods_list:
            method_decl = ast.get_subtree(method_node)
            for method_invoked in method_decl.get_proxy_nodes(
                    ASTNodeType.METHOD_INVOCATION):
                found_method_decl = method_declarations.get(method_invoked.member, [])
                # ignore overloaded functions
                if len(found_method_decl) == 1:
                    try:
                        make_insertion(
                            ast,
                            class_declaration,
                            dst_filename,
                            found_method_decl,
                            method_declarations,
                            method_invoked,
                            method_node,
                            output_path,
                            file_path,
                            results
                        )
                    except Exception as e:
                        print('Error has happened during file analyze: ' + str(e))

    if not results:
        dst_filename.unlink()

    return results


def make_insertion(ast, class_declaration, dst_filename, found_method_decl, method_declarations, method_invoked,
                   method_node, output_path, source_filepath, results):
    is_matched = is_match_to_the_conditions(
        ast,
        method_invoked,
        found_method_decl[0]
    )
    if is_matched:
        log_of_inline = insert_code_with_new_file_creation(
            class_declaration.name,
            ast,
            method_node,
            method_invoked,
            dst_filename,
            output_path,
            method_declarations,
            source_filepath)
        if log_of_inline:
            # change source filename, since it will be changed
            log_of_inline['input_filename'] = str(dst_filename.as_posix())
            results.append(log_of_inline)


def collect_info_about_functions_without_params(
        class_declaration: ASTNode,
        method_declarations: Dict[str, List[ASTNode]]) -> None:
    for method in class_declaration.methods:
        if not method.parameters:
            method_declarations[method.name].append(method)

# def save_input_file(input_dir: Path, filename: Path) -> Path:
#     # need to avoid situation when filenames are the same
#     hash_path = hashlib.sha256(str(filename.parent).encode('utf-8')).hexdigest()
#     dst_filename = input_dir / f'{filename.stem}_{hash_path}.java'
#     if not dst_filename.parent.exists():
#         dst_filename.parent.mkdir(parents=True)
#     if not dst_filename.exists():
#         shutil.copyfile(filename, dst_filename)
#     return dst_filename


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

    df = pd.DataFrame(
        columns=[
            'project',
            'input_filename',
            'class_name',
            'invocation_text_string',
            'method_where_invocation_occurred',
            'start_line_of_function_where_invocation_occurred',
            'invocation_method_name',
            'invocation_method_start_line',
            'invocation_method_end_line',
            'output_filename',
            'can_be_parsed',
            'inline_insertion_line_start',
            'inline_insertion_line_end'
        ])

    with ProcessPool(system_cores_qty) as executor:
        p_analyze = partial(
            analyze_file,
            output_path=output_dir.absolute(),
            input_dir=input_dir
        )
        future = executor.map(p_analyze, files_without_tests, timeout=1000, )
        result = future.result()

        # each 100 cycles we dump the results
        iteration_cycle = 1000
        iteration_number = 0
        for filename in tqdm(files_without_tests):
            try:
                single_file_features = next(result)
                if single_file_features:
                    for i in single_file_features:
                        #  get local path for inlined filename
                        i['output_filename'] = i['output_filename'].relative_to(os.getcwd()).as_posix()
                        print(i['output_filename'], filename)
                        i['invocation_text_string'] = str(i['invocation_text_string']).encode('utf8')
                        df = df.append(i, ignore_index=True)

                if (iteration_number % iteration_cycle) == 0:
                    df.to_csv(csv_output)
                iteration_number += 1
            except Exception as e:
                print(str(e))

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
            input_filename = row['input_filename']
            dst_filename = small_input_dir / Path(input_filename).name
            shutil.copyfile(input_filename, dst_filename)
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
