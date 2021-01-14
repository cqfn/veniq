import pandas as pd

df = pd.read_csv(r'd:\git\veniq\veniq\dataset_collection\new_dataset\full_dataset\out.csv')
immutable_df = df.copy()


def remove_indices(df_to_filter: pd.DataFrame, src_df):
    rows = src_df[src_df.index.isin(df_to_filter.index)]
    src_df.drop(rows.index, inplace=True)


print(f'Total lines: {df.shape[0]}')
duplicateRowsDF = immutable_df[immutable_df.duplicated()]
print(f'Duplicated rows: {duplicateRowsDF.shape[0]}')
remove_indices(duplicateRowsDF, df)
ncss_target = immutable_df[immutable_df['ncss_target'] > 2]
remove_indices(ncss_target, df)
print(f'ncss_target > 2 {ncss_target.shape[0]}')

# exclude abstract extract methods
abstract_method = immutable_df[immutable_df['ABSTRACT_METHOD'] == True]
remove_indices(abstract_method, df)

# REMOVE METHOD CHAINING SINCE IT IS not correct
# to inline them, we have different type objects,
# it's not a function of the original class
method_chain_before = immutable_df[immutable_df['METHOD_CHAIN_BEFORE'] == True]
remove_indices(method_chain_before, df)
method_chain_after = immutable_df[immutable_df['METHOD_CHAIN_AFTER'] == True]
remove_indices(method_chain_after, df)

method_with_arguments = immutable_df[immutable_df['METHOD_WITH_ARGUMENTS'] == True]
print(f'Samples where extracted method has parameters: '
      f'{method_with_arguments.shape[0]}. We prune such methods')
with_arguments_df = df[df['METHOD_WITH_ARGUMENTS'] == True]
remove_indices(method_with_arguments, df)


def count_filters_for_df(immutable_df, df_changed):
    crossed_var_names = immutable_df[immutable_df['CROSSED_VAR_NAMES'] == True]
    remove_indices(crossed_var_names, df_changed)
    print(f'Samples where var names of extracted function is crossed with target method'
          f'{crossed_var_names.shape[0]}')

    do_nothing = immutable_df[immutable_df['do_nothing'] == True]
    remove_indices(do_nothing, df_changed)
    print(f'Samples where we rejected to inline by some reason'
          f'{do_nothing.shape[0]}')

    not_simple_actual_parameter = immutable_df[immutable_df['NOT_SIMPLE_ACTUAL_PARAMETER'] == True]
    remove_indices(not_simple_actual_parameter, df_changed)
    print(f'Samples where actual parameter in invocation is not simple'
          f'{not_simple_actual_parameter.shape[0]}')

    inside_if = immutable_df[immutable_df['INSIDE_IF'] == True]
    remove_indices(inside_if, df_changed)
    print(f'Samples where invocation was inside if condition'
          f'{inside_if.shape[0]}')

    inside_while = immutable_df[immutable_df['INSIDE_WHILE'] == True]
    remove_indices(inside_while, df_changed)
    print(f'Samples where invocation was inside while condition'
          f'{inside_while.shape[0]}')

    not_simple_actual_parameter = immutable_df[immutable_df['INSIDE_FOR'] == True]
    remove_indices(not_simple_actual_parameter, df_changed)
    print(f'Samples where invocation was inside for condition'
          f'{not_simple_actual_parameter.shape[0]}')

    inside_foreach = immutable_df[immutable_df['INSIDE_FOREACH'] == True]
    remove_indices(inside_foreach, df_changed)
    print(f'Samples where invocation was inside foreach condition'
          f'{inside_foreach.shape[0]}')

    inside_binary_operation = immutable_df[immutable_df['INSIDE_BINARY_OPERATION'] == True]
    remove_indices(inside_binary_operation, df_changed)
    print(f'Samples where invocation was inside binary operation'
          f'{inside_binary_operation.shape[0]}')

    inside_ternary = immutable_df[immutable_df['INSIDE_TERNARY'] == True]
    remove_indices(inside_ternary, df_changed)
    print(f'Samples where invocation was inside ternary operation'
          f'{inside_ternary.shape[0]}')

    inside_class_creator = immutable_df[immutable_df['INSIDE_CLASS_CREATOR'] == True]
    remove_indices(inside_class_creator, df_changed)
    print(f'Samples where invocation was inside class creator'
          f'{inside_class_creator.shape[0]}')

    cast_of_return_type = immutable_df[immutable_df['CAST_OF_RETURN_TYPE'] == True]
    remove_indices(cast_of_return_type, df_changed)
    print(f'Samples where return parameter was casted'
          f'{cast_of_return_type.shape[0]}')

    cast_in_actual_params = immutable_df[immutable_df['CAST_IN_ACTUAL_PARAMS'] == True]
    remove_indices(cast_in_actual_params, df_changed)
    print(f'Samples where actual parameter in invocation was casted'
          f'{cast_in_actual_params.shape[0]}')

    inside_array_creator = immutable_df[immutable_df['INSIDE_ARRAY_CREATOR'] == True]
    remove_indices(inside_array_creator, df_changed)
    print(f'Samples where invocation was in array creator'
          f'{inside_array_creator.shape[0]}')

    single_statement_in_if = immutable_df[immutable_df['SINGLE_STATEMENT_IN_IF'] == True]
    remove_indices(single_statement_in_if, df_changed)
    print(f'Samples where invocation was in if block with 1 statement'
          f'{single_statement_in_if.shape[0]}')

    inside_lambda = immutable_df[immutable_df['INSIDE_LAMBDA'] == True]
    remove_indices(inside_lambda, df_changed)
    print(f'Samples where invocation was in lambda'
          f'{inside_lambda.shape[0]}')

    already_assigned_value_in_invocation = immutable_df[immutable_df['ALREADY_ASSIGNED_VALUE_IN_INVOCATION'] == True]
    remove_indices(already_assigned_value_in_invocation, df_changed)
    print(f'Samples where already assigned value was in invocation'
          f'{already_assigned_value_in_invocation.shape[0]}')

    several_returns = immutable_df[immutable_df['SEVERAL_RETURNS'] == True]
    remove_indices(several_returns, df_changed)
    print(f'Samples where there are several returns in extracted method'
          f'{several_returns.shape[0]}')

    is_not_at_the_same_line_as_prohibited_stats = immutable_df[immutable_df['IS_NOT_AT_THE_SAME_LINE_AS_PROHIBITED_STATS'] == True]
    remove_indices(is_not_at_the_same_line_as_prohibited_stats, df_changed)
    print(f'Samples where invocation was inside try-statement, synchronized statement,'
        'catch clause, super constructor invocation'
          f'{is_not_at_the_same_line_as_prohibited_stats.shape[0]}')

    is_not_parent_member_ref = immutable_df[immutable_df['IS_NOT_PARENT_MEMBER_REF'] == True]
    remove_indices(is_not_parent_member_ref, df_changed)
    print(f'Samples where is_not_parent_member_ref:'
          f'{is_not_parent_member_ref.shape[0]}')


count_filters_for_df(immutable_df, df)
count_filters_for_df(immutable_df, with_arguments_df)

# immutable_df['score_diff'] = immutable_df['invocation_method_end_line'].sub(immutable_df['invocation_method_start_line'], axis=0)
# negative_insertions = immutable_df[immutable_df['score_diff'] < 0]
# remove_indices(negative_insertions)
# print(f'Negative insertions: {negative_insertions.shape[0]}')
#
# print(f'Total cases: {df.shape[0]}')
# print(f'Target ncss 3: {df.shape[0]}')
