import os
from argparse import ArgumentParser
from functools import partial
from pathlib import Path

import pandas as pd
from enum import Enum

from pebble import ProcessPool
from tqdm import tqdm

from veniq.utils.ast_builder import build_ast
from veniq.ast_framework import AST, ASTNodeType
from veniq.utils.encoding_detector import read_text_with_autodetected_encoding
from veniq.dataset_collection.augmentation import method_body_lines

import traceback


class FunctionExist(Enum):
    ERROR = -1
    CLASS_NOT_FOUND = 0
    OVERLOADED_FUNC = 1
    FUNCTION_NO_FOUND = 2
    FUNCTION_LINES_NOT_MATCHED = 3
    FUNCTION_LINES_MATCHED = 4


def was_not_inlined(inline_insertion_line_start, invocation_text_string, output_filename):
    text = read_text_with_autodetected_encoding(output_filename).split('\n')
    invocation_text_line = text[inline_insertion_line_start - 1]
    return invocation_text_line.strip() == invocation_text_string.strip()


def check_function_start_end_line(
        filename: str,
        class_name: str,
        function_name: str,
        start_line: int,
        end_line=None):
    ast = AST.build_from_javalang(build_ast(filename))
    class_decl = [
        x for x in ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
        if x.name == class_name]

    if len(class_decl) == 0:
        return FunctionExist.CLASS_NOT_FOUND
    else:
        class_decl = class_decl[0]
        ctrs = [x for x in ast.get_proxy_nodes(ASTNodeType.CONSTRUCTOR_DECLARATION)]

        all_considered_methods = list([x for x in class_decl.methods]) + ctrs
        functions = [x for x in all_considered_methods if x.name == function_name]

        if len(functions) == 0:
            return (None, None), FunctionExist.FUNCTION_EXISTS.name
        elif len(functions) > 1:
            return (None, None), FunctionExist.OVERLOADED_FUNC.name
        else:
            original_func = functions[0]
            body_start_line, body_end_line = method_body_lines(original_func, Path(filename))

            if end_line is None:
                if original_func.line == start_line:
                    return (original_func.line, body_end_line), FunctionExist.FUNCTION_LINES_MATCHED.name
                else:
                    return (None, None), FunctionExist.FUNCTION_LINES_NOT_MATCHED.name

            elif (body_start_line == start_line) and (body_end_line == end_line):
                return (body_start_line, body_end_line), FunctionExist.FUNCTION_LINES_MATCHED.name
            elif (body_start_line != start_line) or (body_end_line != end_line):
                return (None, None), FunctionExist.FUNCTION_LINES_NOT_MATCHED.name

    return (None, None), FunctionExist.ERROR.name


def make_check(series: pd.Series, output_path: str):
    _, row = series
    output_filename = str(Path(output_path, row['output_filename']))
    class_name = row['class_name']
    invocation_text_string = row['invocation_text_string']
    method_where_invocation_occurred = row['method_where_invocation_occurred']
    start_line_of_function_where_invocation_occurred = row['start_line_of_function_where_invocation_occurred']
    invocation_method_name = row['invocation_method_name']
    invocation_method_start_line = row['invocation_method_start_line']
    invocation_method_end_line = row['invocation_method_end_line']
    # can_be_parsed = row['can_be_parsed']
    inline_insertion_line_start = row['inline_insertion_line_start']
    inline_insertion_line_end = row['inline_insertion_line_end']

    _, row['are_inlined_lines_matched'] = check_function_start_end_line(
        filename=output_filename,
        class_name=class_name,
        function_name=invocation_method_name,
        start_line=invocation_method_start_line,
        end_line=invocation_method_end_line
    )

    lines, row['are_target_lines_matched'] = check_function_start_end_line(
        filename=output_filename,
        class_name=class_name,
        function_name=method_where_invocation_occurred,
        start_line=start_line_of_function_where_invocation_occurred
    )

    body_start_line, body_end_line = lines

    if body_start_line and body_end_line:
        is_inside_start = 1 if \
            inline_insertion_line_start < start_line_of_function_where_invocation_occurred \
            else 0
        row['insertion_start_line_inside_target'] = is_inside_start
        is_inside_end = 1 if \
            inline_insertion_line_end > body_end_line \
            else 0
        row['insertion_end_line_inside_target'] = is_inside_end
    else:
        row['insertion_start_line_inside_target'] = row['insertion_end_line_inside_target'] = -1

    row['was_not_inlined'] = was_not_inlined(
        inline_insertion_line_start,
        invocation_text_string,
        output_filename
    )

    return row


if __name__ == '__main__':  # noqa: C901
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--dir",
        required=True,
        help="File path to JAVA source code for methods augmentations"
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
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help='Csv file for dataset'
    )

    args = parser.parse_args()

    full_df = pd.read_csv(args.csv)
    df = full_df[full_df['can_be_parsed']]
    columns = [x for x in df.columns if x.find('Unnamed') < 0] \
              + ['are_target_lines_matched',
                 'are_inlined_lines_matched',
                 'was_not_inlined',
                 'insertion_start_line_inside_target',
                 'insertion_end_line_inside_target'
                 ]
    new_df = pd.DataFrame(columns=columns)

    with ProcessPool(system_cores_qty) as executor:
        p_check = partial(
            make_check,
            output_path=args.dir,
        )
        future = executor.map(p_check, df.iterrows())
        result = future.result()

        for _, row in tqdm(df.iterrows(), total=df.shape[0]):
            try:
                res = next(result)
                new_df = new_df.append(res[columns], ignore_index=True)

                new_df.to_csv('checked.csv')
            except Exception as e:
                print(f'Exception in {_} case')
                traceback.print_exc()

    filtered_df = new_df.copy()

    def remove_indices(df_to_filter: pd.DataFrame):
        rows = filtered_df[filtered_df.index.isin(df_to_filter.index)]
        filtered_df.drop(rows.index, inplace=True)

    print(f'Total lines: {new_df.shape[0]}')
    duplicateRowsDF = new_df[new_df.duplicated()]
    print(f'Duplicated rows: {duplicateRowsDF.shape[0]}')
    remove_indices(duplicateRowsDF)
    was_not_inlined_df = new_df[new_df['was_not_inlined']]
    remove_indices(was_not_inlined_df)
    print(f'Was not inlined {was_not_inlined_df.shape[0]}')

    insertion_start_line_inside_target = new_df[new_df['insertion_start_line_inside_target'] == 1]
    remove_indices(insertion_start_line_inside_target)
    print(f'Samples where insertion start line '
          f'was outside target function {insertion_start_line_inside_target.shape[0]}')
    insertion_end_line_inside_target = new_df[new_df['insertion_end_line_inside_target'] == 1]
    remove_indices(insertion_end_line_inside_target)
    print(f'Samples where insertion end line '
          f'was outside target function {insertion_end_line_inside_target.shape[0]}')

    new_df['score_diff'] = new_df['invocation_method_end_line'].sub(new_df['invocation_method_start_line'], axis=0)
    negative_insertions = new_df[new_df['score_diff'] < 0]
    remove_indices(negative_insertions)
    print(f'Negative insertions: {negative_insertions.shape[0]}')

    can_be_parsed = full_df[~full_df['can_be_parsed']]
    print(f'Cases when insertion was made '
          f'but it cannot be parsed {can_be_parsed.shape[0]}')
    #################################################################################################################
    temp_df = new_df[
        new_df['are_inlined_lines_matched'] == FunctionExist.ERROR.name
    ]
    remove_indices(temp_df)
    print(f'Samples where error happened '
          f'when checking inlined\'s range {temp_df.shape[0]}')
    temp_df = new_df[
        new_df['are_inlined_lines_matched'] == FunctionExist.CLASS_NOT_FOUND.name
    ]
    remove_indices(temp_df)
    print(f'Samples where class was not found '
          f'when checking inlines\'s range {temp_df.shape[0]}')
    temp_df = new_df[
        new_df['are_target_lines_matched'] == FunctionExist.OVERLOADED_FUNC.name
    ]
    remove_indices(temp_df)
    print(f'Samples where inlined function is overloaded '
          f'when checking inlines\'s range {temp_df.shape[0]}')
    temp_df = new_df[
        new_df['are_inlined_lines_matched'] == FunctionExist.FUNCTION_NO_FOUND.name
    ]
    remove_indices(temp_df)
    print(f'Samples where inlined function was not found '
          f'when checking inlines\'s range {temp_df.shape[0]}')
    temp_df = new_df[
        new_df['are_inlined_lines_matched'] == FunctionExist.FUNCTION_LINES_NOT_MATCHED.name
        ]
    print(f'Samples where lines of inlined function were not matched '
          f'when checking inlines\'s range {temp_df.shape[0]}')
    remove_indices(temp_df)
    temp_df = new_df[
        new_df['are_inlined_lines_matched'] == FunctionExist.FUNCTION_LINES_MATCHED.name
    ]
    print(f'Samples where lines of inlined function were matched '
          f'when checking inlines\'s range {temp_df.shape[0]}')
    #########################################################################################
    temp_df = new_df[
        new_df['are_target_lines_matched'] == FunctionExist.ERROR.name
    ]
    remove_indices(temp_df)
    print(f'Samples where error happened '
          f'when checking target\'s range {temp_df.shape[0]}')
    temp_df = new_df[
        new_df['are_target_lines_matched'] == FunctionExist.CLASS_NOT_FOUND.name
    ]
    remove_indices(temp_df)
    print(f'Samples where class was not found '
          f'when checking target\'s range {temp_df.shape[0]}')
    temp_df = new_df[
        new_df['are_target_lines_matched'] == FunctionExist.OVERLOADED_FUNC.name
    ]
    remove_indices(temp_df)
    print(f'Samples where target function is overloaded '
          f'when checking target\'s range {temp_df.shape[0]}')
    target_lines_matched = new_df[
        new_df['are_target_lines_matched'] == FunctionExist.FUNCTION_NO_FOUND.name
    ]
    remove_indices(temp_df)
    print(f'Samples where target function was not found '
          f'when checking target\'s range {temp_df.shape[0]}')

    temp_df = new_df[
        new_df['are_target_lines_matched'] == FunctionExist.FUNCTION_LINES_NOT_MATCHED.name
        ]
    print(f'Samples where lines of target function were not matched '
          f'when checking inlines\'s range {temp_df.shape[0]}')
    remove_indices(temp_df)
    temp_df = new_df[
        new_df['are_target_lines_matched'] == FunctionExist.FUNCTION_LINES_MATCHED.name
    ]

    print(f'Samples where lines of target function were matched '
          f'when checking target\'s range {temp_df.shape[0]}')

    filtered_size = filtered_df.shape[0] - can_be_parsed.shape[0]
    print(f'After filtering we\'ve got {filtered_size} of {new_df.shape[0]}')
    ratio = float(filtered_size)/new_df.shape[0]
    print(f'We have {ratio}% correct samples of all dataset')
