from argparse import ArgumentParser
import os
from typing import Tuple, Dict, Union

from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.utils.ast_builder import build_ast



def _get_last_line(child_statement: ASTNode) -> int:
    '''
    This function is aimed to find the last line of
    the all childrens and childerns of childrens
    for a chosen statement.
    Main goal is to get the last line of method. 
    '''
    last_line = child_statement.line
    if hasattr(child_statement, 'children'):
        for children in child_statement.children:
            if children.line >= last_line:
                last_line = _get_last_line(children)
    return last_line


def _method_body_lines(method_node: ASTNode, file_path: str) -> Tuple[int, int]:
    '''
    Ger start and end of method's body
    '''
    method_all_childs = list(method_node.children)[-1]
    if len(method_node.body):
        start_line = method_node.body[0].line
        end_line = _get_last_line(method_all_childs)
    return (start_line, end_line)


def _get_method_lines_dict(classes_declaration: ASTNode) -> Dict[ASTNode, Dict[str, Tuple[int, int]]]:
    '''
    This method is aimed to process each class, 
    also for each class to process all it's methods.
    Find starting and end lines of each method's body.
    And finally to store it into dictionary.
    '''
    dictionary = {}
    for classes_declaration_node in classes_declaration:
        for method_node in classes_declaration_node.methods:
            lines = _method_body_lines(method_node, args.file)
            if not dictionary.get(method_node):
                dictionary[method_node] = {classes_declaration_node.name: lines}
            elif not dictionary[method_node].get(classes_declaration_node).name:
                dictionary[method_node][classes_declaration_node.name] = lines
    return dictionary


def _get_method_node_of_invocated(
    invocated_method_node: ASTNode,
    dict_method_lines: Dict
    ) -> Union[ASTNode, None]:
    '''
    To find method node of class by
    its invoced version in the other one method.
    '''
    for method_node in dict_method_lines:
        if invocated_method_node.member == method_node.name:
            return method_node
    return None


def _process_invocations_inside(
    method_node: ASTNode,
    file_path,
    dict_method_lines
    ):
    '''
    To process each class's method in order to find 
    its invocation inside and also process them.
    '''
    file_ast = AST.build_from_javalang(build_ast(args.file))
    method_ast = file_ast.get_subtree(method_node)
    for method_invoce in method_ast.get_proxy_nodes(ASTNodeType.METHOD_INVOCATION):
        is_invocated_also_method_class = _get_method_node_of_invocated(
            method_invoce, dict_method_lines) is not None

        if is_invocated_also_method_class and method_invoce.member != method_node.name:
            _create_new_files(method_node, method_invoce, file_path, dict_method_lines)


def _create_new_files(
    method_node: ASTNode,
    invocation_node: ASTNode,
    file_path: str,
    dict_method_lines: Dict
    ) -> None:
    '''
    If invocations of class's methods were found,
    we process through all of them and for each
    substitution opportunity by method's body, 
    we creat new file.
    '''
    file_name = file_path.replace('\\', '/').split('/')[-1].split('.java')[0]
    new_data_path = 'augmentated_data/'
    if not os.path.exists(new_data_path):
        os.mkdir(new_data_path)

    new_file_path = f'{new_data_path}{file_name}_{method_node.name}.java'
    f = open(new_file_path, 'w')
    original_file = open(file_path)

    method_node_invoced = _get_method_node_of_invocated(invocation_node, dict_method_lines)
    method_lines = method_node_invoced.line
    class_method_lines = dict_method_lines[method_node_invoced][method_node.parent.name]
    lines = list(original_file)

    # original code before method invocation, which will be substituted
    lines_to_write = lines[:invocation_node.line - 1]
    # body of the original method, which will be inserted
    lines_to_write += lines[class_method_lines[0] - 1:class_method_lines[1]]
    # original code after method invocation
    lines_to_write += lines[invocation_node.line:]
    for i in lines_to_write:
        f.write(i)

    method_params = lines[method_lines - 1: method_lines]
    invocated_method_params = lines[invocation_node.line - 1: invocation_node.line]
    print(method_params)
    print(invocated_method_params,'\n')


def main(file_path: str) -> None:
    ast = AST.build_from_javalang(build_ast(file_path))
    classes_declaration = [
        node for node in ast.get_root().types if node.node_type == ASTNodeType.CLASS_DECLARATION
    ]

    dict_method_lines = _get_method_lines_dict(classes_declaration)
    for classes_declaration_node in classes_declaration:
        for method_node in classes_declaration_node.methods:
            _process_invocations_inside(method_node, file_path, dict_method_lines)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "-f", "--file", required=True, help="File path to JAVA source code for methods augmentations"
    )
    args = parser.parse_args()
    main(args.file)
