import json
import os
import subprocess
from argparse import ArgumentParser
from pathlib import Path

import numpy as np

from veniq.dataset_collection.augmentation import get_ast_if_possible

'https://api.github.com/repos/realm/realm-java/commits/6cf596df183b3c3a38ed5dd9bb3b0100c6548ebb'


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
        "-d", "--cloned_repos",
        required=True,
        help="Directory where cloned repos will be saved"
    )
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
    cloned_repos = Path(args.cloned_repos)
    output_dir = Path(args.output_dir)

    if not cloned_repos.exists():
        cloned_repos.mkdir(parents=True)

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    with open(args.dataset_file, encoding='utf-8') as f:
        dataset_samples = json.loads(f.read())
        for sample in dataset_samples:
            refactorings = [x for x in sample['refactorings'] if x['type'] == 'Extract Method']
            if refactorings:
                repository_url = sample['repository']
                example_id = sample['id']
                commit_sha = sample['sha1']
                repo_dir = cloned_repos / Path(repository_url).stem
                result = _run_command(f"git -C {str(cloned_repos)} clone {repository_url}")
                # Failed to connect to github.com port
                if result != 128:
                    os.chdir(repo_dir)
                    print(f'Switched to {repo_dir}')
                    result: subprocess.CompletedProcess = _run_command_with_error_check(
                        f'git log --full-history --pretty=format:"%H %ad %s"'
                    )
                    if result.stdout:
                        dataset_samples = [x.strip().split()[0] for x in result.stdout.decode('utf-8').split('\n')]
                        # print(dataset_samples)
                        saved_files = set()

                        for em in refactorings:
                            description = em.get('description')
                            filename_raw = description.split('in class')[1].replace('.', '\\').strip()
                            class_name = filename_raw.split('\\')[-1]
                            found_files = list(repo_dir.glob(f'**/{class_name}.java'))
                            output_dir_for_saved_file = output_dir / str(example_id)
                            if found_files:
                                current_file_name = found_files[0].relative_to(repo_dir).as_posix()
                                if current_file_name in saved_files:
                                    continue

                                file_after_changes = Path(output_dir_for_saved_file, class_name + '_after.java')

                                ast_of_new_file = save_after_file(
                                    output_dir_for_saved_file,
                                    class_name,
                                    commit_sha,
                                    current_file_name
                                )
                                if ast_of_new_file:
                                    i = np.argwhere(np.array(dataset_samples) == commit_sha)
                                    index_of_first = int(i.min())
                                    if index_of_first:
                                        ast_of_old_file = save_file_before_changes(
                                            index_of_first,
                                            dataset_samples,
                                            output_dir_for_saved_file,
                                            class_name,
                                            current_file_name)

                                        if ast_of_old_file:
                                            saved_files.add(current_file_name)

                                else:
                                    print(f'File {file_after_changes} was not found')
