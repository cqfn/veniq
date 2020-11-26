from collections import defaultdict
from typing import List

import textdistance

files = [
    ('EduStepicConnector', [142, 153], [159, 171]),
    ('FixedMembershipToken', [55, 88], [73, 82])
]


def is_similar_functions(
        file_before: str,
        file_after: str,
        ranges_before: List[int],
        ranges_after: List[int]):
    d = defaultdict(set)
    exc = [' ', '{', '}', '']
    with open(file_before) as before:
        before_text = before.read().split('\n')
        start_before, end_before = ranges_before
        before_lines = before_text[start_before: end_before]
        with open(file_after) as after:
            start_after, end_after = ranges_after
            after_lines = after.read().split('\n')[start_after: end_after]

            for iteration_i, i in enumerate(after_lines, start=start_before):
                for iteration_j, j in enumerate(before_lines, start=start_after):
                    i = i.strip()
                    j = j.strip()
                    if (i != '') and (j != '') and (i not in exc) and (j not in exc):
                        longest_subs = textdistance.ratcliff_obershelp(i, j)
                        hamm = textdistance.hamming.normalized_similarity(i, j)
                        d[j].add((longest_subs, hamm, iteration_i, iteration_j, i))

        matched_strings_before = []

        find_similar_strings(d, matched_strings_before)

    lines_number_of_function_before = 0
    for i in before_lines:
        if i.strip() not in exc:
            lines_number_of_function_before += 1

    ratio = len(matched_strings_before) / float(lines_number_of_function_before)
    if ratio > 0.700000000000000000000000000000001:
        return True

    return False


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
