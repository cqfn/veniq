import json
import os
import subprocess
from argparse import ArgumentParser
from pathlib import Path

from tqdm import tqdm


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
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--cloned_repos",
        required=True,
        help="Directory where cloned repos will be saved"
    )
    parser.add_argument(
        "-s", "--dataset_file",
        help="Json with dataset",
        required=True,
        type=str,
    )
    args = parser.parse_args()
    cloned_repos = Path(args.cloned_repos)

    if not cloned_repos.exists():
        cloned_repos.mkdir(parents=True)

    with open(args.dataset_file, encoding='utf-8') as f:
        dataset_samples = json.loads(f.read())
        repos_urls = set()
        for sample in dataset_samples:
            refactorings = [x for x in sample['refactorings'] if x['type'] == 'Extract Method']
            if refactorings:
                repos_urls.add(sample['repository'])
        print(len(repos_urls))
        for repo in tqdm(repos_urls):
            repo_dir = cloned_repos / Path(repo).stem
            print(repo_dir)
            result = _run_command(f"git -C {str(cloned_repos)} clone {repo}")
