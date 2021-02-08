from collections import defaultdict
from typing import List, Dict

import d6tcollect
import d6tflow
# from veniq.dataset_collection.augmentation import InvocationType
from joblib import Parallel, delayed

from veniq.ast_framework import AST
from veniq.ast_framework import ASTNodeType, ASTNode
from veniq.dataset_collection.augmentation import collect_info_about_functions_without_params
from veniq.dataset_collection.dataflow.preprocess import TaskAggregatorJavaFiles
from veniq.utils.ast_builder import build_ast

d6tcollect.submit = False


@d6tflow.requires({'csv': TaskAggregatorJavaFiles})
class TaskFindEM(d6tflow.tasks.TaskCache):
    dir_to_search = d6tflow.Parameter()
    dir_to_save = d6tflow.Parameter()
    system_cores_qty = d6tflow.IntParameter()

    def _find_EMs(self, row):
        result_dict = {}
        try:
            ast = AST.build_from_javalang(build_ast(row['original_filename']))
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
                            result_dict[method_invoked.line] = [target_node, method_invoked, extracted_m_decl]
            # print({'em_list': result_dict, 'ast': ast})
            if result_dict:
                print(f' FFF {result_dict}')
                return [{'em_list': result_dict, 'ast': ast}]
            else:
                return {}
        except Exception:
            pass

        return {}

    def run(self):
        csv = self.inputLoad()['csv']
        rows = [x for _, x in csv.iterrows()]

        with Parallel(n_jobs=2, require='sharedmem') as parallel:
            results = parallel((delayed(self._find_EMs)(a) for a in rows))
        self.save({"data": [x for x in results if x]})
