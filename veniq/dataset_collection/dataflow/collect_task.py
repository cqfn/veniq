import hashlib
import os
import re
from argparse import ArgumentParser
from functools import partial
from pathlib import Path

import javalang
from javalang.parse import parse
import d6tflow
import pandas as pd

import d6tcollect

# from veniq.dataset_collection.augmentation import InvocationType
from pebble import ProcessPool
from tqdm import tqdm

from veniq.ast_framework import AST, ASTNodeType
from veniq.utils.ast_builder import build_ast
from veniq.utils.encoding_detector import read_text_with_autodetected_encoding

d6tcollect.submit = False

# columns = [
#         'project_id',
#         'original_filename',
#         'class_name',
#         'invocation_line_string',
#         'invocation_line_number_in_original_file',
#         'target_method',
#         'target_method_start_line',
#         'extract_method',
#         'extract_method_start_line',
#         'extract_method_end_line',
#         'output_filename',
#         'is_valid_ast',
#         'insertion_start',
#         'insertion_end',
#         'ncss_target',
#         'ncss_extracted',
#         'do_nothing',
#         'ONE_LINE_FUNCTION',
#         'NO_IGNORED_CASES'
#     ] + [x for x in InvocationType.list_types()]


class TaskAggregatorJavaFiles(d6tflow.tasks.TaskCache):
    dir_to_search = d6tflow.Parameter()
    dir_to_save = d6tflow.Parameter()
    system_cores_qty = d6tflow.IntParameter()

    def run(self):
        test_files = set(Path(self.dir_to_search).glob('**/*Test*.java'))
        not_test_files = set(Path(self.dir_to_search).glob('**/*.java'))
        files_without_tests = list(not_test_files.difference(test_files))
        if not files_without_tests:
            raise Exception("No java files were found")

        full_dataset_folder = Path(self.dir_to_save) / 'full_dataset'
        self.output_dir = full_dataset_folder / 'output_files'
        self.input_dir = full_dataset_folder / 'input_files'
        # df = pd.DataFrame(columns=columns)
        results = []
        # with ProcessPool(system_cores_qty) as executor:
        #
        #     future = executor.map(TaskPreprocessJavaFile.run, timeout=200, )
        #     result = future.result()
        #
        #     # each 100 cycles we dump the results
        #     iteration_cycle = 1000
        #     iteration_number = 0
        #     for filename in tqdm(files_without_tests):
        #         try:
        #             # print(filename)
        #             single_file_features = next(result)
        #             if single_file_features:
        #                 results.append(single_file_features)
        #         except Exception as e:
        #             print(e)
        for x in files_without_tests:
            # d = {j: '' for j in columns}
            # d.update({'original_filename': x})
            # df = df.append(d, ignore_index=True)
            # self.save({'file': str(x)})
            a = yield TaskPreprocessJavaFile(file=str(x))
            results.append(a)
        self.save({"results": results})


# @d6tflow.requires({'file': TaskAggregatorJavaFiles})
class TaskPreprocessJavaFile(d6tflow.tasks.TaskCache):
    file = d6tflow.Parameter()

    # target_class = d6tflow.targets.TaskPickle
    # target_ext = 'pkl'
    # persist = ['data']
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

    # def save_text_to_new_file(
    #         self,
    #         input_dir: Path,
    #         text: str, filename: Path):
    #     # need to avoid situation when filenames are the same
    #     hash_path = hashlib.sha256(str(filename.parent).encode('utf-8')).hexdigest()
    #     dst_filename = input_dir / f'{filename.stem}_{hash_path}.java'
    #     # if not dst_filename.parent.exists():
    #     #     dst_filename.parent.mkdir(parents=True)
    #     # if not dst_filename.exists():
    #     #     with open(dst_filename, 'w', encoding='utf-8') as w:
    #     #         w.write(text)
    #
    #     return dst_filename, text

    # @classmethod
    def run(self):
        # file = self.inputLoad()['file']['file']
        print(self.file)
        # file = files['file'].absolute()
        # print(f'TaskPreprocessJavaFile {df.shape[0]}')
        original_text = read_text_with_autodetected_encoding(str(self.file))
        # remove comments
        text_without_comments = self._remove_comments(original_text)
        # remove whitespaces
        text = "\n".join([ll.rstrip() for ll in text_without_comments.splitlines() if ll.strip()])
        try:
            ast = AST.build_from_javalang(parse(text))
            self.save({'text': text, 'ast': ast})
        except javalang.parser.JavaSyntaxError:
            pass
        # for _, x in df.iterrows():
        #     # print(x)
        #     x['output_file'] = 'XXXX'
        #     original_text = read_text_with_autodetected_encoding(str(self.file))
        #     # remove comments
        #     text_without_comments = self._remove_comments(original_text)
        #     # remove whitespaces
        #     text = "\n".join([ll.rstrip() for ll in text_without_comments.splitlines() if ll.strip()])
        #     ast = AST.build_from_javalang(parse(text))
        #
        #     self.save()


#@d6tflow.requires({'input1': TaskPreprocessJavaFile})
# class TaskFindEM(d6tflow.tasks.TaskJson):
#     # ast_tree = AST
#     # text = d6tflow.Parameter()
#
#     def __init__(self, *args, **kwargs):
#         kwargs_ = {k: v for k, v in kwargs.items() if k in self.get_param_names()}
#         super().__init__(*args, **kwargs_)
#
#     def run(self):
#         input1 = self.inputLoad()['input1']
#
#         class_name = [x for x in input1['ast_tree'].get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)][0]
#         #print(class_name)
#         self.save({"class_name": class_name})


if __name__ == '__main__':
    # Intelligently rerun workflow after changing parameters
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dir",
        required=True,
        help="File path to JAVA source code for methods augmentations"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path for file with output results",
        default='augmented_data'
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
        "-z", "--zip",
        action='store_true',
        help="To zip input and output files."
    )
    parser.add_argument(
        "-s", "--small_dataset_size",
        help="Number of files in small dataset",
        default=100,
        type=int,
    )

    args = parser.parse_args()

    d6tflow.preview(TaskAggregatorJavaFiles(dir_to_search=args.dir, dir_to_save=args.output, system_cores_qty=args.jobs))
    d6tflow.run(TaskAggregatorJavaFiles(dir_to_search=args.dir, dir_to_save=args.output, system_cores_qty=args.jobs))
    data = TaskAggregatorJavaFiles(dir_to_search=args.dir, dir_to_save=args.output, system_cores_qty=args.jobs).outputLoad(cached=False)
    print(data)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
