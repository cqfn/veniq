from pathlib import Path

import pandas as pd

from baselines.semi.create_extraction_opportunities import create_extraction_opportunities
from baselines.semi.extract_semantic import extract_method_statements_semantic
from baselines.semi.filter_extraction_opportunities import filter_extraction_opportunities
from baselines.semi.rank_extraction_opportunities import rank_extraction_opportunities
from utils.ast_builder import build_ast
from veniq.ast_framework import AST, ASTNodeType
from random import choice


def _print_extraction_opportunities(
        method_ast: AST):
    statements_semantic = extract_method_statements_semantic(method_ast)
    extraction_opportunities = create_extraction_opportunities(statements_semantic)
    filtered_extraction_opportunities = filter_extraction_opportunities(
        extraction_opportunities, statements_semantic, method_ast
    )
    extraction_opportunities_groups = rank_extraction_opportunities(
        statements_semantic, filtered_extraction_opportunities
    )

    # print(
    #     f"Extraction opportunities groups of method {method_name} in class {class_name} in file {filepath}:"
    # )

    # for extraction_opportunity_group in extraction_opportunities_groups:
    #     print(f"\tExtraction opportunities group with scope {extraction_opportunity_group.benifit}:")
    #     for extraction_opportunity, benifit in extraction_opportunity_group.opportunities:
    #         print(f"\t\tExtraction opportunity with score {benifit}:")
    #         for statement in extraction_opportunity:
    #             print(f"\t\t\t{statement.node_type} on line {statement.line}")
    return extraction_opportunities_groups


if __name__ == '__main__':
    dir_with_dataset = Path(r'D:\temp\dataset_colelction_refactoring\small_dataset')
    df = pd.read_csv(Path(dir_with_dataset) / r'out.csv')
    failed_cases_in_SEMI_algorithm = 0
    failed_cases_in_validation_examples = 0
    matched_cases = 0
    no_opportunity_chosen = 0
    total_number = df.shape[0]
    for row in df.iterrows():
        start_line = row[1]['start_line']
        end_line = row[1]['end_line']
        src_filename = row[1]['output_filename']
        class_name = row[1]['className']

        print(class_name)
        try:
            ast = AST.build_from_javalang(build_ast(dir_with_dataset / src_filename))
        except Exception as e:
            failed_cases_in_validation_examples += 1

        function_to_analyze = row[1]['invocation function name']
        for class_decl in ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION):
            class_ast = ast.get_subtree(class_decl)
            if class_decl.name != class_name:
                continue

            for method_decl in class_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION):
                if method_decl.name != function_to_analyze:
                    continue

                try:
                    opport = _print_extraction_opportunities(
                        ast.get_subtree(method_decl)
                    )
                    if opport:
                        best_group = opport[0]
                        best_opportunity, benefit = choice(list(best_group.opportunities))
                        lines = [node.line for node in best_opportunity]
                        start_line_opportunity = min(lines)
                        end_line_opportunity = max(lines)
                        if (start_line == start_line_opportunity) and (end_line == end_line_opportunity):
                            matched_cases += 1
                    else:
                        no_opportunity_chosen += 0
                        print(class_decl.name, method_decl.name)

                except Exception as e:
                    failed_cases_in_SEMI_algorithm += 1

                break

    matched = (failed_cases_in_SEMI_algorithm + failed_cases_in_validation_examples
               + matched_cases + no_opportunity_chosen)
    print(float(matched) / total_number)
