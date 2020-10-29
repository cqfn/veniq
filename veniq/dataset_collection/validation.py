import os
from argparse import ArgumentParser
from collections import namedtuple
from functools import partial
from pathlib import Path
from typing import Tuple, List
import traceback
import pandas as pd
from numpy import mean
from pebble import ProcessPool
from tqdm import tqdm

from metrics.ncss.ncss import NCSSMetric
from veniq.baselines.semi.create_extraction_opportunities import create_extraction_opportunities
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.baselines.semi.filter_extraction_opportunities import filter_extraction_opportunities
from veniq.baselines.semi.rank_extraction_opportunities import rank_extraction_opportunities
from veniq.dataset_collection.augmentation import method_body_lines
from veniq.utils.ast_builder import build_ast
from veniq.ast_framework import AST, ASTNodeType
from random import choice

from dataclasses import make_dataclass as md, dataclass, asdict


def find_extraction_opportunities(
        method_ast: AST):
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
class MatchedResult:
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


def validate_row(dataset_dir: Path, row: pd.Series) \
        -> List[MatchedResult]:
    """
    Validate row of dataset

    :param dataset_dir: directory to dataset, path before the relative path in
    output_filename
    :param row: row of dataframe
    :return: boolean value whether we should consider this row or skip it,
    Stats - return collected stats
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
            # class_ast = ast.get_subtree(class_decl)
            if class_decl.name != class_name:
                continue
            elif class_decl.name == class_name:
                objects_to_consider = list(class_decl.methods) + list(class_decl.constructors) or []
                for ast_node in objects_to_consider:
                    result = MatchedResult(
                        output_filename=full_path,
                        input_filename=row[1]['input_filename'],
                        class_name='',
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
                            best_group = opport[0]
                            lines = [node.line for node in best_group._optimal_opportunity]
                            start_line_opportunity = min(lines)
                            end_line_opportunity = max(lines)
                            dataset_range_extraction = range(start_line_of_inserted_block, end_line_of_inserted_block)
                            lines_intersected = set(dataset_range_extraction) & set(lines)
                            result.class_name = class_decl.name
                            result.method_name = ast_node.name
                            result.start_line_SEMI = start_line_opportunity
                            result.end_line_SEMI = end_line_opportunity
                            result.ncss = NCSSMetric().value(ast_subtree)

                            if (start_line_of_inserted_block == start_line_opportunity) \
                                    and (end_line_of_inserted_block == end_line_opportunity):
                                result.matched = True

                            result.percent_matched = float(len(lines_intersected)) / len(dataset_range_extraction)
                        else:
                            result.no_opportunity_chosen = True
                            # print(class_decl.name, method_decl.name)

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

    # print(dataset_dir / src_filename)
    return results


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--dataset_dir",
        help="Path for file with output results",
        required=True
    )
    parser.add_argument(
        "-i", "--csv_input",
        help="Path for csv"
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

    output_df = pd.DataFrame(columns=list(MatchedResult.__annotations__.keys()))

    with ProcessPool(system_cores_qty) as executor:
        validate_row_f = partial(validate_row, dataset_dir)
        future = executor.map(validate_row_f, df.iterrows(), timeout=10000, )
        result = future.result()
        for index, row in tqdm(df.iterrows()):
            try:
                # print(row['input_filename'])
                results: List[MatchedResult] = next(result)
                for res in results:
                    output_df = output_df.append(asdict(res), ignore_index=True)
                output_df.to_csv('matched.csv')
            except Exception as e:
                # print(f"Exception inside thread happened: {str(e)}")
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
    total_case_handled = output_df.shape[0] - \
                   failed_cases_in_SEMI_algorithm - \
                   failed_cases_in_validation_examples
    if total_case_handled > 0:
        result = matched_cases / total_case_handled
        print(f'Matched {result}% of cases, {matched_cases} out of {total_case_handled}')
