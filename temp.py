from collections import defaultdict, OrderedDict
from pathlib import Path

from veniq.baselines.semi.extract_semantic import extract_method_statements_semantic
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


def convert_matrix_to_csv_with_names(filename, matrix, rows, columns):
    import csv
    import operator

    with open(filename, 'w', newline='') as csvfile:
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
    global columns
    names_inverted = {}
    arr = []
    print(len(names_usage_dict.keys()), len(columns))
    for i, (member_name, code_lines) in enumerate(names_usage_dict.items()):
        names_inverted[i] = member_name
        unique_names = set()
        for line in code_lines:
            column_index = columns.get(line)
            unique_names.add(column_index + 1)

            # print(i + 1, column_index + 1, end=' ')
            # matrix[i][column_index] = 1
        q = ' '.join([str(i + 1)] + [str(x) for x in sorted(unique_names)])
        arr.append(q)
    # print('\n'.join(arr))
    # print('\n'.join(arr))
    return arr


def print_full_matrix_to_csv(filename, names_dict, columns):
    # global names_inverted, member_name, line
    matrix = [[0 for x in range(len(columns))] for y in range(len(names_dict.keys()))]
    names_inverted = {}
    for i, (member_name, code_lines) in enumerate(names_dict.items()):
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
    convert_matrix_to_csv_with_names(filename, matrix, names_inverted, invert_dict(columns))


def make_permutation(names_usage_dict, column_perm, row_perm, inverted_columns):
    names_src_oder = list(names_usage_dict.keys())
    new_names_order = OrderedDict()
    columns = OrderedDict()
    # for i, name in enumerate(names_src_oder):
    #     print(name, i, row_perm[i])
    # j = 1
    for i in row_perm:
        # print(i)
        try:
            name = names_src_oder[i]
            new_names_order[name] = []
            # j += 1
        except IndexError as e:
            print(i)
    # print(new_names_order)
    for i, new_column in enumerate(column_perm):
        for name, old_columns_list in names_usage_dict.items():
            new_columns_list = old_columns_list.copy()
            old_real_line = inverted_columns.get(i)[0]
            if old_real_line in new_columns_list:
                new_columns_list.remove(old_real_line)
                new_real_line = inverted_columns.get(new_column)[0]
                new_columns_list.append(new_real_line)
                columns[new_real_line] = i
                new_names_order[name] = new_columns_list
    # print(new_names_order)
    print_full_matrix_to_csv('reordered.csv', new_names_order, columns)



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

                    # print_full_matrix_to_csv('matrix.csv', names_usage_dict, columns)
                    print_short_matrix(names_usage_dict)
                    row_perm = [18, 23, 35, 21, 10, 9, 28, 8, 17, 13, 6, 2, 7, 19, 26, 25, 24, 1, 4, 16, 15, 5, 0,
                                36, 37, 14, 3, 27, 31, 12, 11, 20, 32, 33, 34, 30, 29, 22]
                    column_perm = [37, 4, 26, 19, 0, 20, 24, 14, 9, 17, 25, 13, 35, 5, 38, 34, 15, 6, 12, 3, 8, 23, 22,
                                   36, 27, 21, 1, 39, 10, 2, 11, 7, 28, 30, 31, 33, 29, 16, 32, 18]
                    clusters = [[0, 13], [13, 17], [18, 20], [21, 25], [26, 30], [31, 35], [36, 39]]
                    # make_permutation(names_usage_dict, column_perm, row_perm, invert_dict(columns))
                    with open(file, 'r', encoding='utf-8') as f:
                        str_lines = f.read().split('\n')
                        inv_columns = invert_dict(columns)
                        for i, cluster in enumerate(clusters):
                            print(f"Cluster {i}:")
                            permuted_lines = list(range(cluster[0], cluster[1] + 1))
                            for new_line in permuted_lines:
                                line_after_permutation = column_perm[new_line]
                                line_in_file = inv_columns[line_after_permutation][0]
                                # print(inv_columns[old_line], ' ')
                                # print(old_line, ' ')
                                print(str_lines[line_in_file - 1])
                            print()