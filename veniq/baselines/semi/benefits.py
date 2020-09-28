from collections import Counter, defaultdict
from typing import Tuple, Dict, List


def _check_is_common(
        dict_file: Dict[int, List[str]],
        statement_1: int,
        statement_2: int
) -> bool:
    '''
    This function is aimed to check whether 2 statements have
    common semantics or not.
    '''
    var_dict_1 = defaultdict(lambda: [], dict_file)[statement_1]
    var_dict_2 = defaultdict(lambda: [], dict_file)[statement_2]
    joined_names: Counter = Counter(var_dict_1 + var_dict_2)
    duplicates = {element: count for element, count in joined_names.items() if count > 1}.keys()
    return len(list(duplicates)) >= 1


def _LCOM2(
        line_to_semantic_dict: Dict[int, List[str]],
        range_statements: Tuple[int] = None,
        mode='original'
) -> int:
    '''
    LCOM_2 = P - Q;
    P is the number of pairs of statements
    that do not share variables and Q is the number
    of pairs of lines that share variables.

    line_to_semantic_dict is a map from line number
    to variables that are referenced there.
    range_statements is the range of lines for which LCOM2
    is calculated.
    '''
    P = 0
    Q = 0
    list_statements = []

    if mode == 'after_ref':
        list_statements = list(range(range_statements[0])) + list(range(range_statements[1] + 1,
                                                                        len(line_to_semantic_dict)))
    elif mode == 'opportunity':
        list_statements = list(range(range_statements[0], range_statements[1] + 1))
    else:
        list_statements = list(line_to_semantic_dict.keys())

    for stat_1 in list_statements:
        for stat_2 in list_statements:
            if stat_1 < stat_2:
                if _check_is_common(line_to_semantic_dict, stat_1, stat_2):
                    Q += 1
                else:
                    P += 1
    return P - Q


def _get_benefit(dict_semantic: Dict[int, List[str]], range_stats: Tuple[int, int]) -> int:
    original_value = _LCOM2(dict_semantic)
    opportunity_value = _LCOM2(dict_semantic, range_stats, 'opportunity')
    original_after_ref_value = _LCOM2(dict_semantic, range_stats, 'after_ref')
    return original_value - max(opportunity_value, original_after_ref_value)


def is_first_more_benefit(
        line_to_semantic_dict: Dict[int, List[str]],
        range_1: Tuple[int, int],
        range_2: Tuple[int, int],
        difference_threshold: float = 0.01,
        **kwargs
) -> bool:
    """
    Takes two opportunities and check if first opportunity
    is more benefit than the second one.
    """
    first_benefit = _get_benefit(line_to_semantic_dict, range_1)
    second_benefit = _get_benefit(line_to_semantic_dict, range_2)
    diff_between_benefits = abs(first_benefit - second_benefit) / \
        max(first_benefit, second_benefit)
    return diff_between_benefits >= difference_threshold
