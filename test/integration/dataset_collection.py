import json
import tempfile
from os import listdir
from pathlib import Path
from typing import Dict, List
from unittest import TestCase

from tqdm import tqdm
import pandas as pd
from veniq.dataset_collection.augmentation import analyze_file


class IntegrationDatasetCollection(TestCase):

    def test_dataset_collection(self):
        samples_path = Path(__file__).absolute().parent / "dataset_collection"
        # ignore output filename, cause it is not so important
        results_predefined: List[Dict[str, any]] = \
            [{'input_filename': 'GlobalShortcutConfigForm.java',
              'class_name': 'GlobalShortcutConfigForm',
              'invocation_text_string': 'this.initComponents();',
              'method_where_invocation_occurred': 'GlobalShortcutConfigForm',
              'start_line_of_function_where_invocation_occurred': 78,
              'invocation_method_name': 'initComponents',
              'invocation_method_start_line': 89,
              'invocation_method_end_line': 181,
              'can_be_parsed': True},
             {'input_filename': 'HudFragment.java',
              'class_name': 'HudFragment',
              'invocation_text_string': 'toggleMenus();',
              'method_where_invocation_occurred': 'build',
              'start_line_of_function_where_invocation_occurred': 43,
              'invocation_method_name': 'toggleMenus',
              'invocation_method_start_line': 510,
              'invocation_method_end_line': 516,
              'can_be_parsed': True},
             {'input_filename': 'HudFragment.java',
              'class_name': 'HudFragment', 'invocation_text_string': 'showLaunchConfirm();',
              'method_where_invocation_occurred': 'addWaveTable',
              'start_line_of_function_where_invocation_occurred': 518,
              'invocation_method_name': 'showLaunchConfirm', 'invocation_method_start_line': 479,
              'invocation_method_end_line': 497,
              'can_be_parsed': True},
             {'input_filename': 'PlanetDialog.java',
              'class_name': 'PlanetDialog',
              'invocation_text_string': 'makeBloom();',
              'method_where_invocation_occurred': 'PlanetDialog',
              'start_line_of_function_where_invocation_occurred': 67,
              'invocation_method_name': 'makeBloom',
              'invocation_method_start_line': 147,
              'invocation_method_end_line': 158,
              'can_be_parsed': True},
             {'input_filename': 'PlanetDialog.java',
              'class_name': 'PlanetDialog', 'invocation_text_string': 'updateSelected();',
              'method_where_invocation_occurred': 'PlanetDialog',
              'start_line_of_function_where_invocation_occurred': 67,
              'invocation_method_name': 'updateSelected', 'invocation_method_start_line': 334,
              'invocation_method_end_line': 382,
              'can_be_parsed': True},
             {'input_filename': 'ReaderHandler.java',
              'class_name': 'ReaderHandler',
              'invocation_text_string': 'receiveMessage();',
              'method_where_invocation_occurred': 'onWebSocketConnect',
              'start_line_of_function_where_invocation_occurred': 181,
              'invocation_method_name': 'receiveMessage',
              'invocation_method_start_line': 115,
              'invocation_method_end_line': 178,
              'can_be_parsed': True},
             {'input_filename': 'ToggleProfilingPointAction.java',
              'class_name': 'ToggleProfilingPointAction',
              'invocation_text_string': 'nextFactory();',
              'method_where_invocation_occurred': 'actionPerformed',
              'start_line_of_function_where_invocation_occurred': 241,
              'invocation_method_name': 'nextFactory', 'invocation_method_start_line': 361,
              'invocation_method_end_line': 367,
              'can_be_parsed': True},
             {'input_filename': 'ToggleProfilingPointAction.java',
              'class_name': 'ToggleProfilingPointAction',
              'invocation_text_string': 'resetFactories();',
              'method_where_invocation_occurred': 'actionPerformed',
              'start_line_of_function_where_invocation_occurred': 241,
              'invocation_method_name': 'resetFactories',
              'invocation_method_start_line': 369,
              'invocation_method_end_line': 376,
              'can_be_parsed': True}
             ]

        results_output = []
        with tempfile.TemporaryDirectory() as tmpdirname:
            print('created temporary directory', tmpdirname)
            for filepath in tqdm(listdir(samples_path)):
                full_filename = samples_path / filepath
                try:
                    results_output.extend(analyze_file(full_filename, tmpdirname))
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to run analyze function in file {full_filename}"
                    ) from e

            new_results = pd.DataFrame(columns=[
                'input_filename',
                'class_name',
                'invocation_text_string',
                'method_where_invocation_occurred',
                'start_line_of_function_where_invocation_occurred',
                'invocation_method_name',
                'invocation_method_start_line',
                'invocation_method_end_line',
                'can_be_parsed'
            ])
            for x in results_output:
                x['input_filename'] = str(Path(x['input_filename']).name)
                del x['output_filename']
                new_results = new_results.append(x, ignore_index=True)

        df = pd.DataFrame(new_results)
        new_results = df.sort_values(by=df.columns.to_list())

        df = pd.DataFrame(results_predefined)
        results_predefined = df.sort_values(by=df.columns.to_list())

        df_diff = pd.concat([new_results, results_predefined]).drop_duplicates(keep=False)
        print('Difference in dataframes: {df_diff.shape[0]} rows')
        self.assertEqual(df_diff.shape[0], 0)
