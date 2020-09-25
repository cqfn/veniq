from collections import defaultdict, OrderedDict
from pathlib import Path

from veniq.extract_method_baseline.extract_semantic import extract_method_statements_semantic
from veniq.ast_framework import AST, ASTNodeType
from utils.ast_builder import build_ast

main_path = Path(r'D:\temp\wp_private\wp\experiments\extract_method\Validation_examples\6')


def add_unique_member_to_dict(lst, rows):
    global cur_rows_index
    for var in lst:
        key = rows.get(var)
        if not key:
            rows[var] = cur_rows_index
            cur_rows_index += 1


def add_unique_statement_to_dict(statement, dict_statements):
    global cur_columns_index
    key = dict_statements.get(statement.line)
    if not key:
        dict_statements[statement.line] = cur_columns_index
        cur_columns_index += 1


def convert_matrix_to_csv_with_names(matrix, rows, columns):
    import csv
    import operator

    with open('matrix.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(
            csvfile, delimiter=',',
            quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        sorted_columns = OrderedDict(sorted(columns.items()))
        spamwriter.writerow([''] + [str(x[0]) for x in sorted_columns.values()])

        for i, x in enumerate(matrix):
            name = rows.get(i)
            row = [name] + [str(j) for j in x]
            spamwriter.writerow(row)


def invert_dict(d):
    d_inv = defaultdict(list)
    for k, v in d.items():
        d_inv[v].append(k)
    return d_inv


def print_short_matrix(names_usage_dict):
    names_inverted = {}
    print(len(names_usage_dict.keys()), len(columns))
    for i, (member_name, code_lines) in enumerate(names_usage_dict.items()):
        names_inverted[i] = member_name
        unique_names = set()
        for line in code_lines:
            column_index = columns.get(line)
            unique_names.add(column_index + 1)
            unique_names.add(i + 1)
            # print(i + 1, column_index + 1, end=' ')
            # matrix[i][column_index] = 1
        print(' '.join(str(x) for x in sorted(unique_names)))


def print_full_matrix_to_csv():
    global names_inverted, member_name, line
    matrix = [[0 for x in range(len(columns))] for y in range(len(names_usage_dict.keys()))]
    names_inverted = {}
    for i, (member_name, code_lines) in enumerate(names_usage_dict.items()):
        names_inverted[i] = member_name
        unique_names = set()
        for line in code_lines:
            column_index = columns.get(line)
            unique_names.add(column_index + 1)
            unique_names.add(i + 1)
            # print(i + 1, column_index + 1, end=' ')
            matrix[i][column_index] = 1
        # print(' '.join(str(x) for x in sorted(unique_names)))
    # print_short_matrix(names_usage_dict)
    convert_matrix_to_csv_with_names(matrix, names_inverted, invert_dict(columns))


for file in main_path.glob('**/SAXParserImpl.java'):
    print(file)
    ast = AST.build_from_javalang(build_ast(str(file)))
    classes_ast = [
        ast.get_subtree(node)
        for node in ast.get_root().types
        if node.node_type == ASTNodeType.CLASS_DECLARATION
    ]
    for class_ast in classes_ast:
        class_declaration = class_ast.get_root()
        if class_declaration.name == 'SAXParserImpl':
            # for method in class_declaration.methods:
            for method in class_declaration.constructors:
                if len(method.parameters) == 3:
                    print(method.name)
                    m_dl = class_ast.get_subtree(method)
                    res = extract_method_statements_semantic(m_dl)
                    # print(res)
                    names_usage_dict = defaultdict(list)
                    columns = dict()
                    cur_rows_index = 0
                    cur_columns_index = 0
                    # prepare rows, extract unique keys
                    for x, y in res.items():
                        for j in y.used_variables:
                            names_usage_dict[j].append(x.line)
                        for j in y.used_objects:
                            names_usage_dict[j].append(x.line)
                        for j in y.used_methods:
                            names_usage_dict[j].append(x.line)
                        add_unique_statement_to_dict(x, columns)

                    # print_full_matrix_to_csv()
                    print_short_matrix(names_usage_dict)
