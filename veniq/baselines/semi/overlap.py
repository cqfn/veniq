from typing import List


def is_overlap(a: Tuple[int, int], b: Tuple[int, int], min_overlap: float=0.1) -> bool:
    """
    Checks whether 2 opportunities are overlapped

    :param a: array of 2 elements, the first is start statements number,
    the second is end statements number
    :param b: array of 2 elements, the first is start statements number,
    the second is end statements number
    :param min_overlap: min accepted value
    :return: True if it is an overlap, False if it is not
    """

    a_LoC = abs(a[1] + 1 - a[0])
    b_LoC = abs(b[1] + 1 - b[0])
    overlap = len(set(range(a[0], a[1] + 1)) & set(range(b[0], b[1] + 1)))
    overlap_index = overlap / float(max(a_LoC, b_LoC))
    return overlap_index >= min_overlap
