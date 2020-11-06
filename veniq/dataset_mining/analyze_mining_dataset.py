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
from pebble import ProcessPool
from tqdm import tqdm

from dataset_collection.augmentation import get_ast_if_possible
from veniq.ast_framework import AST, ASTNodeType
from veniq.ast_framework import ASTNode


@dataclass
class RowResult:
    file_name_before: str
    file_name_after: str
    has_duplicated_code: bool
    error_string: str
    overloaded: int
    invoked_times: int


def check_duplication(
        sample: Dict[str, Any],
        output_dir: Path) -> List[RowResult]:

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
            file_after_changes = Path(output_dir_for_saved_file, class_name + '_after.java')
            file_before_changes = Path(output_dir_for_saved_file, class_name + '_before.java')
            ast_before = get_ast_if_possible(file_before_changes)
            r = RowResult(
                file_name_before=str(file_before_changes),
                file_name_after=str(file_after_changes),
                has_duplicated_code=False,
                error_string='',
                invoked_times=1,
                overloaded=0
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
                    functions_number = len(methods[extracted_function_name])
                    if functions_number > 1:
                        # overloaded function, we ignore it
                        r.error_string = f'{extracted_function_name} is overloaded in {class_name}'
                        print(r.error_string)
                        r.overloaded = functions_number
                        results.append(r)
                        continue
                    elif functions_number == 0:
                        r.error_string = f'The name of parsed function {extracted_function_name} ' \
                                         f'was not found in class {class_name}. It\'s an error'
                        results.append(r)
                        print(r.error_string)
                    else:
                        invocations = [
                            x for x in class_subtree_before.get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
                            if x.member == extracted_function_name]
                        if len(invocations) > 1:
                            r.error_string = f'Function {extracted_function_name} ' \
                                             f'is invoked {len(invocations)} times in before class {class_name}.'
                            results.append(r)
                            r.invoked_times = len(invocations)
                            print(r.error_string)
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
    if len(invocations) > 0:
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
        with ProcessPool(system_cores_qty) as executor:
            check_duplication_f = partial(
                check_duplication,
                output_dir=output_dir
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
