import hashlib
import os
import re
from argparse import ArgumentParser
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Any, Dict, List
from javalang.parse import parse

import aiofiles
import bonobo

from veniq.ast_framework import AST, ASTNodeType, ASTNode
from veniq.utils.ast_builder import build_ast
from veniq.dataset_collection.augmentation import collect_info_about_functions_without_params

from veniq.utils.encoding_detector import detect_encoding_of_file, read_text_with_autodetected_encoding


def read_file(filepath: str):
    yield read_text_with_autodetected_encoding(filepath)


def get_list_of_files(path: str):
    test_files = set(Path(path).glob('**/*Test*.java'))
    not_test_files = set(Path(path).glob('**/*.java'))
    print('get_list_of_files')
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


def create_dirs(output):
    def create_existing_dir(directory):
        if not directory.exists():
            directory.mkdir(parents=True)

    full_dataset_folder = Path(output) / 'full_dataset'
    output_dir = full_dataset_folder / 'output_files'
    create_existing_dir(output_dir)
    input_dir = full_dataset_folder / 'input_files'
    create_existing_dir(input_dir)
    yield {'input_dir': input_dir, 'output_dir': output_dir}


def save_text_to_new_file(input_dir: Path, text: str, filename: Path):
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
                        yield {t: tuple([target_node, method_invoked, extracted_m_decl])}
                        # result_dict[method_invoked.line] = [target_node, method_invoked, extracted_m_decl]
        # print({'em_list': result_dict, 'ast': ast})
        # if result_dict:
        #     # print(f' FFF {result_dict}')
        #     return [{'em_list': result_dict, 'ast': ast}]
        # else:
        #     yield {}
    except Exception as e:
        print(str(e))

    # yield {}


def print_ast(lst):
    print(str(lst))
    yield {}


def get_graph(**bonobo_args):
    output_dir = bonobo_args['output']
    dataset_dir = bonobo_args['dir']
    graph = bonobo.Graph()
    # files = get_list_of_files('/mnt/d/temp/dataset/01')
    # files = get_list_of_files(r'd:\\temp\\dataset\\01')
    # print(type(files[0]))
    # f = partial(get_list_of_files, '/mnt/d/temp/dataset/01')

    dirs = graph >> create_dirs(output_dir)
    graph.get_cursor(None) >> save_text_to_new_file
    preprocessed_texts = dirs >> get_list_of_files(dataset_dir) >> preprocess
    # graph.add_chain(
    #     create_dirs(output_dir),
    #     get_list_of_files(dataset_dir),
    #     preprocess
    # )
    # dirs >> save_text_to_new_file
    # preprocessed_texts >> save_text_to_new_file
    result = preprocessed_texts >> find_EMS >> print_ast

    # preprocessed_texts >> save_text_to_new_file
    return result


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
        required=True,
        help="File path to JAVA source code for methods augmentations"
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

    # graph.get_cursor(f) >> print
    # read_file
    # graph.get_cursor(b) >> f >> g
    # files_without_tests

