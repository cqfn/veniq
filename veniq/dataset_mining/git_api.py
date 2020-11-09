import json
import os
import subprocess
import traceback
from argparse import ArgumentParser
from dataclasses import asdict
from functools import partial
from pathlib import Path, PurePath
import requests
import numpy as np
import pandas as pd
from lxml import etree
import time

from pebble import ProcessPool
from tqdm import tqdm

from veniq.dataset_collection.augmentation import get_ast_if_possible
from bs4 import BeautifulSoup


def get_before_url(file_item):
    url_after = file_item['blob_url'].replace('blob', 'commits')
    html_history = requests.get(url_after).content
    soup = BeautifulSoup(html_history, 'html.parser')
    dom = etree.HTML(str(soup))
    links = dom.xpath('//p[@class="mb-1"]/a')
    try:
        href = links[1].attrib['href']
        commit_sha_before = Path(href).parts[-1].split('#')[0]
        return commit_sha_before
    except:
        print(f'cannot get {url_after}')
        commit_sha_before = ''
    return commit_sha_before


def handle_commit_example(sample, token, output_dir):
    refactorings = [x for x in sample['refactorings'] if x['type'] == 'Extract Method']
    results = []
    proxies = {"https": "182.52.90.42", "http": "167.71.5.83"}

    if refactorings:
        repository_url = sample['repository']
        example_id = sample['id']
        commit_sha = sample['sha1']
        report_part_1 = Path(repository_url).parts[2:-1]
        report_part_2 = Path(repository_url).parts[-1].replace('.git', '')
        repo_name = Path(*report_part_1, report_part_2).as_posix()
        classes = set()
        for em in refactorings:
            description = em.get('description')
            filename_raw = Path(description.split('in class')[1].replace('.', '/').strip())
            class_name = filename_raw.parts[-1]
            if class_name not in classes:
                classes.add(class_name)
                commit_url = f'https://api.github.com/repos/{repo_name}/commits/{commit_sha}'
                headers = {f"Authorization": f"token {token}"}
                s = requests.Session()
                resp = s.get(commit_url, headers=headers)
                json_resp = resp.json()
                # time.sleep(10)
                output_dir_for_saved_file = output_dir / str(example_id)
                if not output_dir_for_saved_file.exists():
                    output_dir_for_saved_file.mkdir(parents=True)

                d = {
                    'repo_url': repository_url,
                    'file_name_before': '',
                    'file_name_after': '',
                    'downloaded_after': False,
                    'downloaded_before': False,
                    'class_name': class_name,
                    'commit_before': '',
                    'commit_after': commit_sha
                }
                files = json_resp.get('files', [])
                if not files:
                    print(resp.content, resp.status_code, commit_url)

                files_after_arr = [x for x in files if x['filename'].find(filename_raw.as_posix()) > -1]
                if not files_after_arr:
                    filename_raw_after = Path(*filename_raw.parts[:-1])
                    files_after_arr = [x for x in files if x['filename'].find(filename_raw_after.as_posix()) > -1]
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

                    commit_sha_before = get_before_url(file_item)
                    if commit_sha_before:
                        d['commit_before'] = commit_sha_before
                        commit_url = f'https://api.github.com/repos/{repo_name}/commits/{commit_sha_before}'
                        resp_before = s.get(commit_url, headers=headers)
                        resp_before_json = resp_before.json()
                        # time.sleep(10)
                        files_before = resp_before_json.get('files', [])
                        if not files_before:
                            print(resp_before.content, resp_before.status_code, commit_url)

                        files_before_arr = [x for x in files_before if x['filename'].find(filename_raw.as_posix()) > -1]
                        if not files_before_arr:
                            filename_raw_before = Path(*filename_raw.parts[:-1])
                            files_after_arr = [
                                x for x in files if
                                x['filename'].find(filename_raw_before.as_posix()) > -1]

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
            'repo_url',
            'class_name',
            'file_name_after',
            'file_name_before',
            'downloaded_after',
            'downloaded_before',
            'commit_before',
            'commit_after'
        ]
    )
    with open(args.dataset_file, encoding='utf-8') as f:
        with ProcessPool(system_cores_qty) as executor:
            dataset_samples = json.loads(f.read())
            f = partial(handle_commit_example, output_dir=output_dir, token=args.token)
            future = executor.map(f, dataset_samples, timeout=10000, )
            result = future.result()

            for sample in tqdm(dataset_samples, total=len(dataset_samples)):
                try:
                    results = next(result)
                    for res in results:
                        output_df = output_df.append(res, ignore_index=True)
                    output_df.to_csv('new_urls.csv')
                except Exception:
                    print(traceback.format_exc())
                    continue

    output_df = output_df.drop_duplicates()
    output_df.to_csv('new_urls.csv')
