import hashlib
import os
import re
from argparse import ArgumentParser
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Tuple
from javalang.parse import parse
from functools import lru_cache
import aiofiles
import bonobo

from veniq.metrics.ncss.ncss import NCSSMetric
from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.utils.ast_builder import build_ast
from veniq.dataset_collection.dataflow.annotation import annotate
from veniq.dataset_collection.augmentation import collect_info_about_functions_without_params

from veniq.utils.encoding_detector import detect_encoding_of_file, read_text_with_autodetected_encoding


def read_file(filepath: str):
    yield read_text_with_autodetected_encoding(filepath)


def get_list_of_files(path: str):
    test_files = set(Path(path).glob('**/*Test*.java'))
    not_test_files = set(Path(path).glob('**/*.java'))
    for x in not_test_files.difference(test_files):
        yield x


def preprocess(file: str):
    def _remove_comments(string: str):
        pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
        # first group captures quoted strings (double or single)
        # second group captures comments (//single-line or /* multi-line */)
        regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

        def _replacer(match):
            # if the 2nd group (capturing comments) is not None,
            # it means we have captured a non-quoted (real) comment string.
            if match.group(2) is not None:
                # so we will return empty to remove the comment
                return ""
            else:  # otherwise, we will return the 1st group
                return match.group(1)  # captured quoted-string

        return regex.sub(_replacer, string)

    original_text = read_text_with_autodetected_encoding(str(file))
    # remove comments
    text_without_comments = _remove_comments(original_text)
    # remove whitespaces
    text = "\n".join([ll.rstrip() for ll in text_without_comments.splitlines() if ll.strip()])

    yield {'text': text}


@lru_cache()
def create_dirs(output):
    def create_existing_dir(directory):
        if not directory.exists():
            directory.mkdir(parents=True)

    full_dataset_folder = Path(output) / 'full_dataset'
    output_dir = full_dataset_folder / 'output_files'
    create_existing_dir(output_dir)
    input_dir = full_dataset_folder / 'input_files'
    create_existing_dir(input_dir)
    return {'input_dir': input_dir, 'output_dir': output_dir}


def save_text_to_new_file(input_dir: Path, text: str, dct: Dict[Tuple, Tuple], output_dir=None):
    print(dct)
    filename = dct.key()
    # need to avoid situation when filenames are the same
    hash_path = hashlib.sha256(str(filename.parent).encode('utf-8')).hexdigest()
    dst_filename = input_dir / f'{filename.stem}_{hash_path}.java'
    if not dst_filename.parent.exists():
        dst_filename.parent.mkdir(parents=True)
    if not dst_filename.exists():
        with open(dst_filename, 'w', encoding='utf-8') as w:
            w.write(text)
    yield {}


def find_EMS(dct):
    # result_dict = {}
    text: str = dct['text']
    try:
        ast = AST.build_from_javalang(parse(text))
        classes_declaration = [
            ast.get_subtree(node)
            for node in ast.get_root().types
            if node.node_type == ASTNodeType.CLASS_DECLARATION
        ]
        method_declarations: Dict[str, List[ASTNode]] = defaultdict(list)
        for class_ast in classes_declaration:
            class_declaration = class_ast.get_root()
            collect_info_about_functions_without_params(class_declaration, method_declarations)

            methods_list = list(class_declaration.methods) + list(class_declaration.constructors)
            for method_node in methods_list:
                target_node = ast.get_subtree(method_node)
                for method_invoked in target_node.get_proxy_nodes(
                        ASTNodeType.METHOD_INVOCATION):
                    extracted_m_decl = method_declarations.get(method_invoked.member, [])
                    if len(extracted_m_decl) == 1:
                        t = tuple([class_declaration.name, method_invoked.line])
                        yield {t: tuple([ast, text, target_node, method_invoked, extracted_m_decl[0]])}
    except Exception as e:
        print(str(e))


def print_ast(lst):
    print(str(lst))
    yield {}


def pass_params_to_next_node(dirs_dict, em_item: Dict[Tuple, Tuple]):
    class_name, invocation_line = list(em_item.keys())[0]
    ast, text, target_node, method_invoked, extracted_m_decl = list(em_item.values())[0]
    params_dict = {
        'ast': ast,
        'class_name': class_name,
        'invocation_line_number_in_original_file': invocation_line,
        'text': text,
        'target_node': target_node,
        'method_invoked': method_invoked,
        'extracted_m_decl': extracted_m_decl
    }

    yield {**params_dict, **dirs_dict}


def filter_by_ncss(em_info):
    ast = em_info['ast']
    extracted_m_decl = em_info['extracted_m_decl']
    ncss = NCSSMetric().value(ast.get_subtree(extracted_m_decl))
    if ncss > 3:
        em_info['ncss_extracted'] = ncss
        ncss_target_node = NCSSMetric().value(ast.get_subtree(extracted_m_decl))
        em_info['ncss_target'] = ncss_target_node
        yield em_info


def filter_code_duplication(res):
    yield res


def filter_by_second_filter(res):
    yield res


def make_inline(res):
    yield res


def save_file(res):
    yield res


def get_graph(**bonobo_args):
    output_dir = bonobo_args['output']
    dataset_dir = bonobo_args['dir']
    graph = bonobo.Graph()
    dirs = create_dirs(output_dir)
    em_dict = graph >> get_list_of_files(dataset_dir) >> preprocess >> find_EMS
    f_pass_params_to_next_node = partial(pass_params_to_next_node, dirs)
    em_dict >> f_pass_params_to_next_node >> filter_by_ncss >> annotate >> make_inline >> save_filee
    # TODO ignore overridden extracted functions, now it must be a different filter
    return graph


def get_services(**options):
    return {}


if __name__ == '__main__':
    system_cores_qty = os.cpu_count() or 1
    # argument_parser = ArgumentParser()

    # args = argument_parser.parse_args()

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