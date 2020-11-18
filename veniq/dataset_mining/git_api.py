import json
import os
import traceback
from argparse import ArgumentParser
from functools import partial
from multiprocessing import Manager
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import requests
from pebble import ProcessPool
from tqdm import tqdm


def get_previous_commit(
        sha: str,
        file_path: str,
        repo: str,
        d: Dict[str, Any],
        session: requests.Session,
        headers: Dict[str, str]):

    commit_sha_before = ''
    url_with_params = f'https://api.github.com/repos/{repo}/commits?path={file_path}&sha={sha}'
    # time.sleep(10)

    resp = session.get(url_with_params, headers=headers)
    if resp.status_code == 200:
        try:
            resp_json = resp.json()
            if len(resp_json) < 2:
                d['error'] = 'No previous commit found. Files was moved'
            else:
                previous_commit_item = resp_json[1]
                commit_sha_before = previous_commit_item['sha']

        except Exception as e:
            print(f'cannot get previous commit {str(e)}')
            d['error'] = str(e)
    else:
        d['error'] = f'{str(resp.status_code)}: {str(resp.content)}'

    return commit_sha_before


def download_file(
        repo_name: str,
        commit_sha: str,
        filename_raw: Path,
        output_dir_for_saved_file: Path,
        headers: Dict[str, str],
        session: requests.Session,
        file_prefix: str,
        dict_result: Dict[str, Any],
        is_finding_previous_commit=False):

    commit_url = f'https://api.github.com/repos/{repo_name}/commits/{commit_sha}'

    resp = session.get(commit_url, headers=headers)
    resp_json = resp.json()
    files = resp_json.get('files', [])
    if not files:
        dict_result['error'] = f'{resp.status_code}: {resp.content}'  # type: ignore

    found_files_in_commit = search_filenames_in_commit(filename_raw, files)
    if not found_files_in_commit:
        dict_result['error'] = f'File{file_prefix} was not found in commit'

    for file_item in found_files_in_commit:
        url = file_item['raw_url']
        file_content = session.get(url, headers=headers).content
        file_name_for_csv = Path(
            output_dir_for_saved_file,
            Path(file_item['filename']).stem + file_prefix + '.java')
        dict_result['file_name' + file_prefix] = str(file_name_for_csv)
        with open(file_name_for_csv, 'wb') as w:
            w.write(file_content)
            dict_result['downloaded' + file_prefix] = True

        if is_finding_previous_commit:
            return
        else:
            commit_sha_before = get_previous_commit(
                commit_sha,
                file_item['filename'],
                repo_name,
                dict_result,
                session,
                headers
            )
            if commit_sha_before:
                dict_result['commit_before'] = commit_sha_before
                download_file(
                    repo_name,
                    commit_sha_before,
                    filename_raw,
                    output_dir_for_saved_file,
                    headers,
                    session,
                    '_before',
                    dict_result,
                    True
                )


def handle_commit_example(sample, token, output_dir, classes_dict):
    refactorings = sample.get('refactorings')
    results = []
    repository_url = sample['repository']
    example_id = sample['id']
    commit_sha_after = sample['sha1']
    report_part_1 = Path(repository_url).parts[2:-1]
    report_part_2 = Path(repository_url).parts[-1].replace('.git', '')
    repo_name = Path(*report_part_1, report_part_2).as_posix()
    description = refactorings.get('description')
    filename_raw = Path(description.split('in class')[1].replace('.', '/').strip())
    class_name = filename_raw.stem
    classes = classes_dict.get(commit_sha_after, set())
    if class_name not in classes:
        add_to_dict_set(commit_sha_after, class_name, classes_dict)
        output_dir_for_saved_file = output_dir / str(example_id)
        if not output_dir_for_saved_file.exists():
            output_dir_for_saved_file.mkdir(parents=True)

        headers = {f"Authorization": f"token {token}"}
        session = requests.Session()
        d = {
            'repo_url': repository_url,
            'file_name_before': 'Not found',
            'file_name_after': 'Not found',
            'downloaded_after': False,
            'downloaded_before': False,
            'class_name': class_name,
            'commit_before': '',
            'commit_after': commit_sha_after,
            'id': example_id,
            'error': ''
        }

        download_file(
            repo_name,
            commit_sha_after,
            filename_raw,
            output_dir_for_saved_file,
            headers,
            session,
            '_after',
            d
        )
        results.append(d)

    return results


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
        "-t", "--token",
        help="Token for github API",
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
        "-s", "--dataset_file",
        help="Json with dataset",
        required=True,
        type=str,
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    output_df = pd.DataFrame(
        columns=[
            'id',
            'repo_url',
            'class_name',
            'file_name_after',
            'file_name_before',
            'downloaded_after',
            'downloaded_before',
            'commit_before',
            'commit_after',
        ]
    )
    with open(args.dataset_file, encoding='utf-8') as f:
        with Manager() as manager:
            d = manager.dict()  # type: ignore
            with ProcessPool(system_cores_qty) as executor:
                dataset_samples = json.loads(f.read())

                handled_samples = filter_refactorings_by_em(dataset_samples)

                func = partial(handle_commit_example, output_dir=output_dir, token=args.token, classes_dict=d)
                future = executor.map(func, handled_samples, timeout=10000, )
                result = future.result()

                for sample in tqdm(handled_samples, total=len(handled_samples)):
                    try:
                        results = next(result)
                        for res in results:
                            output_df = output_df.append(res, ignore_index=True)
                        output_df.to_csv('new_urls.csv')
                    except Exception:
                        print(traceback.format_exc())
                        continue

    # output_df = output_df.drop_duplicates()
    # output_df.to_csv('new_urls.csv')
