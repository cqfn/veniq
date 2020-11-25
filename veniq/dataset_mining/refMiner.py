from collections import OrderedDict
from functools import partial
from pathlib import Path
import os
import subprocess

from pebble import ProcessPool
from tqdm import tqdm

new_dataset = set()
folder_to_analyze = r'/hdd/new_dataset/RefactoringMiner/RefactoringMiner/build/distributions/RefactoringMiner-2.0.1/bin/01'

for folder in Path(folder_to_analyze).iterdir():
    if folder.is_dir():
        # print(folder)
        for subfolder in folder.iterdir():
            if subfolder.is_dir():
                dir = subfolder.parts[-2] + '/' + subfolder.parts[-1]
                #dir = subfolder.parts[-1]
                new_dataset.add(dir)


def run_ref_miner(folder: str):
    p = Path(folder)
    f_err = open(f"{'_'.join(p.parts)}.err.txt")
    f_out = open(f"{'_'.join(p.parts)}.out.txt")
    command = ['./RefactoringMiner', '-a', f"01/{folder}"]
    print(command)
    subprocess.Popen(command, stderr=f_err, stdout=f_out).wait()


system_cores_qty = 4
dir_to_analyze = {}
for x in new_dataset:
    java_files = [x.stat().st_size for x in Path(folder_to_analyze, x).glob('**/*.java')]
    sum_size = sum(java_files)
    dir_to_analyze[x] = sum_size

dir_to_analyze = OrderedDict(sorted(dir_to_analyze.items(), key=lambda x: x[1]))
dir_to_analyze = [x[0] for x in dir_to_analyze]

with ProcessPool(system_cores_qty) as executor:
    future = executor.map(run_ref_miner, dir_to_analyze)
    result = future.result()
    for filename in tqdm(dir_to_analyze):
        next(result)
