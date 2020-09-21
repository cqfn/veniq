from itertools import combinations
from typing import List
import operator

MIN_OVERLAP = 0.1


def is_overlap(a: List[int], b: List[int]):
    """
    Checks whether 2 opportunities are overlapping

    :param a: array of 2 elements, the first is start statements number,
    the second is end statements number
    :param b: array of 2 elements, the first is start statements number,
    the second is end statements number

    :return: True if it is an overlap, False if it is not
    """

    a_LoC = abs(a[1] - a[0])
    b_LoC = abs(b[1] - b[0])
    overlap = len(set(range(a[0], a[1] + 1)) & set(range(b[0], b[1] + 1)))
    overlap_index = overlap / float(max(a_LoC, b_LoC))
    print(overlap_index)
    if overlap_index >= MIN_OVERLAP:
        return True
    else:
        return False
