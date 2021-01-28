from typing import List, Tuple, Union
from tempfile import NamedTemporaryFile
from functools import reduce
from operator import itemgetter
import os

from javalang.parser import JavaSyntaxError

from veniq.utils.ast_builder import build_ast
from veniq.ast_framework import AST, ASTNodeType
from veniq.baselines.semi.rank_extraction_opportunities import \
    rank_extraction_opportunities, ExtractionOpportunityGroup
from veniq.baselines.semi.create_extraction_opportunities import \
    create_extraction_opportunities
from veniq.baselines.semi.extract_semantic import \
    extract_method_statements_semantic
from veniq.baselines.semi.filter_extraction_opportunities import \
    filter_extraction_opportunities
from veniq.baselines.semi._common_types import ExtractionOpportunity


EMO = Tuple[int, int]


class WrongMethodFormatException(Exception):
    pass


def _add_class_decl_wrap(method_decl: List[str]) -> List[str]:
    class_decl = ['class FakeClass {'] + method_decl + ['}']
    return class_decl


def _get_method_subtree(class_decl: List[str]) -> AST:
    with NamedTemporaryFile(delete=False) as f:
        _name = f.name
        f.write('\n'.join(class_decl).encode())
    try:
        javalang_ast = build_ast(_name)
        ast = AST.build_from_javalang(javalang_ast)
        os.unlink(_name)
    except JavaSyntaxError as e:
        os.unlink(_name)
        raise e

    class_node = list(ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION))[0]
    objects_to_consider = list(class_node.methods) + \
        list(class_node.constructors)
    method_node = objects_to_consider[0]
    ast_subtree = ast.get_subtree(method_node)
    return ast_subtree


def _find_EMO_groups(method_subtree: AST) -> List[ExtractionOpportunityGroup]:
    statements_semantic = extract_method_statements_semantic(method_subtree)
    extraction_opportunities = create_extraction_opportunities(
        statements_semantic)
    filtered_extraction_opportunities = filter_extraction_opportunities(
        extraction_opportunities, statements_semantic, method_subtree)
    extraction_opportunities_groups = rank_extraction_opportunities(
        statements_semantic, filtered_extraction_opportunities
    )

    return extraction_opportunities_groups


def _convert_ExtractionOpportunity_to_EMO(
        extr_opport: ExtractionOpportunity, class_decl: List[str]) -> EMO:
    ''' Converts extraction opportunity of type ExtractionOpportunity from
    veniq.baselines.semi._common_types to type EMO defined here.
    '''
    lines = [node.line for node in extr_opport]
    # subtract 1 because we count from 0
    start_line_opportunity = min(lines) - 1
    end_line_opportunity = max(lines) - 1
    extraction = class_decl[start_line_opportunity:]
    extraction_lines_number = end_line_opportunity - start_line_opportunity + 1

    # additional procedure to find closing brackets
    bracket_balance = 0
    for i, x in enumerate(extraction):
        open_brackets = x.count('{')
        bracket_balance += open_brackets
        closing_brackets = x.count('}')
        bracket_balance -= closing_brackets
        if i >= extraction_lines_number - 1:
            if bracket_balance <= 0:
                break

    return (start_line_opportunity, start_line_opportunity + i)


def check_format_validity(method_decl: List[str]) -> None:
    """
    Checks that the input method declaration is a syntactically
    correct Java method declaration.
    Raises exception otherwise.
    """
    # TODO
    pass


def recommend_for_method(method_decl: List[str]) -> Union[List[EMO], str]:
    '''
    Takes method declaration in form of list of lines,
    outputs list of EMOs in the order of decreasing recommendation.
    EMO is a (start_line_extraction, end_line_extraction)
    (the range is inclusive).

    TODO: use error codes in the future insteach of string
    error messages
    '''
    try:
        check_format_validity(method_decl)
    except WrongMethodFormatException:
        return "Wrong format"

    class_decl_fake = _add_class_decl_wrap(method_decl)
    try:
        method_subtree = _get_method_subtree(class_decl_fake)
    except JavaSyntaxError:
        return "Javalang can't parse"
    emo_groups = _find_EMO_groups(method_subtree)
    if emo_groups is None or emo_groups == []:
        return []
    all_opportunities = \
        reduce(lambda x, y: x + list(y.opportunities), emo_groups, [])

    all_opportunities_ranked = sorted(all_opportunities, key=itemgetter(1),
                                      reverse=True)
    all_opportunities_ranked = [_convert_ExtractionOpportunity_to_EMO(
        x[0], class_decl_fake) for x in all_opportunities_ranked]

    # subtract 1 because we added fake class declaration line
    all_opportunities_ranked = [(x[0] - 1, x[1] - 1) for x
                                in all_opportunities_ranked]
    return all_opportunities_ranked
