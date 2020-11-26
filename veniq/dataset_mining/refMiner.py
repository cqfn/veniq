import os
import subprocess
from argparse import ArgumentParser
from collections import OrderedDict
from pathlib import Path

from pebble import ProcessPool
from tqdm import tqdm


def run_ref_miner(folder: str):
    p = Path(folder)
    f_err = open(f"{'_'.join(p.parts)}.err.txt")
    f_out = open(f"{'_'.join(p.parts)}.out.txt")
    command = ['./RefactoringMiner', '-a', f"01/{folder}"]
    print(command)
    subprocess.Popen(command, stderr=f_err, stdout=f_out).wait()


if __name__ == '__main__':  # noqa: C901
    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dir",
        required=True,
        help="File path to JAVA projects"
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

    args = parser.parse_args()
    new_dataset = set()

    for folder in Path(args.dir).iterdir():
        if folder.is_dir():
            for subfolder in folder.iterdir():
                if subfolder.is_dir():
                    dir_name = subfolder.parts[-2] + '/' + subfolder.parts[-1]
                    new_dataset.add(dir_name)

    dir_to_analyze = {}
    for x in new_dataset:
        java_files = [x.stat().st_size for x in Path(args.dir, x).glob('**/*.java')]
        sum_size = sum(java_files)
        dir_to_analyze[x] = sum_size

    dir_to_analyze = OrderedDict(sorted(dir_to_analyze.items(), key=lambda x: x[1]))
    dir_to_analyze = [x[0] for x in dir_to_analyze]

    with ProcessPool(system_cores_qty) as executor:
        future = executor.map(run_ref_miner, dir_to_analyze)
        result = future.result()
        for filename in tqdm(dir_to_analyze):
            next(result)
