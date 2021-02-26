import os
from functools import lru_cache
from functools import partial
from pathlib import Path
from typing import Dict, Tuple

import bonobo

from veniq.dataset_collection.dataflow.post_process import post_process_data
from veniq.dataset_collection.dataflow.data_aggregation import aggregate
from veniq.dataset_collection.dataflow.save_file import save_input_file, save_output_file
from veniq.dataset_collection.dataflow.preprocess import preprocess, create_existing_dir
from veniq.dataset_collection.dataflow.annotation import annotate
from veniq.dataset_collection.dataflow.find_inline_methods import find_EMs
from veniq.dataset_collection.dataflow.inlining import inline
from veniq.dataset_collection.dataflow.ncss_filter import filter_by_ncss


def get_list_of_files(path: str):
    test_files = set(Path(path).glob('**/*Test*.java'))
    not_test_files = set(Path(path).glob('**/*.java'))
    for x in not_test_files.difference(test_files):
        yield x


@lru_cache()
def create_dirs(output):
    full_dataset_folder = Path(output) / 'full_dataset'
    output_dir = full_dataset_folder / 'output_files'
    create_existing_dir(output_dir)
    input_dir = full_dataset_folder / 'input_files'
    create_existing_dir(input_dir)
    return {'input_dir': str(input_dir), 'output_dir': str(output_dir)}


def add_additional_params_to_output(dirs_dict: Dict[str, str], dataset_dir: str, em_item: Dict[Tuple, Tuple]):
    original_filename, class_name, invocation_line = list(em_item.keys())[0]
    ast, text, target_node, method_invoked, extracted_m_decl = list(em_item.values())[0]
    params_dict = {
        'ast': ast,
        'class_name': class_name,
        'invocation_line_number_in_original_file': invocation_line,
        'text': text,
        'target_node': target_node,
        'method_invoked': method_invoked,
        'extracted_m_decl': extracted_m_decl,
        'original_filename': original_filename,
        'dataset_dir': dataset_dir
    }

    yield {**params_dict, **dirs_dict}


def get_graph(**bonobo_args):
    output_dir = bonobo_args['output']
    dataset_dir = bonobo_args['dir']
    graph = bonobo.Graph()
    dirs = create_dirs(output_dir)

    f_pass_params_to_next_node = partial(add_additional_params_to_output, dirs, dataset_dir)
    res = graph >> get_list_of_files(dataset_dir) >> preprocess >> find_EMs >> \
        f_pass_params_to_next_node >> save_input_file >> filter_by_ncss >> \
        annotate >> bonobo.Filter(lambda *s: s[1] != 'NO_IGNORED_CASES') >> \
        inline >> save_output_file >> post_process_data >> aggregate

    return res


def get_services(**options):
    return {}


if __name__ == '__main__':
    system_cores_qty = os.cpu_count() or 1
    bonobo_parser = bonobo.get_argument_parser()
    bonobo_parser.add_argument(
        "-d",
        "--dir",
        # required=True,
        help="File path to JAVA source code for methods augmentations",
        default='/d/mnt/temp/dataset/01'
    )
    bonobo_parser.add_argument(
        "-o", "--output",
        help="Path for file with output results",
        default='augmented_data'
    )
    bonobo_parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=system_cores_qty - 1,
        help="Number of processes to spawn. "
             "By default one less than number of cores. "
             "Be careful to raise it above, machine may stop responding while creating dataset.",
    )
    bonobo_parser.add_argument(
        "-z", "--zip",
        action='store_true',
        help="To zip input and output files."
    )
    bonobo_parser.add_argument(
        "-s", "--small_dataset_size",
        help="Number of files in small dataset",
        default=100,
        type=int,
    )
    with bonobo.parse_args(bonobo_parser) as options:
        bonobo.run(
            get_graph(**options),
            services=get_services(**options),
        )
