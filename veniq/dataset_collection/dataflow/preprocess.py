import hashlib
import re
from pathlib import Path

import d6tcollect
import d6tflow
import pandas as pd
# from veniq.dataset_collection.augmentation import InvocationType
from pebble import ProcessPool
from tqdm import tqdm

from veniq.utils.encoding_detector import read_text_with_autodetected_encoding

d6tcollect.submit = False


class TaskAggregatorJavaFiles(d6tflow.tasks.TaskCSVPandas):
    dir_to_search = d6tflow.Parameter()
    dir_to_save = d6tflow.Parameter()
    system_cores_qty = d6tflow.IntParameter()

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
    ]  # + [x for x in InvocationType.list_types()]

    def _remove_comments(self, string: str):
        pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
        # first group captures quoted strings (double or single)
        # second group captures comments (//single-line or /* multi-line */)
        regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

        def _replacer(match):
            # if the 2nd group (capturing comments) is not None,
            # it means we have captured a non-quoted (real) comment string.
            if match.group(2) is not None:
                # so we will return empty to remove the comment
                return ""
            else:  # otherwise, we will return the 1st group
                return match.group(1)  # captured quoted-string

        return regex.sub(_replacer, string)

    def _preprocess(self, file):
        original_text = read_text_with_autodetected_encoding(str(file))
        # remove comments
        text_without_comments = self._remove_comments(original_text)
        # remove whitespaces
        text = "\n".join([ll.rstrip() for ll in text_without_comments.splitlines() if ll.strip()])

        return text

    def _save_text_to_new_file(self, input_dir: Path, text: str, filename: Path) -> Path:
        # need to avoid situation when filenames are the same
        hash_path = hashlib.sha256(str(filename.parent).encode('utf-8')).hexdigest()
        dst_filename = input_dir / f'{filename.stem}_{hash_path}.java'
        if not dst_filename.parent.exists():
            dst_filename.parent.mkdir(parents=True)
        if not dst_filename.exists():
            with open(dst_filename, 'w', encoding='utf-8') as w:
                w.write(text)

        return dst_filename

    def run(self):
        test_files = set(Path(self.dir_to_search).glob('**/*Test*.java'))
        not_test_files = set(Path(self.dir_to_search).glob('**/*.java'))
        files_without_tests = list(not_test_files.difference(test_files))
        if not files_without_tests:
            raise Exception("No java files were found")

        full_dataset_folder = Path(self.dir_to_save) / 'full_dataset'
        if not full_dataset_folder.exists():
            full_dataset_folder.mkdir(parents=True)
        self.output_dir = full_dataset_folder / 'output_files'
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        self.input_dir = full_dataset_folder / 'input_files'
        if not self.input_dir.exists():
            self.input_dir.mkdir(parents=True)
        df = pd.DataFrame(columns=['original_filename'])
        with ProcessPool(self.system_cores_qty) as executor:
            future = executor.map(self._preprocess, files_without_tests, timeout=200, )
            result = future.result()
            for filename in tqdm(files_without_tests):
                try:
                    text = next(result)
                    if text:
                        df = df.append(
                            {'original_filename': self._save_text_to_new_file(self.input_dir, text,
                                                                              filename).absolute()},
                            ignore_index=True
                        )
                except Exception as e:
                    print(str(e))

        self.save(data=df)
