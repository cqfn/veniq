import json
import os
import subprocess
import traceback
from argparse import ArgumentParser
from collections import defaultdict
from dataclasses import dataclass, asdict
from functools import partial
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from numpy import mean
from pebble import ProcessPool
from tqdm import tqdm

from dataset_collection.augmentation import get_ast_if_possible
from veniq.ast_framework import AST, ASTNodeType
from veniq.ast_framework import ASTNode
from veniq.baselines.semi.create_extraction_opportunities import create_extraction_opportunities
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.baselines.semi.filter_extraction_opportunities import filter_extraction_opportunities
from veniq.baselines.semi.rank_extraction_opportunities import rank_extraction_opportunities, ExtractionOpportunityGroup
from veniq.metrics.ncss.ncss import NCSSMetric
from veniq.utils.ast_builder import build_ast
from veniq.utils.encoding_detector import read_text_with_autodetected_encoding

def _run_command(command) -> subprocess.CompletedProcess:
    print("Command: {}".format(command))
    result = subprocess.run(command, shell=True, capture_output=True)
    print(result.stdout.decode("utf-8"))
    print(result.stderr.decode("utf-8"))
    return result


def _run_command_with_error_check(command) -> subprocess.CompletedProcess:
    print("Command: {}".format(command))
    result = subprocess.run(command, shell=True, capture_output=True)
    if result.stderr:
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=result.args,
            stderr=result.stderr
        )
    # if result.stdout:
    # print("Command Result: {}".format(result.stdout.decode('utf-8')))
    return result


def save_after_file(output_dir, class_name, commit_sha, current_file_name):
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    _run_command_with_error_check(
        f'git show {commit_sha}:{current_file_name} > {file_after_changes}'
    )
    return get_ast_if_possible(file_after_changes)


def save_file_before_changes(
        index_of_first,
        dataset_samples,
        output_dir,
        class_name,
        current_file_name):
    previous_commit_sha = dataset_samples[index_of_first - 1]
    print(f'previous commit-sha is {previous_commit_sha}')
    file_before_changes = Path(output_dir, class_name + '_before.java')
    _run_command_with_error_check(
        f'git show {previous_commit_sha}:"{current_file_name}" > {file_before_changes}')

    return get_ast_if_possible(file_before_changes)


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
        "-s", "--dataset_file",
        help="Json with dataset",
        required=True,
        type=str,
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    with open(args.dataset_file, encoding='utf-8') as f:
        after_files = set()
        before_files = set()
        dataset_samples = json.loads(f.read())
        for sample in dataset_samples:
            repository_url = sample['repository']
            example_id = sample['id']
            commit_sha = sample['sha1']
            output_dir_for_saved_file = output_dir / str(example_id)
            for em in sample['refactorings']:
                if em['type'] == 'Extract Method':
                    description = em.get('description')
                    filename_raw = Path(description.split('in class')[1].replace('.', '/').strip())
                    class_name = filename_raw.parts[-1]
                    file_after_changes = Path(output_dir_for_saved_file, class_name + '_after.java')
                    file_before_changes = Path(output_dir_for_saved_file, class_name + '_before.java')
                    ast_after = get_ast_if_possible(file_after_changes)
                    if not ast_after:
                        continue
                    else:
                        class_ast = [x for x in ast_after.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
                                     if x.name == class_name][0]
                        class_subtree = ast_after.get_subtree(class_ast)
                        methods = defaultdict(list)
                        for x in class_ast.methods:
                            methods[x.name].append(x.name)
                        # remove 'Extract Method private/public' from description
                        extracted_function_name = description.split()[3].strip()
                        functions_number = len(methods[extracted_function_name])
                        if functions_number > 1:
                            # overloaded function, we ignore it
                            print(f'{extracted_function_name} is overloaded in {class_name}')
                            continue
                        else:
                            ast_before = get_ast_if_possible(file_before_changes)
                            if not ast_before:
                                continue
                            else:
                                class_ast = [
                                    x for x in ast_before.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
                                    if x.name == class_name][0]
                                class_subtree = ast_after.get_subtree(class_ast)
                                invocations = [
                                    x for x in class_subtree.get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
                                    if x.member == extracted_function_name]
                                if len(invocations) > 0:
                                    print(f'Duplicated code of {extracted_function_name} in {class_name}')

                    # if file_after_changes not in after_files:
                    #     # print(file_after_changes, file_after_changes.exists())
                    #     get_ast_if_possible(file_after_changes)
                    #     after_files.add(file_after_changes)
                    # if file_before_changes not in before_files:
                    #     # print(file_before_changes, file_before_changes.exists())
                    #     get_ast_if_possible(file_after_changes)
                    #     before_files.add(file_after_changes)
