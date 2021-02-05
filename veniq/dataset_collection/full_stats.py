import pandas as pd


def remove_indices(df_to_filter: pd.DataFrame, src_df):
    rows = src_df[src_df.index.isin(df_to_filter.index)]
    print(f'dropped {rows.shape[0]}')
    src_df.drop(rows.index, inplace=True)
    print(f'remained {src_df.shape[0]}')


def make_filtration():
    # df = pd.read_csv(r'D:\git\veniq\veniq\dataset_collection\new_dataset\full_dataset\out.csv')

    df = pd.read_csv(r'D:\temp\dataset_colelction_refactoring\1_21\out.csv')
    immutable_df = df.copy()
    print(f'Total lines: {df.shape[0]}')
    duplicateRowsDF = immutable_df[immutable_df.duplicated()]
    print(f'Duplicated rows: {duplicateRowsDF.shape[0]}')
    remove_indices(duplicateRowsDF, df)

    # method_with_arguments = immutable_df[immutable_df['METHOD_WITH_ARGUMENTS'] == True]
    # percent_without = (method_with_arguments.shape[0] / float(immutable_df.shape[0])) * 100
    # print(f'Samples where extracted method has parameters: '
    #       f'{method_with_arguments.shape[0]}; {percent_without:.2f}')

    # without_arguments_df = immutable_df[immutable_df['METHOD_WITH_ARGUMENTS'] == False]
    # percent_with = (without_arguments_df.shape[0] / float(immutable_df.shape[0])) * 100
    # print(f'Samples where extracted method doesn\'t parameters: '
    #       f'{without_arguments_df.shape[0]}; {percent_with:.2f}')
    #
    # print('Analyzing methods without arguments')
    # must_have_filtration(without_arguments_df.__deepcopy__(), without_arguments_df.__deepcopy__())
    # print('Analyzing methods with arguments')
    # must_have_filtration(method_with_arguments.__deepcopy__(), df.__deepcopy__())

    must_have_filtration(immutable_df.__deepcopy__(), df.__deepcopy__())


def must_have_filtration(immutable_df, df):

    print('Must-have filters')
    filter_with_indices_exclusion(df, immutable_df, immutable_df['ncss_extracted'] < 3, 'ncss_extracted < 3')
    # exclude abstract extract methods
    filter_with_indices_exclusion(df, immutable_df, immutable_df['ABSTRACT_METHOD'] == True, 'abstract methods')
    # REMOVE METHOD CHAINING SINCE IT IS not correct
    # to inline them, we have different type objects,
    # it's not a function of the original class

    filter_with_indices_exclusion(
        df, immutable_df,
        immutable_df['METHOD_CHAIN_BEFORE'] == True, 'method_chain_before')

    filter_with_indices_exclusion(
        df, immutable_df,
        immutable_df['METHOD_CHAIN_AFTER'] == True, 'method_chain_after')

    count_filters_for_df(df.__deepcopy__(), df.__deepcopy__())


def filter_with_indices_exclusion(df, immutable_df, lambda_f, str_to_print):
    filtered_df = immutable_df[lambda_f]
    remove_indices(filtered_df, df)
    percent = (filtered_df.shape[0] / float(immutable_df.shape[0])) * 100
    print(f'{str_to_print} {filtered_df.shape[0]}; {percent:.2f}%')


def count_filters_for_df(immutable_df, df_changed):

    print('Filters with invocation types classification')
    is_valid_ast = immutable_df[immutable_df['is_valid_ast'] == True]

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['CROSSED_VAR_NAMES_INSIDE_FUNCTION'] == True,
        'Samples where var names of extracted function is crossed with target method excepting function arguments'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['NOT_FUNC_PARAMS_EQUAL'] == True,
        'Samples where function parameters of invoked function are not matched with actual arguments'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['do_nothing'] == True,
        'Samples where we rejected to inline by some reason'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['NOT_SIMPLE_ACTUAL_PARAMETER'] == True,
        'Samples where actual parameter in invocation is not simple'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_IF'] == True,
        'Samples where invocation was inside if condition'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_WHILE'] == True,
        'Samples where invocation was inside while condition'
    )

    # filter_with_indices_exclusion(
    #     df_changed,
    #     immutable_df,
    #     immutable_df['INSIDE_FOR'] == True,
    #     'Samples where invocation was inside for condition'
    # )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_FOREACH'] == True,
        'Samples where invocation was inside foreach condition'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_BINARY_OPERATION'] == True,
        'Samples where invocation was inside binary operation'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_TERNARY'] == True,
        'Samples where invocation was inside ternary operation'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_CLASS_CREATOR'] == True,
        'Samples where invocation was inside class creator'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['CAST_OF_RETURN_TYPE'] == True,
        'Samples where return parameter was casted'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['CAST_IN_ACTUAL_PARAMS'] == True,
        'Samples where actual parameter in invocation was casted'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_ARRAY_CREATOR'] == True,
        'Samples where invocation was in array creator'
    )
    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['SINGLE_STATEMENT_IN_IF'] == True,
        'Samples where invocation was in if block with 1 statement'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['INSIDE_LAMBDA'] == True,
        'Samples where invocation was in lambda'
    )

    # filter_with_indices_exclusion(
    #     df_changed,
    #     immutable_df,
    #     immutable_df['ALREADY_ASSIGNED_VALUE_IN_INVOCATION'] == True,
    #     'Samples where already assigned value was in invocation'
    # )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['SEVERAL_RETURNS'] == True,
        'Samples where there are several returns in extracted method'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['THROW_IN_EXTRACTED'] == True,
        'Samples where we have throw statement in extracted method'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['IS_NOT_AT_THE_SAME_LINE_AS_PROHIBITED_STATS'] == True,
        'Samples where invocation was inside try-statement, synchronized statement,'
        'catch clause, super constructor invocation'
    )

    filter_with_indices_exclusion(
        df_changed,
        immutable_df,
        immutable_df['IS_NOT_PARENT_MEMBER_REF'] == True,
        'Samples where is_not_parent_member_ref'
    )

    print(f'Remained cases: {df_changed.shape[0]}')
    df_changed.to_csv('remained.csv')
    print(f'is_valid_ast cases: {is_valid_ast.shape[0]}')
    is_valid_ast.to_csv('is_valid_ast.csv')
    print(f'cases where filters didn\'t work: {is_valid_ast.shape[0]}')


if __name__ == '__main__':
    make_filtration()
