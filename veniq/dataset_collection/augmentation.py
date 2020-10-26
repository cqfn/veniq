from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

from veniq.baselines.semi.create_extraction_opportunities import create_extraction_opportunities
from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
from veniq.baselines.semi.filter_extraction_opportunities import filter_extraction_opportunities
from veniq.baselines.semi.rank_extraction_opportunities import rank_extraction_opportunities
from veniq.dataset_collection.augmentation import method_body_lines
from veniq.utils.ast_builder import build_ast
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
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--dataset_dir",
        help="Path for file with output results",
        required=True
    )
    parser.add_argument(
        "-i", "--csv_input",
        help="Path for csv"
    )
    args = parser.parse_args()
    dataset_dir = Path(args.dataset_dir)
    csv_dataset_filename = Path(args.csv_input)
    df = pd.read_csv(csv_dataset_filename)
    df_is_parsed = df[df['can_be_parsed']]
    failed_cases_in_SEMI_algorithm = 0
    failed_cases_in_validation_examples = 0
    matched_cases = 0
    no_opportunity_chosen = 0
    total_number = df.shape[0]
    matched_percent = 0
    # f = r'D:\temp\dataset_colelction_refactoring\small_dataset\output_files\SecurityConstraintPanel_setValue_192.java'
    # ast = AST.build_from_javalang(build_ast(f))
    # class_t = [x for x in ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION) if x.name == 'SecurityConstraintPanel'][0]
    # method_decl = [x for x in ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION) if x.name == 'refillUserDataConstraint'][0]
    # body_start_line, body_end_line = method_body_lines(method_decl, f)
    # print(body_start_line, body_end_line)
    iteration_number = 0

    for row in df_is_parsed.iterrows():
        iteration_number += 1
        start_line_of_invocation_occurred = row[1]['start_line_of_function_where_invocation_occurred']
        start_line_of_invoked_function = row[1]['invocation_method_start_line']
        end_line_of_invoked_function = row[1]['invocation_method_end_line']
        end_line_of_invocation_occurred = end_line_of_invoked_function - start_line_of_invoked_function
        lines_inserted = end_line_of_invocation_occurred - start_line_of_invocation_occurred
        if lines_inserted >= 1:
            continue

        src_filename = row[1]['output_filename']
        class_name = row[1]['class_name']
        try:
            print(dataset_dir / src_filename)
            ast = AST.build_from_javalang(build_ast(dataset_dir / src_filename))
            function_to_analyze = row[1]['invocation_method_name']
            for class_decl in ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION):
                # class_ast = ast.get_subtree(class_decl)
                if class_decl.name != class_name:
                    continue
                elif class_decl.name == class_name:
                    for method_decl in class_decl.methods:
                        if method_decl.name != function_to_analyze:
                            continue
                        try:
                            # print(
                            #     f'Trying analyze {class_decl.name} {method_decl.name} '
                            #     f'{iteration_number}/{total_number}')
                            opport = _print_extraction_opportunities(
                                ast.get_subtree(method_decl)
                            )
                            if opport:
                                best_group = opport[0]
                                lines = [node.line for node in best_group._optimal_opportunity]
                                start_line_opportunity = min(lines)
                                end_line_opportunity = max(lines)
                                lines_intersected = set(
                                    range(end_line_of_invocation_occurred, end_line_of_invocation_occurred)) \
                                                    & set(lines)

                                if (start_line_of_invocation_occurred == start_line_opportunity) \
                                        and (end_line_of_invocation_occurred == end_line_opportunity):
                                    matched_cases += 1
                                matched_percent += float(len(lines_intersected)) / len(lines)
                            else:
                                no_opportunity_chosen += 0
                                # print(class_decl.name, method_decl.name)

                        except Exception as e:
                            import traceback
                            print(src_filename)
                            traceback.print_exc()
                            failed_cases_in_SEMI_algorithm += 1

                        break
                    break

        except Exception as e:
            failed_cases_in_validation_examples += 1

    print(f'Failed SEMI algorithm errors: {failed_cases_in_SEMI_algorithm}')
    print(f'Failed examples of synth dataset: {failed_cases_in_validation_examples}')
    print(f'matched_cases: {matched_cases}')
    print(f'No opportunity chosen: {no_opportunity_chosen} times')
    print(f'Total number of cases: {total_number}')
    print(f'Total number of matched lines: {matched_percent}')
    matched = (matched_cases + no_opportunity_chosen)
    total_number = total_number - failed_cases_in_SEMI_algorithm - failed_cases_in_validation_examples
    print(float(matched) / total_number)
