from argparse import ArgumentParser
from typing import Callable, NamedTuple

from veniq.ast_framework import AST, ASTNodeType
from veniq.utils.ast_builder import build_ast

# Main function parameters:
#  - AST of a single method
#  - path of file with source code
#  - class name
#  - method name
MainFunction = Callable[[AST, str, str, str], None]


class MethodInfo(NamedTuple):
    ast: AST
    method_name: str
    class_name: str


def common_cli(main: MainFunction, description: str) -> None:
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "-f", "--file", required=True, help="File path to JAVA source code for extracting semantic"
    )
    parser.add_argument(
        "-c",
        "--class",
        default=None,
        dest="class_name",
        help="Class name of method to parse, if omitted all classes are considered",
    )
    parser.add_argument(
        "-m",
        "--method",
        default=None,
        dest="method_name",
        help="Method name to parse, if omitted all method are considered",
    )
    args = parser.parse_args()

    ast = AST.build_from_javalang(build_ast(args.file))

    classes_declarations = (
        node for node in ast.get_root().types if node.node_type == ASTNodeType.CLASS_DECLARATION
    )

    if args.class_name is not None:
        classes_declarations = (node for node in classes_declarations if node.name == args.class_name)

    methods_infos = (
        MethodInfo(
            ast=ast.get_subtree(method_declaration),
            method_name=method_declaration.name,
            class_name=class_declaration.name,
        )
        for class_declaration in classes_declarations
        for method_declaration in class_declaration.methods
    )

    if args.method_name is not None:
        methods_infos = (
            method_info for method_info in methods_infos if method_info.method_name == args.method_name
        )

    for method_info in methods_infos:
        main(method_info.ast, args.file, method_info.class_name, method_info.method_name)
