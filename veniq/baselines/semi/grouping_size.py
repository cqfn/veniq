from typing import Tuple


def is_similar_size(range_1: Tuple[int, int],
                    range_2: Tuple[int, int],
                    max_size_difference: float = 0.2) -> bool:
    """
    Takes two opportunities and check if they are similar in size.
    Default value of max_size_difference is from the originl paper.
    """
    loc_1 = range_1[1] - range_1[0] + 1
    loc_2 = range_2[1] - range_2[0] + 1
    return abs(loc_1 - loc_2) / min(loc_1, loc_2) <= max_size_difference
