from dataclasses import dataclass
from typing import Optional, Tuple

import pandas as pd

from veniq.utils.encoding_detector import read_text_with_autodetected_encoding
from veniq.ast_framework import ASTNodeType
from veniq.dataset_collection.augmentation import method_body_lines
from veniq.utils.ast_builder import build_ast
from veniq.ast_framework import AST
from pathlib import Path
from ast import literal_eval
from veniq.dataset_mining.code_similarity import is_similar_functions, get_after_lines

current_directory = Path(r'D:\temp\dataset_colelction_refactoring\12_07')

df = pd.read_csv('temp_filtered.csv')
df['real_extractions'] = df['real_extractions'].apply(literal_eval)
for index, row in df.iterrows():
    target_function_name = row['function_name_with_LM']
    real_extractions = row['real_extractions']
    class_name = row['class_name']
    filepath_after = str(current_directory / row['filepath_saved'])
    filepath_before = filepath_after.replace('_after.java', '_before.java')
    extracted_function_name = row['function_inlined']
    function_target_start_line = row['function_target_start_line']
    function_target_end_line = row['function_target_end_line']
    ast_after = AST.build_from_javalang(build_ast(filepath_after))
    ast_before = AST.build_from_javalang(build_ast(filepath_before))
    class_ = [x for x in ast_after.get_proxy_nodes(
        ASTNodeType.CLASS_DECLARATION,
        ASTNodeType.ENUM_DECLARATION,
        ASTNodeType.INTERFACE_DECLARATION
    ) if x.name == class_name][0]
    target_modified = [x for x in class_.methods if x.name == target_function_name][0]
    body_start_line_mdfd, body_end_line_mdfd = method_body_lines(
        target_modified,
        Path(filepath_after)
    )

    _, lines_matched, _, _, how_similar_btw_extractions_target_modified, _ = is_similar_functions(
        str(current_directory / filepath_before),
        str(current_directory / filepath_after),
        [[function_target_start_line + 1, function_target_end_line]],
        (body_start_line_mdfd, body_end_line_mdfd)
    )
    exc = [' ', '{', '}', '']
    after_lines = get_after_lines(
        exc,
        filepath_after,
        (body_start_line_mdfd, body_end_line_mdfd))

    # we add 1 line since invocation of extracted method
    # will differ every time
    lines_matched += 1
    target_modified_size = len(after_lines[0])
    df['similarity_modified'] = float(lines_matched) / target_modified_size
    df.to_csv('filtered_target_modified.csv')
