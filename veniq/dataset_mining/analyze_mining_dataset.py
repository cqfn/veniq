import json
import os
import traceback
from argparse import ArgumentParser
from collections import defaultdict
from dataclasses import dataclass, asdict
from functools import partial
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import requests
from pebble import ProcessPool
from tqdm import tqdm

from dataset_mining.git_api import search_filenames_in_commit
from veniq.dataset_collection.augmentation import get_ast_if_possible
from veniq.ast_framework import AST, ASTNodeType
from veniq.ast_framework import ASTNode


@dataclass
class RowResult:
    id: int
    file_name_before: str
    file_name_after: str
    has_duplicated_code: bool
    error_string: str
    overloaded: int
    invoked_times_before_changes: int
    invoked_times_after_changes: int
    function_name: str
    class_name: str


def check_duplication(
        sample: Dict[str, Any],
        output_dir: Path,
        token: str
) -> List[RowResult]:

    results: List[RowResult] = []
    # repository_url = sample['repository']
    example_id = sample['id']
    # commit_sha = sample['sha1']
    output_dir_for_saved_file = output_dir / str(example_id)
    for em in sample['refactorings']:
        if em['type'] == 'Extract Method':
            description = em.get('description')
            filename_raw = Path(description.split('in class')[1].replace('.', '/').strip())
            class_name = filename_raw.parts[-1]

            repository_url = sample['repository']
            report_part_1 = Path(repository_url).parts[2:-1]
            report_part_2 = Path(repository_url).parts[-1].replace('.git', '')
            repo_name = Path(*report_part_1, report_part_2).as_posix()
            session = requests.Session()
            commit_sha = sample['sha1']
            commit_url = f'https://api.github.com/repos/{repo_name}/commits/{commit_sha}'
            headers = {f"Authorization": f"token {token}"}
            resp = session.get(commit_url, headers=headers)
            resp_json = resp.json()
            files = resp_json.get('files', [])
            if not files:
                print(f'{resp.status_code}: {resp.content}')

            found_files_in_commit = search_filenames_in_commit(filename_raw, files)
            if not found_files_in_commit:
                print(f'Files not found in {commit_sha}')
            else:
                file_item = found_files_in_commit[0]
                real_class_name = Path(file_item['filename']).stem

                file_after_changes = Path(output_dir_for_saved_file, real_class_name + '_after.java')
                file_before_changes = Path(output_dir_for_saved_file, real_class_name + '_before.java')
                ast_before = get_ast_if_possible(file_before_changes)
                r = RowResult(
                    id=example_id,
                    file_name_before=str(file_before_changes),
                    file_name_after=str(file_after_changes),
                    has_duplicated_code=False,
                    error_string='',
                    invoked_times_before_changes=0,
                    invoked_times_after_changes=0,
                    overloaded=0,
                    class_name=class_name,
                    function_name=''
                )

                if not ast_before:
                    r.error_string = 'Cannot parse ast before'
                    print(r.error_string)
                    results.append(r)
                    continue
                else:
                    classes_ast = [
                        x for x in ast_before.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
                        if x.name == class_name]
                    if not classes_ast:
                        r.error_string = f'File {file_before_changes} is empty'
                        results.append(r)
                        print(r.error_string)
                    else:
                        class_ast_before = classes_ast[0]
                        class_subtree_before = ast_before.get_subtree(class_ast_before)
                        methods = defaultdict(list)
                        for x in class_ast_before.methods:
                            methods[x.name].append(x.name)
                        # remove 'Extract Method private/public' from description
                        extracted_function_name = description.split()[3].strip().split('(')[0]
                        r.function_name = extracted_function_name
                        functions_number = len(methods[extracted_function_name])
                        if functions_number > 1:
                            # overloaded function, we ignore it
                            r.error_string = f'{extracted_function_name} is overloaded in {class_name}'
                            # print(r.error_string)
                            r.overloaded = functions_number
                            results.append(r)
                            continue
                        else:
                            invocations_before = [
                                x for x in class_subtree_before.get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
                                if x.member == extracted_function_name]
                            r.invoked_times_before_changes = len(invocations_before)
                            if len(invocations_before) > 1:
                                r.error_string = f'Function {extracted_function_name} ' \
                                                 f'is invoked {len(invocations_before)} times in before class {class_name}.'
                                results.append(r)
                                # print(r.error_string)
                            else:
                                ast_after = get_ast_if_possible(file_after_changes)
                                if not ast_after:
                                    r.error_string = 'Cannot parse ast after'
                                    print(r.error_string)
                                    results.append(r)
                                    continue
                                else:
                                    classes_ast = [
                                        x for x in ast_after.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
                                        if x.name == class_name]
                                    if not classes_ast:
                                        r.error_string = f'File {file_after_changes} is empty'
                                        results.append(r)
                                        print(r.error_string)
                                    else:
                                        check_after_file(
                                            ast_after,
                                            class_name,
                                            classes_ast,
                                            extracted_function_name,
                                            r,
                                            results)
    return results


def check_after_file(
        ast_after: AST,
        class_name: str,
        classes_ast: List[ASTNode],
        extracted_function_name: str,
        r: RowResult,
        results: List[RowResult]):
    class_ast_after = classes_ast[0]
    class_subtree_before = ast_after.get_subtree(class_ast_after)
    invocations = [
        x for x in class_subtree_before.get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
        if x.member == extracted_function_name]
    r.invoked_times_after_changes = len(invocations)
    if len(invocations) > 1:
        r.has_duplicated_code = True
        results.append(r)
        # print(f'Duplicated code of {extracted_function_name} in {class_name}')
    elif len(invocations) == 0:
        r.error_string = 'The name of invoked parsed function ' \
                         f'{extracted_function_name} was not found ' \
                         f'in class {class_name}. It\'s an error'
        print(r.error_string)
        results.append(r)
    else:
        r.has_duplicated_code = False
        results.append(r)
        # print(f'1 invocation')


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
        help="Token",
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
        "-d", "--dataset_file",
        help="Json with dataset",
        required=True,
        type=str,
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    dataset_file = Path(args.dataset_file)

    output_df = pd.DataFrame(columns=list(RowResult.__annotations__.keys()))

    with open(args.dataset_file, encoding='utf-8') as f:
        dataset_samples = json.loads(f.read())
        with ProcessPool(1) as executor:
            check_duplication_f = partial(
                check_duplication,
                output_dir=output_dir,
                token=args.token
            )
            future = executor.map(check_duplication_f, dataset_samples, )
            result = future.result()

            for sample in tqdm(dataset_samples, total=len(dataset_samples)):
                try:
                    results: List[RowResult] = next(result)
                    for res in results:
                        output_df = output_df.append(asdict(res), ignore_index=True)
                    output_df.to_csv('output_mining.csv')

                except Exception:
                    print(traceback.format_exc())
                    continue
