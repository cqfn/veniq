import pandas as pd

df = pd.read_csv('out.csv')
immutable_df = df.copy()


def remove_indices(df_to_filter: pd.DataFrame):
    rows = df[df.index.isin(df_to_filter.index)]
    df.drop(rows.index, inplace=True)


print(f'Total lines: {df.shape[0]}')
duplicateRowsDF = immutable_df[immutable_df.duplicated()]
print(f'Duplicated rows: {duplicateRowsDF.shape[0]}')
remove_indices(duplicateRowsDF)
ncss_target = immutable_df[immutable_df['ncss_target'] > 2]
remove_indices(ncss_target)
print(f'ncss_target > 2 {ncss_target.shape[0]}')

# REMOVE METHOD CHAINING SINCE IT IS not correct
# to inline them, we have different type objects,
# it's not a function of the original class
method_chain_before = immutable_df[immutable_df['METHOD_CHAIN_BEFORE'] == True]
remove_indices(method_chain_before)
method_chain_after = immutable_df[immutable_df['METHOD_CHAIN_AFTER'] == True]
remove_indices(method_chain_after)

method_with_arguments = immutable_df[immutable_df['METHOD_WITH_ARGUMENTS'] == True]
print(f'Samples where extracted method has parameters: '
      f'{method_with_arguments.shape[0]}. We prune such methods')
remove_indices(method_with_arguments)

crossed_var_names = immutable_df[immutable_df['CROSSED_VAR_NAMES'] == True]
remove_indices(crossed_var_names)
print(f'Samples where var names of extracted function is crossed with target method'
      f'{crossed_var_names.shape[0]}')

do_nothing = immutable_df[immutable_df['do_nothing'] == True]
remove_indices(do_nothing)
print(f'Samples where we rejected to inline by some reason'
      f'{do_nothing.shape[0]}')


not_simple_actual_parameter = immutable_df[immutable_df['NOT_SIMPLE_ACTUAL_PARAMETER'] == True]
remove_indices(not_simple_actual_parameter)
print(f'Samples where actual parameter in invocation is not simple. Sometimes it matches the cast typing'
      f'{not_simple_actual_parameter.shape[0]}')


# immutable_df['score_diff'] = immutable_df['invocation_method_end_line'].sub(immutable_df['invocation_method_start_line'], axis=0)
# negative_insertions = immutable_df[immutable_df['score_diff'] < 0]
# remove_indices(negative_insertions)
# print(f'Negative insertions: {negative_insertions.shape[0]}')
#
# print(f'Total cases: {df.shape[0]}')
# print(f'Target ncss 3: {df.shape[0]}')
