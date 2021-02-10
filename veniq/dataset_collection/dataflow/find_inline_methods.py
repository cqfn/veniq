from collections import defaultdict
from typing import Dict, List

from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.dataset_collection.augmentation import collect_info_about_functions_without_params
from javalang.parse import parse


def find_EMS(dct):
    text: str = dct['text']
    try:
        ast = AST.build_from_javalang(parse(text))
        classes_declaration = [
            ast.get_subtree(node)
            for node in ast.get_root().types
            if node.node_type == ASTNodeType.CLASS_DECLARATION
        ]
        method_declarations: Dict[str, List[ASTNode]] = defaultdict(list)
        for class_ast in classes_declaration:
            class_declaration = class_ast.get_root()
            collect_info_about_functions_without_params(class_declaration, method_declarations)

            methods_list = list(class_declaration.methods) + list(class_declaration.constructors)
            for method_node in methods_list:
                target_node = ast.get_subtree(method_node)
                for method_invoked in target_node.get_proxy_nodes(
                        ASTNodeType.METHOD_INVOCATION):
                    extracted_m_decl = method_declarations.get(method_invoked.member, [])
                    if len(extracted_m_decl) == 1:
                        t = tuple([class_declaration.name, method_invoked.line])
                        yield {t: tuple([ast, text, target_node, method_invoked, extracted_m_decl[0]])}
    except Exception as e:
        print(str(e))
