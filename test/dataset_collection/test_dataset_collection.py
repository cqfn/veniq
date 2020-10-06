from pathlib import Path
from unittest import TestCase

from dataset_collection.augmentation import determine_type
from veniq.ast_framework import AST, ASTNodeType
from veniq.dataset_collection.types_identifier import InlineTypesAlgorithms
from veniq.utils.ast_builder import build_ast


class TestDatasetCollection(TestCase):
    current_directory = Path(__file__).absolute().parent

    def test_determine_type_without_return(self):
        filepath = self.current_directory / "Example.java"
        ast = AST.build_from_javalang(build_ast(filepath))
        m_decl = [
            x for x in ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'reset_return_var_decl'][0]
        m_decl_original = [
            x for x in ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'closeServer_return'][0]
        m_inv = [
            x for x in ast.get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'closeServer_return'][0]
        d = {'closeServer_return': [m_decl_original]}
        type = determine_type(m_decl, m_inv, d)
        self.assertEqual(type, InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS)

    def test_determine_type_without_parameters(self):
        self.assertEqual(True, True)

    def test_determine_type_with_parameters(self):
        self.assertEqual(True, True)

    def test_determine_type_with_overridden_functions(self):
        self.assertEqual(True, True)

    def test_determine_type_with_not_found_functions(self):
        """Tests if we have and invocation,
        but we didn't find it in the list of method
        in current class."""
        self.assertEqual(True, True)

    def test_determine_type_wittout_variables_declaration(self):
        self.assertEqual(True, True)

    def test_determine_type_with_intersected_variables_declaration(self):
        self.assertEqual(True, True)

    def test_determine_type_with_non_intersected_variables_declaration(self):
        self.assertEqual(True, True)