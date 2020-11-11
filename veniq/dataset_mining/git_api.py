import json
import os
import time
import traceback
from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Dict, Any
from multiprocessing import Process, Manager
import pandas as pd
import requests
from bs4 import BeautifulSoup
from lxml import etree
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
    str_filename = description.split('in class')[1].replace('.', '/').strip() + '.java'
    filename_raw = Path(str_filename)
    class_name = filename_raw.stem
    classes = classes_dict.get(commit_sha_after, set())
    if class_name not in classes:
        add_to_dict_set(commit_sha_after, class_name, classes_dict)
        commit_url = f'https://api.github.com/repos/{repo_name}/commits/{commit_sha_after}'
        headers = {f"Authorization": f"token {token}"}
        s = requests.Session()
        resp = s.get(commit_url, headers=headers)
        json_resp = resp.json()
        output_dir_for_saved_file = output_dir / str(example_id)
        if not output_dir_for_saved_file.exists():
            output_dir_for_saved_file.mkdir(parents=True)

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
        files = json_resp.get('files', [])
        if not files:
            d['error'] = resp.content
            print(resp.content, resp.status_code, commit_url, resp.status_code)

        files_after_arr = search_filenames_in_commit(filename_raw, files)
        if not files_after_arr:
            d['error'] = 'File_before was not found in commit'

        for file_item in files_after_arr:
            url_after = file_item['raw_url']
            content_after = s.get(url_after, headers=headers).content
            file_after_changes = Path(
                output_dir_for_saved_file,
                Path(file_item['filename']).stem + '_after.java')
            d['file_name_after'] = str(file_after_changes)
            with open(file_after_changes, 'wb') as w:
                w.write(content_after)
                d['downloaded_after'] = True

            commit_sha_before = get_previous_commit(
                commit_sha_after,
                file_item['filename'],
                repo_name,
                d,
                s,
                headers
            )
            if commit_sha_before:
                d['commit_before'] = commit_sha_before
                commit_url = f'https://api.github.com/repos/{repo_name}/commits/{commit_sha_before}'
                resp_before = s.get(commit_url, headers=headers)
                resp_before_json = resp_before.json()
                files_before = resp_before_json.get('files', [])
                if not files_before:
                    print(resp_before.content, resp_before.status_code, commit_url)

                files_after_arr = search_filenames_in_commit(filename_raw, files_before)

                for file_item_before in files_after_arr:
                    url_before = file_item_before['raw_url']
                    content_before = s.get(url_before, headers=headers).content
                    file_before_changes = Path(
                        output_dir_for_saved_file,
                        Path(file_item_before['filename']).stem + '_before.java')
                    d['file_name_before'] = str(file_before_changes)
                    with open(file_before_changes, 'wb') as w:
                        w.write(content_before)
                        d['downloaded_before'] = True

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
    files_after_arr = find_filename(filename_raw, files)
    if not files_after_arr:
        # finds subclass
        files_after_arr = find_filename(Path(*filename_raw.parts[:-1]), files)
    if not files_after_arr:
        # finds subclass of subclass
        files_after_arr = find_filename(Path(*filename_raw.parts[:-2]), files)
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
            d = manager.dict()
            with ProcessPool(system_cores_qty) as executor:
                dataset_samples = json.loads(f.read())

                handled_samples = filter_refactorings_by_em(dataset_samples)

                print(1)
                f = partial(handle_commit_example, output_dir=output_dir, token=args.token, classes_dict=d)
                future = executor.map(f, handled_samples, timeout=10000, )
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
