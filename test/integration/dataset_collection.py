import tempfile
from os import listdir
from pathlib import Path
from unittest import TestCase

import pandas as pd
from tqdm import tqdm
import difflib
import pprint

from veniq.dataset_collection.augmentation import analyze_file
import traceback

class IntegrationDatasetCollection(TestCase):

    def diff_dicts(self, a, b):
        if a == b:
            return ''
        return '\n'.join(
            difflib.ndiff(pprint.pformat(a, width=30).splitlines(),
                          pprint.pformat(b, width=30).splitlines())
        )

    def test_dataset_collection(self):
        samples_path = Path(__file__).absolute().parent / "dataset_collection"
        # ignore output filename, cause it is not so important

        results_output = []
        with tempfile.TemporaryDirectory() as tmpdirname:
            print('created temporary directory', tmpdirname)

            full_dataset_folder = Path(tmpdirname) / 'full_dataset'
            output_dir = full_dataset_folder / 'output_files'
            if not output_dir.exists():
                print('created temporary directory', output_dir)
                output_dir.mkdir(parents=True)

            input_dir = full_dataset_folder / 'input_files'
            if not input_dir.exists():
                print('created temporary directory', input_dir)
                input_dir.mkdir(parents=True)

            for filepath in tqdm(listdir(samples_path)):
                full_filename = samples_path / filepath
                try:
                    results_output.extend(analyze_file(full_filename, output_dir, input_dir))
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to run analyze function in file {full_filename}"
                    ) from e

            new_results = pd.DataFrame(columns=[
                'project'
                'input_filename',
                'class_name',
                'invocation_text_string',
                'method_where_invocation_occurred',
                'start_line_of_function_where_invocation_occurred',
                'invocation_method_name',
                'invocation_method_start_line',
                'invocation_method_end_line',
                'can_be_parsed',
                'inline_insertion_line_start',
                'inline_insertion_line_end'
            ])
            for x in results_output:
                x['input_filename'] = str(Path(x['input_filename']).name).split('_')[0] + '.java'
                del x['output_filename']
                del x['project']
                new_results = new_results.append(x, ignore_index=True)

        df = pd.DataFrame(new_results)
        new_results = df.sort_values(by=df.columns.to_list())

        df = pd.read_csv(Path(__file__).absolute().parent / 'results_predefined.csv', index_col=0)
        results_predefined = df.sort_values(by=df.columns.to_list())
        df_diff = pd.concat([new_results, results_predefined]).drop_duplicates(keep=False)
        size_of_difference = df_diff.shape[0]
        print(f'Difference in dataframes: {size_of_difference} rows')

        try:
            self.assertEqual(size_of_difference, 0)
        except AssertionError as e:
            print(self.diff_dicts(new_results.to_dict(), results_predefined.to_dict()))
            raise e
