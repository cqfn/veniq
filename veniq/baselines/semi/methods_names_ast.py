from typing import Dict, List
from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.utils.ast_builder import build_ast
from argparse import ArgumentParser


def methods_ast_and_class_name(filepath: str, args_class_name=None, args_method_name=None) -> Dict[int, List[str]]:
    ast = AST.build_from_javalang(build_ast(filepath))
    classes_declarations = (
        node for node in ast.get_root().types
        if node.node_type == ASTNodeType.CLASS_DECLARATION
    )

    if args_class_name is not None:
        classes_declarations = (
            node for node in classes_declarations if node.name == args_class_name
        )

    methods_declarations = (
        method_declaration for class_declaration in classes_declarations
        for method_declaration in class_declaration.methods
    )

    if args_method_name is not None:
        methods_declarations = (
            method_declaration for method_declaration in methods_declarations
            if method_declaration.name == args_method_name
        )

    methods_ast_and_class_name = (
        (ast.get_subtree(method_declaration), method_declaration.parent.name)
        for method_declaration in methods_declarations
    )

    return methods_ast_and_class_name

if __name__ == '__main__':
    parser = ArgumentParser(description="Extracts semantic from specified methods")
    parser.add_argument("-f", "--file", required=True,
                        help="File path to JAVA source code for extracting semantic")
    parser.add_argument("-c", "--class", default=None, dest="class_name",
                        help="Class name of method to parse, if omitted all classes are considered")
    parser.add_argument("-m", "--method", default=None, dest="method_name",
                        help="Method name to parse, if omitted all method are considered")

    args = parser.parse_args()


    for i, j in methods_ast_and_class_name(args.file, args.class_name. args.method_name):
        print(i, j)