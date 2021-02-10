from enum import Enum
from typing import List, Dict, Any, Tuple

from veniq.ast_framework import ASTNode, AST, ASTNodeType
from veniq.dataset_collection.types_identifier import InlineTypesAlgorithms


class InvocationType(Enum):
    # OK = 0
    METHOD_CHAIN_BEFORE = 1
    NOT_SIMPLE_ACTUAL_PARAMETER = 2
    METHOD_CHAIN_AFTER = 3
    INSIDE_IF = 4
    INSIDE_WHILE = 5
    # INSIDE_FOR = 6
    INSIDE_FOREACH = 7
    INSIDE_BINARY_OPERATION = 8
    INSIDE_TERNARY = 9
    INSIDE_CLASS_CREATOR = 10
    CAST_OF_RETURN_TYPE = 11
    INSIDE_ARRAY_CREATOR = 12
    SINGLE_STATEMENT_IN_IF = 13
    INSIDE_LAMBDA = 14
    # ALREADY_ASSIGNED_VALUE_IN_INVOCATION = 15
    SEVERAL_RETURNS = 16
    IS_NOT_AT_THE_SAME_LINE_AS_PROHIBITED_STATS = 17
    IS_NOT_PARENT_MEMBER_REF = 18
    # EXTRACTED_NCSS_SMALL = 19
    CROSSED_VAR_NAMES_INSIDE_FUNCTION = 20
    CAST_IN_ACTUAL_PARAMS = 21
    ABSTRACT_METHOD = 22
    NOT_FUNC_PARAMS_EQUAL = 23
    THROW_IN_EXTRACTED = 24
    RETURN_IN_ANOTHER_SCOPE = 25

    # METHOD_WITH_ARGUMENTS_VAR_CROSSED = 999

    @classmethod
    def list_types(cls):
        types = [member.name for role, member in cls.__members__.items()]
        return types


def _get_last_line(text: str, start_line: int) -> int:
    """
    This function is aimed to find the last body line of
    considered method. It work by counting the difference
    in number of openning brackets '{' and closing brackets
    '}'. It's start with the method declaration line and going
    to the line where the difference is equal to 0. Which means
    that we found closind bracket of method declaration.
    """
    file_lines = text.split('\n')
    # to start counting opening brackets
    difference_cases = 0

    processed_declaration_line = file_lines[start_line - 1].split('//')[0]
    difference_cases += processed_declaration_line.count('{')
    difference_cases -= processed_declaration_line.count('}')
    for i, line in enumerate(file_lines[start_line:], start_line):
        if difference_cases:
            line_without_comments = line.split('//')[0]
            difference_cases += line_without_comments.count('{')
            difference_cases -= line_without_comments.count('}')
        else:
            # process comments to the last line of method
            if line.strip() == '*/':
                return i + 2
            else:
                return i

    return -1


def get_line_with_first_open_bracket(
        text: str,
        method_decl_start_line: int
) -> int:
    file_lines = text.split('\n')
    for i, line in enumerate(file_lines[method_decl_start_line - 2:], method_decl_start_line - 2):
        if '{' in line:
            return i + 1
    return method_decl_start_line + 1


def method_body_lines(method_node: ASTNode, text: str) -> Tuple[int, int]:
    """
    Get start and end of method's body
    """
    if len(method_node.body):
        m_decl_start_line = method_node.line + 1
        start_line = get_line_with_first_open_bracket(text, m_decl_start_line)
        end_line = _get_last_line(text, start_line)
    else:
        start_line = end_line = -1
    return start_line, end_line


def get_stats_for_pruned_cases(
        is_actual_parameter_simple, is_not_array_creator, has_not_throw,
        is_not_at_the_same_line_as_prohibited_stats, is_not_binary_operation,
        is_not_cast_of_return_type, is_not_chain_after, is_not_chain_before,
        is_not_class_creator, is_not_enhanced_for_control,
        # is_not_inside_for,
        are_var_crossed_inside_extracted,
        is_not_inside_if, is_not_inside_while, is_not_lambda,
        is_not_method_inv_single_statement_in_if, is_not_parent_member_ref,
        is_not_several_returns, is_not_ternary, is_not_actual_param_cast,
        is_not_is_extract_method_abstract, are_functional_arguments_eq, method_invoked) -> List[str]:
    invocation_types_to_ignore: List[str] = []

    if not is_not_is_extract_method_abstract:
        invocation_types_to_ignore.append(InvocationType.ABSTRACT_METHOD.name)
    if not is_not_chain_before:
        invocation_types_to_ignore.append(InvocationType.METHOD_CHAIN_BEFORE.name)
    if not is_actual_parameter_simple:
        invocation_types_to_ignore.append(InvocationType.NOT_SIMPLE_ACTUAL_PARAMETER.name)
    if not is_not_actual_param_cast:
        invocation_types_to_ignore.append(InvocationType.CAST_IN_ACTUAL_PARAMS.name)
    if not is_not_chain_after:
        invocation_types_to_ignore.append(InvocationType.METHOD_CHAIN_AFTER.name)
    if not is_not_inside_if:
        invocation_types_to_ignore.append(InvocationType.INSIDE_IF.name)
    if not is_not_inside_while:
        invocation_types_to_ignore.append(InvocationType.INSIDE_WHILE.name)
    if not is_not_binary_operation:
        invocation_types_to_ignore.append(InvocationType.INSIDE_BINARY_OPERATION.name)
    if not is_not_ternary:
        invocation_types_to_ignore.append(InvocationType.INSIDE_TERNARY.name)
    if not is_not_class_creator:
        invocation_types_to_ignore.append(InvocationType.INSIDE_CLASS_CREATOR.name)
    if not is_not_cast_of_return_type:
        invocation_types_to_ignore.append(InvocationType.CAST_OF_RETURN_TYPE.name)
    if not is_not_array_creator:
        invocation_types_to_ignore.append(InvocationType.INSIDE_ARRAY_CREATOR.name)
    if not is_not_parent_member_ref:
        invocation_types_to_ignore.append(InvocationType.IS_NOT_PARENT_MEMBER_REF.name)
    # if not is_not_inside_for:
    #     invocation_types_to_ignore.append(InvocationType.INSIDE_FOR.name)
    if not is_not_enhanced_for_control:
        invocation_types_to_ignore.append(InvocationType.INSIDE_FOREACH.name)
    if not is_not_lambda:
        invocation_types_to_ignore.append(InvocationType.INSIDE_LAMBDA.name)
    if not is_not_method_inv_single_statement_in_if:
        invocation_types_to_ignore.append(InvocationType.SINGLE_STATEMENT_IN_IF.name)
    # if not is_not_assign_value_with_return_type:
    #     invocation_types_to_ignore.append(InvocationType.ALREADY_ASSIGNED_VALUE_IN_INVOCATION.name)
    if not is_not_several_returns:
        invocation_types_to_ignore.append(InvocationType.SEVERAL_RETURNS.name)
    if not is_not_at_the_same_line_as_prohibited_stats:
        invocation_types_to_ignore.append(InvocationType.IS_NOT_AT_THE_SAME_LINE_AS_PROHIBITED_STATS.name)

    if not are_functional_arguments_eq:
        invocation_types_to_ignore.append(InvocationType.NOT_FUNC_PARAMS_EQUAL.name)
    if are_var_crossed_inside_extracted:
        invocation_types_to_ignore.append(InvocationType.CROSSED_VAR_NAMES_INSIDE_FUNCTION.name)
    if not has_not_throw:
        invocation_types_to_ignore.append(InvocationType.THROW_IN_EXTRACTED.name)

    return invocation_types_to_ignore


def get_variables_decl_in_node(
        method_decl: AST) -> List[str]:
    names = []
    for x in method_decl.get_proxy_nodes(ASTNodeType.VARIABLE_DECLARATOR):
        if hasattr(x, 'name'):
            names.append(x.name)
        elif hasattr(x, 'names'):
            names.extend(x.names)

    for x in method_decl.get_proxy_nodes(ASTNodeType.VARIABLE_DECLARATION):
        if hasattr(x, 'name'):
            names.append(x.name)
        elif hasattr(x, 'names'):
            names.extend(x.names)

    for x in method_decl.get_proxy_nodes(ASTNodeType.TRY_RESOURCE):
        names.append(x.name)

    return names


def are_not_var_crossed(
        invocaton_node: ASTNode,
        method_declaration: ASTNode,
        target: ASTNode,
        ast: AST) -> bool:
    # m_decl_names = set([x.name for x in method_declaration.parameters])
    m_inv_names = set([x.member for x in invocaton_node.arguments])
    var_names_in_extracted = set(get_variables_decl_in_node(ast.get_subtree(method_declaration)))
    var_names_in_target = set(get_variables_decl_in_node(ast.get_subtree(target)))
    var_names_in_target = var_names_in_target.difference(m_inv_names)
    var_names_in_extracted = var_names_in_extracted.difference(m_inv_names)

    if not var_names_in_target or not var_names_in_extracted:
        return True

    intersected_names = var_names_in_target.difference(var_names_in_extracted)
    if not intersected_names:
        return False

    return True


def check_nesting_statements(
        method_invoked: ASTNode
) -> bool:
    """
    Check that the considered method invocation is not
    at the same line as prohibited statements.
    """
    prohibited_statements = [
        ASTNodeType.IF_STATEMENT,
        ASTNodeType.WHILE_STATEMENT,
        ASTNodeType.FOR_STATEMENT,
        ASTNodeType.SYNCHRONIZED_STATEMENT,
        ASTNodeType.CATCH_CLAUSE,
        ASTNodeType.SUPER_CONSTRUCTOR_INVOCATION,
        ASTNodeType.TRY_STATEMENT
    ]
    if method_invoked.parent is not None:
        if (method_invoked.parent.node_type in prohibited_statements) \
                and (method_invoked.parent.line == method_invoked.line):
            return False

        if method_invoked.parent.parent is not None:
            if (method_invoked.parent.parent.node_type in prohibited_statements) \
                    and (method_invoked.parent.parent.line == method_invoked.line):
                return False

            if method_invoked.parent.parent.parent is not None:
                if (method_invoked.parent.parent.parent.node_type in prohibited_statements) \
                        and (method_invoked.parent.parent.parent.line == method_invoked.line):
                    return False

    return True


def are_functional_arguments_equal(
        invocaton_node: ASTNode,
        method_declaration: ASTNode) -> bool:
    """
    Check if names of params of invocation are matched with
    params of method declaration:
    Matched:
    func(a, b);
    public void func(int a, int b)
    Not matched
    func(a, e);
    public void func(int a, int b)
    :param invocaton_node: invocation of function
    :param method_declaration: method declaration of invoked function
    :return:
    """
    m_decl_names = set([x.name for x in method_declaration.parameters])
    m_inv_names = set([x.member for x in invocaton_node.arguments])
    intersection = m_inv_names.difference(m_decl_names)
    if not intersection:
        return True
    else:
        return False


def determine_algorithm_insertion_type(
        extracted_method_decl: ASTNode) -> InlineTypesAlgorithms:
    has_attr_return_type = hasattr(extracted_method_decl, 'return_type')
    if has_attr_return_type:
        if not extracted_method_decl.return_type:
            return InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS
        else:
            return InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS
    #  Else if we have constructor, it doesn't have return type
    else:
        return InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS


def annotate(dct: Dict[str, Any]):
    method_invoked = dct['method_invoked']
    target_node = dct['target_node']
    extracted_m_decl = dct['extracted_m_decl']
    ast = dct['ast']
    text = dct['text']
    if method_invoked.parent.node_type == ASTNodeType.THIS:
        parent = method_invoked.parent.parent
        class_names = [x for x in method_invoked.parent.children if hasattr(x, 'string')]
        member_references = [x for x in method_invoked.parent.children if hasattr(x, 'member')]
        lst = [x for x in member_references if x.member != method_invoked.member] + class_names
        no_children = not lst
    else:
        parent = method_invoked.parent
        no_children = True

    is_not_is_extract_method_abstract = True
    if 'abstract' in extracted_m_decl.modifiers:
        is_not_is_extract_method_abstract = False

    maybe_if = parent.parent
    is_not_method_inv_single_statement_in_if = True
    if maybe_if.node_type == ASTNodeType.IF_STATEMENT:
        if hasattr(maybe_if.then_statement, 'expression'):
            if maybe_if.then_statement.expression.node_type == ASTNodeType.METHOD_INVOCATION:
                is_not_method_inv_single_statement_in_if = False

    ast_subtree_method_decl = ast.get_subtree(extracted_m_decl)
    # is_not_assign_value_with_return_type = True
    is_not_several_returns = True
    if hasattr(extracted_m_decl, 'return_type'):
        if extracted_m_decl.return_type:
            return_stats = len([
                x for x in extracted_m_decl.body
                if x.node_type == ASTNodeType.RETURN_STATEMENT]
            )

            # If we do not have return in function body,
            # it means that we will have deep inside AST tree, so remember it
            stats = [x for x in ast_subtree_method_decl.get_proxy_nodes(ASTNodeType.RETURN_STATEMENT)]
            total_return_statements = len(stats) - return_stats
            if total_return_statements > 0:
                is_not_several_returns = False

    has_not_throw = len([
        x for x in extracted_m_decl.body
        if x.node_type == ASTNodeType.THROW_STATEMENT]) < 1
    is_not_parent_member_ref = not (method_invoked.parent.node_type == ASTNodeType.MEMBER_REFERENCE)
    is_not_chain_before = not (parent.node_type == ASTNodeType.METHOD_INVOCATION) and no_children
    chains_after = [x for x in method_invoked.children if x.node_type == ASTNodeType.METHOD_INVOCATION]
    is_not_chain_after = not chains_after
    is_not_inside_if = not (parent.node_type == ASTNodeType.IF_STATEMENT)
    is_not_inside_while = not (parent.node_type == ASTNodeType.WHILE_STATEMENT)
    # is_not_inside_for = not (parent.node_type == ASTNodeType.FOR_STATEMENT)
    is_not_enhanced_for_control = not (parent.node_type == ASTNodeType.ENHANCED_FOR_CONTROL)
    # ignore case else if (getServiceInterface() != null) {
    is_not_binary_operation = not (parent.node_type == ASTNodeType.BINARY_OPERATION)
    is_not_ternary = not (parent.node_type == ASTNodeType.TERNARY_EXPRESSION)
    # if a parameter is any expression, we ignore it,
    # since it is difficult to extract with AST
    is_actual_parameter_simple = all([hasattr(x, 'member') for x in method_invoked.arguments])
    is_not_actual_param_cast = True
    if not is_actual_parameter_simple:
        found_casts = [x for x in method_invoked.arguments if x.node_type == ASTNodeType.CAST]
        if len(found_casts) > 0:
            is_not_actual_param_cast = False

    is_not_class_creator = not (parent.node_type == ASTNodeType.CLASS_CREATOR)
    is_not_cast_of_return_type = not (parent.node_type == ASTNodeType.CAST)
    is_not_array_creator = not (parent.node_type == ASTNodeType.ARRAY_CREATOR)
    is_not_lambda = not (parent.node_type == ASTNodeType.LAMBDA_EXPRESSION)
    is_not_at_the_same_line_as_prohibited_stats = check_nesting_statements(method_invoked)

    are_functional_arguments_eq = False
    are_var_crossed_inside_extracted = True
    if is_actual_parameter_simple:
        are_functional_arguments_eq = are_functional_arguments_equal(method_invoked, extracted_m_decl)
        if are_functional_arguments_eq:
            if are_not_var_crossed(method_invoked, extracted_m_decl, target_node, ast):
                are_var_crossed_inside_extracted = False

    ignored_cases = get_stats_for_pruned_cases(
        is_actual_parameter_simple,
        is_not_array_creator,
        has_not_throw,
        is_not_at_the_same_line_as_prohibited_stats,
        is_not_binary_operation,
        is_not_cast_of_return_type,
        is_not_chain_after,
        is_not_chain_before,
        is_not_class_creator,
        is_not_enhanced_for_control,
        # is_not_inside_for,
        are_var_crossed_inside_extracted,
        is_not_inside_if,
        is_not_inside_while,
        is_not_lambda,
        is_not_method_inv_single_statement_in_if,
        is_not_parent_member_ref,
        is_not_several_returns,
        is_not_ternary,
        is_not_actual_param_cast,
        is_not_is_extract_method_abstract,
        are_functional_arguments_eq,
        method_invoked
    )

    updated_dict = {
        'extract_method': method_invoked.member,
        'target_method': target_node.name
    }
    # default init
    for case_name in InvocationType.list_types():
        updated_dict[case_name] = False

    body_start_line, body_end_line = method_body_lines(extracted_m_decl, text)
    updated_dict['extract_method_start_line'] = body_start_line
    updated_dict['extract_method_end_line'] = body_end_line

    if body_end_line != body_end_line:
        updated_dict['ONE_LINE_FUNCTION'] = False
    else:
        ignored_cases.append('ONE_LINE_FUNCTION')
        updated_dict['ONE_LINE_FUNCTION'] = True

    if not ignored_cases:
        updated_dict['NO_IGNORED_CASES'] = True
    else:
        updated_dict['NO_IGNORED_CASES'] = False

    algorithm_type = determine_algorithm_insertion_type(extracted_m_decl)
    updated_dict['algorithm_type'] = algorithm_type

    yield {**updated_dict, **dct}
