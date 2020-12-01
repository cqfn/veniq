import json
import os
import random
import traceback
from argparse import ArgumentParser
from ast import literal_eval
from dataclasses import dataclass, asdict
from functools import partial
from multiprocessing import Manager
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
from pebble import ProcessPool
from requests.auth import HTTPBasicAuth
from requests import Session
from tqdm import tqdm

from veniq.ast_framework import ASTNodeType
# f77a2ddf76ca1e95be78c3808278b5a3cf7871d0
from veniq.dataset_collection.augmentation import get_ast_if_possible, method_body_lines
from veniq.dataset_mining.code_similarity import is_similar_functions


@dataclass
class Row:
    filename: str
    filepath_saved: str
    class_name: str
    function_inlined: str
    function_name_with_LM: str
    # hamming: float
    # ratcliff_obershelp: float
    function_target_start_line: int
    function_target_end_line: int
    real_extractions: Optional[Tuple]
    commit_sha_before: str
    commit_sha_after: str
    lines_number: int
    lines_matched: int
    matched_percent: float
    matched_strings: Optional[str]
    is_similar: bool
    repo_url: str
    downloaded_after: bool
    downloaded_before: bool
    found_class_before_in_java_file: bool
    found_class_after_in_java_file: bool
    error: str
    url: str


def get_previous_commit(
        sha: str,
        file_path: str,
        repo: str,
        row_res: Row,
        session: Session,
        auth):
    commit_sha_before = ''
    url_with_params = f'https://api.github.com/repos/{repo}/commits?path={file_path}&sha={sha}'
    # time.sleep(10)

    resp = session.get(url_with_params, auth=auth)
    if resp.status_code == 200:
        try:
            resp_json = resp.json()
            if len(resp_json) < 2:
                row_res.error = 'No previous commit found. Files was moved'
            else:
                previous_commit_item = resp_json[1]
                commit_sha_before = previous_commit_item['sha']

        except Exception as e:
            print(f'cannot get previous commit {str(e)}')
            row_res.error = str(e)
    else:
        row_res.error = f'{str(resp.status_code)}: {str(resp.content)}'

    return commit_sha_before


def download_file(
        repo_name: str,
        commit_sha: str,
        filename_raw: Path,
        output_dir_for_saved_file: Path,
        auth,
        session: Session,
        file_prefix: str,
        row_res: Row):
    commit_url = f'https://api.github.com/repos/{repo_name}/commits/{commit_sha}'

    resp = session.get(commit_url, auth=auth)
    resp_json = resp.json()
    files = resp_json.get('files', [])
    if not files:
        row_res.error = f'{resp.status_code}: {resp.content}'  # type: ignore

    found_files_in_commit = find_filename(Path(filename_raw), files)
    if not found_files_in_commit:
        row_res.error = f'File{file_prefix} was not found in commit'

    file_name_for_csv = ''
    for file_item in found_files_in_commit:
        url = file_item['raw_url']
        file_content = session.get(url, auth=auth).content
        file_name_for_csv = Path(
            output_dir_for_saved_file,
            Path(file_item['filename']).stem + file_prefix + '.java')  # type:ignore

        with open(file_name_for_csv, 'wb') as w:
            w.write(file_content)

    return file_name_for_csv


def sample_from_dict(d, sample=1):
    keys = random.sample(list(d), sample)
    values = [d[k] for k in keys]
    return keys[0], values[0]


def handle_commit_example(sample, tokens, output_dir, classes_dict):
    example_id, series = sample
    results = []
    user, passwd = sample_from_dict(tokens)
    repository_url = series['repository']
    commit_sha_after = series['sha1']
    repo_part_1 = Path(repository_url).parts[2:-1]
    repo_part_2 = Path(repository_url).parts[-1].replace('.git', '')
    repo_name = Path(*repo_part_1, repo_part_2).as_posix()
    description = series.get('description')
    filename_in_commit = series.get('filename')
    filename_raw = Path(description.split('in class')[1].replace('.', '/').strip())
    class_name = filename_raw.stem
    classes = classes_dict.get(commit_sha_after, set())
    if class_name not in classes:
        add_to_dict_set(commit_sha_after, class_name, classes_dict)
        unique_directory = output_dir / str(example_id)
        if not unique_directory.exists():
            unique_directory.mkdir(parents=True)

        auth = HTTPBasicAuth(user, passwd)
        s = Session()
        res = Row(
            filepath_saved='',
            filename=filename_in_commit,
            class_name=class_name,
            repo_url=repository_url,
            function_inlined='',
            function_name_with_LM='',
            commit_sha_before='',
            commit_sha_after=commit_sha_after,
            # hamming=-1,
            # ratcliff_obershelp=-1,
            function_target_start_line=-1,
            function_target_end_line=-1,
            real_extractions=(),
            lines_number=-1,
            lines_matched=-1,
            matched_percent=-1.0,
            matched_strings='',
            is_similar=False,
            error='',
            url=series['url'],
            downloaded_after=False,
            downloaded_before=False,
            found_class_before_in_java_file=False,
            found_class_after_in_java_file=False
        )
        file_after = download_file(
            repo_name, commit_sha_after, filename_in_commit,
            unique_directory, auth, s, '_after', res)
        commit_sha_before = get_previous_commit(
            commit_sha_after, filename_in_commit, repo_name,
            res, s, auth
        )
        if file_after:
            res.downloaded_after = True
            res.filepath_saved = file_after
            if commit_sha_before:
                res.commit_sha_before = commit_sha_before
                file_before = download_file(
                    repo_name,
                    commit_sha_before,
                    filename_in_commit,
                    unique_directory,
                    auth,
                    s,
                    '_before',
                    res
                )
                if file_before:
                    res.downloaded_before = True
                    run_similarity(class_name, description, file_after, file_before, res, series)
                else:
                    res.error = 'File before was not downloaded'
        else:
            res.error = 'File after was not downloaded'

        results.append(res)
    return results


def run_similarity(class_name, description, file_after, file_before, res, series):
    list_of_lines_before = series['lines']
    res.real_extractions = list_of_lines_before
    function_name_inlined = get_function_name_from_description(description, 'Extract Method')
    res.function_inlined = function_name_inlined
    function_name_with_LM = get_function_name_from_description(description, 'extracted from')
    function_name_with_LM = function_name_with_LM.split('(')[0]
    res.function_name_with_LM = function_name_with_LM
    method_node_before = find_function_by_name_in_ast(file_before, class_name, function_name_with_LM, res)
    if method_node_before:
        res.found_class_before_in_java_file = True
    method_node_after = find_function_by_name_in_ast(file_after, class_name, function_name_inlined, res)

    if method_node_after:
        res.found_class_after_in_java_file = True
    if method_node_before and method_node_after:
        lines_after = method_body_lines(method_node_after, file_after)
        lines_before = method_body_lines(method_node_before, file_before)
        res.function_target_start_line = lines_before[0]
        res.function_target_end_line = lines_before[1]
        is_similar = is_similar_functions(
            file_before,
            file_after,
            list_of_lines_before,
            lines_after,
            res
        )
        res.is_similar = is_similar


def get_function_name_from_description(description, split_by):
    function_string_in_after_file = ' '.join(description.split(split_by)[1].strip().split(' ')[1:])
    function_string_in_after_file = function_string_in_after_file.split(':')[0].strip()
    function_name = function_string_in_after_file.split('(')[0]
    return function_name


def find_function_by_name_in_ast(filename, class_name, function_name, res):
    ast = get_ast_if_possible(filename, res)

    if ast:
        classes_ast = [
            ast.get_subtree(x) for x in ast.get_proxy_nodes(
                ASTNodeType.CLASS_DECLARATION, ASTNodeType.INTERFACE_DECLARATION, ASTNodeType.ENUM_DECLARATION)
            if x.name == class_name]

        if classes_ast:
            class_ast = classes_ast[0]
            for method_node in class_ast.get_proxy_nodes(
                    ASTNodeType.METHOD_DECLARATION, ASTNodeType.CONSTRUCTOR_DECLARATION):
                is_name_equal = method_node.name == function_name
                if is_name_equal:
                    return method_node

    return None


def search_filenames_in_commit(filename_raw: Path, files):
    """
    Searches filename in commit. If it is not found it tries
    to find a subclass
    :param filename_raw: file path of file in a commit
    :param files: list of all items of a commit, given by github API
    :return: list of found files
    """
    filename_to_search = Path(*filename_raw.parts[:-1], filename_raw.parts[-1] + '.java')
    files_after_arr = find_filename(filename_to_search, files)
    if not files_after_arr:
        # finds subclass
        filename_to_search = Path(*filename_raw.parts[:-2], filename_raw.parts[-2] + '.java')
        files_after_arr = find_filename(filename_to_search, files)
    if not files_after_arr:
        # finds subclass of subclass
        filename_to_search = Path(*filename_raw.parts[:-3], filename_raw.parts[-3] + '.java')
        files_after_arr = find_filename(filename_to_search, files)
    return files_after_arr


def find_filename(filename_raw: Path, files):
    return [x for x in files if x['filename'].find(filename_raw.as_posix()) > -1]


def add_to_dict_set(key, val, multi_dict):
    if key not in multi_dict:
        multi_dict[key] = set()
    temp_set = multi_dict[key]
    temp_set.add(val)
    multi_dict[key] = temp_set


def filter_refactorings_by_em(dataset_samples):
    handled_samples = []
    for sample in dataset_samples:
        for x in sample['refactorings']:
            if x['type'] == 'Extract Method':
                new_item = sample.copy()
                new_item['refactorings'] = x
                handled_samples.append(new_item)

    return handled_samples


if __name__ == '__main__':
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-o", "--output_dir",
        help="Path where commits with files will be saved",
        required=True
    )
    parser.add_argument(
        "-t", "--token_file",
        help="Json file with tokens for github API",
        required=True
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
        help="csv with dataset",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-of", "--output_file",
        help="Output file for dataset json",
        default='similarity.csv',
        required=True
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    output_df = pd.DataFrame(columns=list(Row.__annotations__.keys()))
    with open(args.token_file, 'r', encoding='utf-8') as f:
        tokens = json.loads(f.read())

    with open(args.csv, encoding='utf-8') as f:
        with Manager() as manager:
            d = manager.dict()  # type: ignore
            with ProcessPool(system_cores_qty) as executor:
                dataset_samples = pd.read_csv(args.csv)
                dataset_samples['lines'] = dataset_samples['lines'].apply(literal_eval)
                func = partial(handle_commit_example, output_dir=output_dir, tokens=tokens, classes_dict=d)
                future = executor.map(func, dataset_samples.iterrows(), timeout=10000, )
                result = future.result()
                rows = dataset_samples.iterrows()
                for sample in tqdm(rows, total=dataset_samples.shape[0]):
                    try:
                        results = next(result)
                        for res in results:
                            output_df = output_df.append(asdict(res), ignore_index=True)
                        output_df.to_csv(args.output_file)
                    except Exception:
                        sha1 = sample[1]['sha1']
                        id = sample[1][0]
                        stack = traceback.format_exc()
                        print(f'Error for {id} {sha1} {stack}')
                        continue

    # output_df = output_df.drop_duplicates()
    # output_df.to_csv('new_urls.csv')
