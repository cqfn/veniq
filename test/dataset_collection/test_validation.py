from typing import Dict, Tuple

from pandas import DataFrame


def semi_approach(
        file: str):
    # [Class.function [start line, end line of extraction]]
    # HTMLLoader.runExecute = [[6, 9], [10, 15]]] -> we extracted from 6th up to 9th line,
    # from 10th up to 15th line
    # HTMLLoader.doNothing = [[6, 7]] -> we extracted from 6th up to 7th line

    return Dict[str, Tuple[int, int]]


def validation(csv: DataFrame) -> float:
    matched_score = 0
    total_opportunities_number = 0
    for row in csv.iterrows():
        original_filename = row['original_filename']
        d = semi_approach(original_filename)
        extracted_start_line = row['extracted_start_line']
        extracted_end_line = row['extracted_end_line']
        true_opportunity = Tuple[extracted_start_line, extracted_end_line]
        for function, list_opportunities in d.items():
            for opportunity in list_opportunities:
                total_opportunities_number += 1
                if opportunity == true_opportunity:
                    matched_score += 1

    return total_opportunities_number / float(matched_score)
