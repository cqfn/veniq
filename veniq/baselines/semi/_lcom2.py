from typing import Dict
from itertools import combinations

from ._common_types import Statement, StatementSemantic


def LCOM2(statements_semantic: Dict[Statement, StatementSemantic]) -> int:
    similar_pairs_qty = 0
    not_similar_pairs_qty = 0
    for semantic1, semantic2 in combinations(statements_semantic.values(), 2):
        if semantic1.is_similar(semantic2):
            similar_pairs_qty += 1
        else:
            not_similar_pairs_qty += 1

    lcom2 = not_similar_pairs_qty - similar_pairs_qty
    if lcom2 < 0:
        lcom2 = 0

    return lcom2
