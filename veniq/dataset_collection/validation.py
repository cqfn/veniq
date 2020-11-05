import os
import traceback
from argparse import ArgumentParser
from dataclasses import dataclass, asdict
from functools import partial
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from numpy import mean
from pebble import ProcessPool
from tqdm import tqdm

from veniq.ast_framework import AST, ASTNodeType
from veniq.ast_framework import ASTNode
from veniq.baselines.semi.create_extraction_opportunities import create_extraction_opportunities
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.baselines.semi.filter_extraction_opportunities import filter_extraction_opportunities
from veniq.baselines.semi.rank_extraction_opportunities import rank_extraction_opportunities, ExtractionOpportunityGroup
from veniq.metrics.ncss.ncss import NCSSMetric
from veniq.utils.ast_builder import build_ast
from veniq.utils.encoding_detector import read_text_with_autodetected_encoding


def find_extraction_opportunities(
        method_ast: AST) -> List[ExtractionOpportunityGroup]:
    statements_semantic = extract_method_statements_semantic(method_ast)
    extraction_opportunities = create_extraction_opportunities(statements_semantic)
    filtered_extraction_opportunities = filter_extraction_opportunities(
        extraction_opportunities, statements_semantic, method_ast
    )
    extraction_opportunities_groups = rank_extraction_opportunities(
        statements_semantic, filtered_extraction_opportunities
    )

    return extraction_opportunities_groups


@dataclass
class RowResult:
    output_filename: str
    input_filename: str
    start_line_SEMI: int
    end_line_SEMI: int
    start_line_dataset: int
    end_line_dataset: int
    percent_matched: float
    class_name: str
    method_name: str
    error_string: str
    ncss: int
    matched: bool
    failed_cases_in_SEMI_algorithm: bool
    no_opportunity_chosen: bool
    failed_cases_in_validation_examples: bool


def fix_start_end_lines_for_opportunity(
        extracted_lines_of_opportunity: List[int],
        filepath: str) -> Tuple[int, int]:
    """
    Finds start and end lines for opportunity

    :param filepath: filename where opportunity was found
    :param extracted_lines_of_opportunity: list of lines for opportunity
    :return: list of extracted lines for opportunity
    """
    start_line_opportunity = min(extracted_lines_of_opportunity)
    end_line_opportunity = max(extracted_lines_of_opportunity)
    text = read_text_with_autodetected_encoding(filepath).split('\n')

    extraction = text[start_line_opportunity - 1:end_line_opportunity]
    open_brackets = 0
    close_brackets = 0
    for x in extraction:
        close_brackets += x.count('}')
        open_brackets += x.count('{')

    if open_brackets < close_brackets:
        diff = close_brackets - open_brackets
        count = 1
        for text_line in text[end_line_opportunity:]:
            while diff > 0:
                if text_line.find('{') > -1:
                    diff -= 1
                    count += 1

        start_line_opportunity += count - 1

    elif open_brackets > close_brackets:
        diff = open_brackets - close_brackets
        count = 1
        for text_line in text[end_line_opportunity:]:
            while diff > 0:
                if text_line.find('}') > -1:
                    diff -= 1
                    count += 1

        end_line_opportunity += count - 1

    return start_line_opportunity, end_line_opportunity


# flake8: noqa: C901
def validate_row(dataset_dir: Path, row: pd.Series) \
        -> List[RowResult]:
    """
    Validate row of dataset

    :param dataset_dir: directory to dataset, path before the relative path in
    output_filename
    :param row: row of dataframe of synth validation dataset
    :return: Stats - return collected stats
    """
    results = []
    try:
        start_line_of_inserted_block = int(row[1]['inline_insertion_line_start'])
        end_line_of_inserted_block = int(row[1]['inline_insertion_line_end'])

        src_filename = row[1]['output_filename']
        class_name = row[1]['class_name']
        full_path = dataset_dir / src_filename
        ast = AST.build_from_javalang(build_ast(full_path))
        function_to_analyze = row[1]['method_where_invocation_occurred']

        for class_decl in ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION):
            if class_decl.name == class_name:
                objects_to_consider = list(class_decl.methods) + list(class_decl.constructors) or []
                for ast_node in objects_to_consider:
                    result = RowResult(
                        output_filename=full_path,
                        input_filename=row[1]['input_filename'],
                        class_name='Not available',
                        method_name='',
                        start_line_SEMI=-1,
                        end_line_SEMI=-1,
                        start_line_dataset=start_line_of_inserted_block,
                        end_line_dataset=end_line_of_inserted_block,
                        percent_matched=-1.0,
                        error_string='',
                        ncss=0,
                        matched=False,
                        failed_cases_in_SEMI_algorithm=False,
                        no_opportunity_chosen=False,
                        failed_cases_in_validation_examples=False,
                    )
                    if ast_node.name != function_to_analyze:
                        continue
                    try:
                        ast_subtree = ast.get_subtree(ast_node)
                        opport = find_extraction_opportunities(ast_subtree)
                        if opport:
                            find_matched_lines(
                                ast_node,
                                ast_subtree,
                                class_decl,
                                start_line_of_inserted_block,
                                end_line_of_inserted_block,
                                full_path,
                                opport,
                                result)
                        else:
                            result.no_opportunity_chosen = True

                    except Exception as e:
                        traceback.print_exc()
                        result.error_string = str(e)
                        result.failed_cases_in_SEMI_algorithm = True
                    finally:
                        results.append(result)

                    break
                break

    except Exception as e:
        traceback.print_exc()
        result.error_string = str(e)
        result.failed_cases_in_validation_examples = True
        results.append(result)

    return results


def find_matched_lines(
        ast_node: ASTNode,
        ast_subtree: AST,
        class_decl: ASTNode,
        start_line_of_inserted_block: int,
        end_line_of_inserted_block: int,
        full_path: str,
        opportunities_list: List[ExtractionOpportunityGroup],
        result: RowResult) -> None:

    best_group = opportunities_list[0]
    lines = [node.line for node in best_group._optimal_opportunity]
    fixed_lines = fix_start_end_lines_for_opportunity(
        lines,
        full_path
    )
    start_line_opportunity = min(fixed_lines)
    end_line_opportunity = max(fixed_lines)
    dataset_range_extraction = range(
        start_line_of_inserted_block,
        end_line_of_inserted_block + 1
    )
    result.class_name = class_decl.name
    result.method_name = ast_node.name
    result.start_line_SEMI = start_line_opportunity
    result.end_line_SEMI = end_line_opportunity
    result.ncss = NCSSMetric().value(ast_subtree)
    if (start_line_of_inserted_block == start_line_opportunity) \
            and (end_line_of_inserted_block == end_line_opportunity):
        result.matched = True
    result.percent_matched = percent_matched(dataset_range_extraction, fixed_lines)


def percent_matched(dataset_range_lines, semi_range_lines):
    lines_intersected = set(dataset_range_lines) & set(semi_range_lines)
    return float(len(lines_intersected)) / len(set(dataset_range_lines))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--dataset_dir",
        help="Path for file with output results",
        required=True
    )
    parser.add_argument(
        "-i", "--csv_input",
        help="Path for csv with synth dataset"
    )
    system_cores_qty = os.cpu_count() or 1
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=system_cores_qty - 1,
        help="Number of processes to spawn. "
             "By default one less than number of cores. "
             "Be careful to raise it above, machine may stop responding while creating dataset.",
    )
    args = parser.parse_args()
    dataset_dir = Path(args.dataset_dir)
    csv_dataset_filename = Path(args.csv_input)
    df = pd.read_csv(csv_dataset_filename)
    df = df[df['can_be_parsed']]

    output_df = pd.DataFrame(columns=list(RowResult.__annotations__.keys()))

    with ProcessPool(1) as executor:
        validate_row_f = partial(validate_row, dataset_dir)
        future = executor.map(validate_row_f, df.iterrows(), timeout=10000, )
        result = future.result()
        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            try:
                results: List[RowResult] = next(result)
                for res in results:
                    output_df = output_df.append(asdict(res), ignore_index=True)
                output_df.to_csv('matched.csv')
            except Exception:
                print(traceback.format_exc())
                continue

    matched_cases = float(output_df[output_df["matched"]].shape[0])
    failed_cases_in_SEMI_algorithm = output_df[output_df["failed_cases_in_SEMI_algorithm"]].shape[0]
    failed_cases_in_validation_examples = output_df[output_df["failed_cases_in_validation_examples"]].shape[0]
    no_opportunity_chosen = output_df[output_df["no_opportunity_chosen"]].shape[0]
    matched_percent = mean(output_df[output_df["percent_matched"] > 0].percent_matched.values)
    print(f'Failed SEMI algorithm errors: {failed_cases_in_SEMI_algorithm}')
    print(f'Failed examples of synth dataset: {failed_cases_in_validation_examples}')
    print(f'matched_cases: {matched_cases}')
    print(f'No opportunity chosen: {no_opportunity_chosen} times')
    print(f'Total number of handled cases: {output_df.shape[0]}')
    print(f'Average of matched lines: {matched_percent}')
    total_case_handled = output_df.shape[0] - failed_cases_in_SEMI_algorithm - failed_cases_in_validation_examples
    if total_case_handled > 0:
        result = matched_cases / total_case_handled
        print(f'Matched {result}% of cases, {matched_cases} out of {total_case_handled}')
