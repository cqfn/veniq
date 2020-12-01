import json
import os
import traceback
from argparse import ArgumentParser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Tuple, Any

import pandas as pd
from pebble import ProcessPool
from sortedcontainers import SortedSet
from tqdm import tqdm

from veniq.utils.encoding_detector import read_text_with_autodetected_encoding


@dataclass
class RowResult:
    filename: str
    repository: str
    lines: Tuple[Tuple[int]]
    sha1: str
    description: str
    url: str


def find_em_items(file: Path):
    text = read_text_with_autodetected_encoding(str(file))
    json_dict = json.loads(text)
    results = []

    for x in json_dict['commits']:
        refactorings = x.get('refactorings')
        if refactorings:
            for ref in refactorings:
                if ref.get('type') == 'Extract Method':
                    res = RowResult(
                        filename='',
                        repository=x['repository'],
                        sha1=x['sha1'],
                        lines=tuple(),  # type: ignore
                        description=ref.get('description'),
                        url=x['url']
                    )
                    ref_items = [
                        x for x in ref.get('leftSideLocations', [])
                        if x.get('codeElementType') != "METHOD_DECLARATION"
                    ]
                    lines_list_of_lists = find_lines(ref_items)
                    res.lines = lines_list_of_lists  # type: ignore
                    if ref_items:
                        res.filename = ref_items[0]['filePath']
                    results.append(res)

    return results


def find_lines(ref_items: List[Dict[str, any]]) -> Tuple[Tuple[Any, ...], ...]:  # type: ignore

    def add_to_list(small_list, global_list):
        range_extraction = tuple([small_list[0], small_list[-1]])
        global_list.append(range_extraction)

    lines = SortedSet()
    for ref_block in ref_items:
        for j in range(ref_block['startLine'], ref_block['endLine'] + 1):  # type: ignore
            lines.add(j)
    prev = lines[0]
    cur_list = [prev]
    lines_list_of_lists: List[Tuple[int, int]] = []
    for x in lines[1:]:
        diff = x - prev
        prev = x
        if diff > 1:
            add_to_list(cur_list, lines_list_of_lists)
            cur_list = [x]
        else:
            cur_list.append(x)

    add_to_list(cur_list, lines_list_of_lists)
    return tuple(lines_list_of_lists)


if __name__ == '__main__':

    system_cores_qty = os.cpu_count() or 1
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dir",
        required=True,
        help="File path where json files of RefMiner2.0 are located"
    )
    parser.add_argument(
        "-o", "--csv_output",
        help="File with output results",
        default='ref_miner.csv'
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
    input_dir = Path(args.dir)
    files = [x for x in input_dir.iterdir() if x.is_file() and x.name.endswith('out.txt')]
    df = pd.DataFrame(columns=list(RowResult.__annotations__.keys()))

    with ProcessPool(system_cores_qty) as executor:
        future = executor.map(find_em_items, files)
        result = future.result()

        for filename in tqdm(files):
            try:
                single_file_features = next(result)
                if single_file_features:
                    for i in single_file_features:
                        df = df.append(asdict(i), ignore_index=True)
                    df.to_csv(args.csv_output)

            except Exception:
                traceback.print_exc()
    df = df.drop_duplicates()
    df.to_csv(args.csv_output)
