import os
import traceback
from argparse import ArgumentParser
from ast import literal_eval
from pathlib import Path

import pandas as pd
from pebble import ProcessPool
from tqdm import tqdm

from veniq.ast_framework import AST
from veniq.ast_framework import ASTNodeType
from veniq.dataset_collection.augmentation import method_body_lines
from veniq.dataset_mining.code_similarity import is_similar_functions, get_after_lines
from veniq.utils.ast_builder import build_ast


def calculate_additional_similarity(row: pd.Series):
    target_function_name = row['function_name_with_LM']
    # real_extractions = row['real_extractions']
    class_name = row['class_name']
    filepath_after = str(csv_output / row['filepath_saved'])
    filepath_before = filepath_after.replace('_after.java', '_before.java')
    # extracted_function_name = row['function_inlined']
    function_target_start_line = row['function_target_start_line']
    function_target_end_line = row['function_target_end_line']
    ast_after = AST.build_from_javalang(build_ast(filepath_after))
    # ast_before = AST.build_from_javalang(build_ast(filepath_before))
    class_ = [x for x in ast_after.get_proxy_nodes(
        ASTNodeType.CLASS_DECLARATION,
        ASTNodeType.ENUM_DECLARATION,
        ASTNodeType.INTERFACE_DECLARATION
    ) if x.name == class_name][0]
    target_modified = [x for x in class_.methods if x.name == target_function_name][0]
    body_start_line_mdfd, body_end_line_mdfd = method_body_lines(
        target_modified,
        Path(filepath_after)
    )

    _, lines_matched, _, _, how_similar_btw_extractions_target_modified, _ = is_similar_functions(
        str(csv_output / filepath_before),
        str(csv_output / filepath_after),
        [[function_target_start_line + 1, function_target_end_line]],
        (body_start_line_mdfd, body_end_line_mdfd)
    )
    exc = [' ', '{', '}', '']
    after_lines = get_after_lines(
        exc,
        filepath_after,
        (body_start_line_mdfd, body_end_line_mdfd))

    # we add 1 line since invocation of extracted method
    # will differ every time
    lines_matched += 1
    target_modified_size = len(after_lines[0])
    row['similarity_modified'] = float(lines_matched) / target_modified_size
    return row


if __name__ == '__main__':  # noqa: C901
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--dir",
        required=True,
        help="File path to JAVA similarity dataset"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input filtered similarity csv dataset file"
    )
    parser.add_argument(
        "-o", "--out",
        help="Output csv file",
        default='filtered_target.csv'
    )
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
    csv_output = Path(args.out, 'filtered_results_with_target.csv')

    df = pd.read_csv(args.input)
    df['real_extractions'] = df['real_extractions'].apply(literal_eval)

    new_df = pd.DataFrame(columns=df.columns)
    with ProcessPool(system_cores_qty) as executor:
        future = executor.map(calculate_additional_similarity)
        result = future.result()

        for filename in tqdm(df.iterrows(), total=df.shape[0]):
            try:
                row = next(result)
                new_df.append(row, ignore_index=True)
            except Exception as e:
                traceback.print_stack()

    new_df.to_csv(args.out)
