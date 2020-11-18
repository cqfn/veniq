import os.path
import shutil
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--csv",
        help="Dataset csv",
        required=True
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    for x in df.iterrows():
        f_out = Path(x[1]['output_filename'])
        print(f_out, Path(os.getcwd(), f_out.name))
        shutil.copyfile(f_out, Path(os.getcwd(), f_out.name))
