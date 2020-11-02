import json
import subprocess
import os
from pathlib import Path
import numpy as np

from dataset_collection.augmentation import get_ast_if_possible

git_repo = 'https://github.com/NationalSecurityAgency/ghidra.git'
clone_repo = False
parent_repo_path = Path(os.getcwd())
sample = '027ba3884a805f6736232e2ad399c3cea4ca5aa5'


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


if __name__ == '__main__':
    with open(r'D:\temp\data.json', encoding='utf-8') as f:
        dataset_samples = json.loads(f.read())
        for sample in dataset_samples:
            refactorings = [x for x in sample['refactorings'] if x['type'] == 'Extract Method']
            if refactorings:
                repository_url = sample['repository']
                # repository_url = 'https://github.com/lyriccoder/temp_python.git'
                commit_sha = sample['sha1']
                try:
                    _run_command_with_error_check(f"git clone {repository_url}")
                except subprocess.CalledProcessError as error:
                    errors_string = error.stderr.decode("utf-8")
                    print(errors_string)
                    if "already exists and is not an empty directory" in errors_string:
                        repo_dir = parent_repo_path / errors_string.split('already exists')[0].split()[-1].strip().replace("...", "").replace("'", "")
                        os.chdir(repo_dir)
                        _run_command(f"git checkout master")
                        _run_command(f"git pull --rebase")
                    elif 'Cloning into' in errors_string:
                        path = errors_string.split('Cloning into')[-1].strip().replace("...", "").replace("'", "")
                        repo_dir = parent_repo_path / path
                        print(f'Cloned into: {repo_dir}')

                _run_command(f"git checkout {commit_sha}")
                # get file

                # _run_command(f'git checkout {commit_sha}')
                result: subprocess.CompletedProcess = _run_command_with_error_check(
                    f'git log --full-history --pretty=format:"%H %ad %s'
                )
                if result.stdout:
                    dataset_samples = [x.strip().split()[0] for x in result.stdout.decode('utf-8').split('\n')]
                    print(dataset_samples)

                    for em in refactorings:
                        description = em.get('description')
                        filename_raw = description.split('in class')[1].replace('.', '\\').strip()
                        class_name = filename_raw.split('.')[-1]
                        found_files = list(repo_dir.glob(f'**/{class_name}.java'))
                        for file in found_files:
                            ast_of_new_file = get_ast_if_possible(file)

                            i = np.argwhere(np.array(dataset_samples) == commit_sha)
                            index_of_first = i.min()
                            if not index_of_first:
                                previous_commit_sha = dataset_samples[index_of_first - 1]
                                print(f'previous commit-sha is {previous_commit_sha}')
                                _run_command(f"git checkout {previous_commit_sha}")
                                ast_of_old_file = get_ast_if_possible(file)
                                # get file
                    else:
                        print(f'commit {sample} was not found in {repository_url}')


