from typing import List, Dict

from aibolit.ast_framework import ASTNode
from aibolit.extract_method_baseline.extract_semantic import \
                                        StatementSemantic


def _reprocess_dict(method_semantic: Dict[ASTNode, StatementSemantic]) -> Dict[int, List[str]]:
    """
    Auxilary method that converts data structure obtained
    from clustering and filtering
    into a dictionary from line number to a list of variables that
    are referenced in that line.
    """
    reprocessed_dict = dict()
    for statement in method_semantic.keys():
        new_values = []
        new_values += list(method_semantic[statement].used_variables)
        new_values += list(method_semantic[statement].used_objects)
        new_values += list(method_semantic[statement].used_methods)
        reprocessed_dict[statement.line] = new_values
    return reprocessed_dict
