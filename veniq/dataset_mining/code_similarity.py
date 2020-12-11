from collections import defaultdict
from typing import List, Tuple

import textdistance

from veniq.utils.encoding_detector import read_text_with_autodetected_encoding


def is_similar_functions(
        file_before: str,
        file_after: str,
        ranges_list_before: List[List[int]],
        ranges_list_after: Tuple[int, int]):
    d = defaultdict(set)
    before_lines_for_all_ranges = []
    exc = [' ', '{', '}', '']
    before_text = read_text_with_autodetected_encoding(file_before).split('\n')
    after_lines, start_after = get_after_lines(exc, file_after, ranges_list_after)
    for start_before, end_before in ranges_list_before:
        # since the beginning in array start with 0
        before_lines = [
            x.strip() for x in before_text[start_before - 1: end_before]
            if x.strip() not in exc]
        before_lines_for_all_ranges.extend(before_lines)

        for iteration_i, i in enumerate(after_lines, start=start_before):
            for iteration_j, j in enumerate(before_lines, start=start_after):
                longest_subs = textdistance.ratcliff_obershelp(i, j)
                hamm = textdistance.hamming.normalized_similarity(i, j)
                d[j].add((longest_subs, hamm, iteration_i, iteration_j, i))

    matched_strings_before: List[str] = []

    find_similar_strings(d, matched_strings_before)

    lines_number_of_function_before = 0
    for _ in before_lines_for_all_ranges:
        lines_number_of_function_before += 1

    if lines_number_of_function_before == 0:
        ratio = 0.0
    else:
        ratio = len(matched_strings_before) / float(lines_number_of_function_before)
    lines_number = lines_number_of_function_before
    lines_matched = len(matched_strings_before)
    matched_percent = ratio
    matched_strings = '\n'.join(matched_strings_before)

    if ratio > 0.699999:
        return lines_number, lines_matched, matched_percent, matched_strings, ratio, True

    return lines_number, lines_matched, matched_percent, matched_strings, ratio, True


def get_after_lines(
        exc: List[str],
        file_after: str,
        ranges_list_after: Tuple[int, int]) -> Tuple[List[str], int]:
    after_text = read_text_with_autodetected_encoding(file_after).split('\n')
    # since the beginning in array start with 0 and we
    # do not need the function's name which is usually on the first line
    start_after, end_after = ranges_list_after
    after_lines = [
        x.strip() for x in after_text[start_after: end_after]
        if x.strip() not in exc]
    return after_lines, start_after


def find_similar_strings(d, matched_strings_before):
    for string_before, lst in d.items():
        max_val = -1
        max_hamm = -1
        for subs_val, hamm, iterator_i, iteration_j, string_matched in lst:
            if max_val < subs_val:
                max_val = subs_val
                max_hamm = hamm

        if max_val > 0.7000000000000000000000000000000000000000001:
            if max_hamm > 0.4:
                matched_strings_before.append(string_before)
