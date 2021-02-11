import uuid
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from pandas import DataFrame

from veniq.dataset_collection.dataflow.annotation import InvocationType
from veniq.dataset_collection.types_identifier import InlineTypesAlgorithms
from bonobo.config import Exclusive


def aggregate(dct: Dict[str, Any]):
    input_dir = Path(dct['input_dir'])
    columns = [
        'project_id',
        'original_filename',
        'class_name',
        'invocation_line_string',
        'invocation_line_number_in_original_file',
        'target_method',
        'target_method_start_line',
        'extract_method',
        'extract_method_start_line',
        'extract_method_end_line',
        'output_filename',
        'is_valid_ast',
        'insertion_start',
        'insertion_end',
        'ncss_target',
        'ncss_extracted',
        'do_nothing',
        'ONE_LINE_FUNCTION',
        'NO_IGNORED_CASES'
    ] + [x for x in InvocationType.list_types()] + [x for x in InlineTypesAlgorithms.list_types()]
    real_keys = set(dct.keys())
    result = {}
    for expected_key in columns:
        if expected_key in real_keys:
            result[expected_key] = dct[expected_key]
        else:
            result[expected_key] = ''

    df = DataFrame(columns=columns)
    df = df.append(result, ignore_index=True)
    dataset_csv_path = input_dir.parent / 'dataset_mmm.csv'
    debug = str(uuid.uuid1())
    print(debug)
    if dataset_csv_path.exists():
        with Exclusive(dct):
            old_df = pd.read_csv(dataset_csv_path, encoding='utf-8', index_col=None)
            new_df = old_df.append(df)
            new_df.to_csv(dataset_csv_path, index=False)
            print(f'{debug}_1')
    else:
        print(f'{debug}_2')
        df.to_csv(dataset_csv_path, index=False)
