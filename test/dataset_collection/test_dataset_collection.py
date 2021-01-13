import unittest
from pathlib import Path
from unittest import TestCase

from veniq.dataset_collection.augmentation import (
    determine_algorithm_insertion_type,
    method_body_lines,
    is_match_to_the_conditions,
    find_lines_in_changed_file)
from veniq.ast_framework import AST, ASTNodeType
from veniq.dataset_collection.types_identifier import (
    InlineTypesAlgorithms,
    InlineWithoutReturnWithoutArguments,
    InlineWithReturnWithoutArguments,
    AlgorithmFactory)
from veniq.utils.ast_builder import build_ast


class TestDatasetCollection(TestCase):
    current_directory = Path(__file__).absolute().parent

    def setUp(self):
        self.filepath = self.current_directory / "Example.java"
        self.example_ast = AST.build_from_javalang(build_ast(self.filepath))
        self.temp_filename = self.current_directory / 'temp.java'

    def tearDown(self):
        if self.temp_filename.exists():
            self.temp_filename.unlink()

    def test_determine_type_without_return_without_arguments(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'method'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'method_without_params'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'method_without_params'][0]
        d = {'method_without_params': [m_decl_original]}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)
        self.assertEqual(type, InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS)

    def test_determine_type_with_return_without_parameters(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'reset_return_var_decl'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'closeServer_return'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'closeServer_return'][0]
        d = {'closeServer_return': [m_decl_original]}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)
        self.assertEqual(type, InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS)

    def test_determine_type_with_parameters(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'some_method'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'method_with_parameters'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'method_with_parameters'][0]
        d = {'method_with_parameters': [m_decl_original]}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)
        self.assertEqual(type, InlineTypesAlgorithms.DO_NOTHING)

    def test_determine_type_with_overridden_functions(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'invoke_overridden'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'overridden_func']
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'overridden_func'][0]
        d = {'overridden_func': m_decl_original}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)
        self.assertEqual(type, InlineTypesAlgorithms.DO_NOTHING)

    def test_determine_type_with_invalid_functions(self):
        """Tests if we have invocation,
        but we didn't find it in the list of method declarations
        in current class."""
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'invoke_overridden'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'overridden_func']
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'overridden_func'][0]
        d = {'SOME_RANDOM_NAME': m_decl_original}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)
        self.assertEqual(type, InlineTypesAlgorithms.DO_NOTHING)

    def test_determine_type_without_variables_declaration(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'method'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'method_without_params'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'method_without_params'][0]
        d = {'method_without_params': [m_decl_original]}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)
        self.assertEqual(type, InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS)

        # We consider all cases (with or without return)
        # if there are no variables, declared in invoked function

        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'method_with_return_not_var_decl'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'closeServer_return'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'closeServer_return'][0]
        d = {'closeServer_return': [m_decl_original]}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)

        self.assertEqual(type, InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS)

    def test_is_invocation_in_if_with_single_statement_valid(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'test_single_stat_in_if'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'intersected_var'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'intersected_var'][0]

        self.assertFalse(is_match_to_the_conditions(self.example_ast, m_inv, m_decl_original))

    def test_is_return_type_not_assigning_value_valid(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'method_decl'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'invocation'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'invocation'][0]
        self.assertFalse(is_match_to_the_conditions(self.example_ast, m_inv, m_decl_original))

    def test_determine_type_with_non_intersected_variables_declaration(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'test_not_intersected_var_decl'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'intersected_var'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'intersected_var'][0]
        d = {'intersected_var': [m_decl_original]}
        type = determine_algorithm_insertion_type(self.example_ast, m_decl, m_inv, d)
        self.assertTrue(type in [
            InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS,
            InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS])

    def _get_lines(self, file, function_name):
        ast = AST.build_from_javalang(build_ast(file))
        m_decl = [
            x for x in ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == function_name][0]
        return method_body_lines(m_decl, file)

    @unittest.skip("This functionality is not implemented")
    def test_inline_with_return_type_but_not_returning(self):
        """
        Test check whether we can inline code function with return type, but actually
        this function is not saving return value,
        so we do not need to declare a variable

        """
        algorithm = InlineWithReturnWithoutArguments()
        file = self.current_directory / 'InlineExamples' / 'ReturnTypeUseless.java'

        test_example = self.current_directory / 'InlineTestExamples' / 'ReturnTypeUseless.java'
        body_start_line, body_end_line = self._get_lines(file, 'invocation')

        algorithm.inline_function(file, 36, body_start_line, body_end_line, self.temp_filename)
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_example, encoding='utf-8') as test_ex:
            self.assertEqual(actual_file.read(), test_ex.read())

    def test_inline_with_return_type(self):
        algorithm = InlineWithReturnWithoutArguments()
        file = self.current_directory / 'InlineExamples' / 'ReaderHandler.java'
        test_example = self.current_directory / 'InlineTestExamples' / 'ReaderHandler.java'
        body_start_line, body_end_line = self._get_lines(file, 'getReceiverQueueSize')

        algorithm.inline_function(file, 76, body_start_line, body_end_line, self.temp_filename)
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_example, encoding='utf-8') as test_ex:
            self.assertEqual(test_ex.read(), actual_file.read())

    def test_inline_without_return_type(self):
        algorithm = InlineWithoutReturnWithoutArguments()
        file = self.current_directory / 'InlineExamples' / 'PlanetDialog.java'
        test_example = self.current_directory / 'InlineTestExamples' / 'PlanetDialog.java'
        body_start_line, body_end_line = self._get_lines(file, 'makeBloom')

        algorithm.inline_function(file, 70, body_start_line, body_end_line, self.temp_filename)
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_example, encoding='utf-8') as test_ex:
            self.assertEqual(actual_file.read(), test_ex.read())

    def test_is_valid_function_with_several_returns(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'runSeveralReturns'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'severalReturns'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'severalReturns'][0]
        is_matched = is_match_to_the_conditions(self.example_ast, m_inv, m_decl_original)
        self.assertEqual(is_matched, False)

    def test_is_valid_function_with_one_return(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'runDelete'][0]
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'delete'][0]
        m_inv = [
            x for x in self.example_ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'delete'][0]
        is_matched = is_match_to_the_conditions(self.example_ast, m_inv, m_decl_original)
        self.assertEqual(is_matched, True)

    def test_invocation_inside_if_not_process(self):
        filepath = self.current_directory / "Example_nested.java"
        ast = AST.build_from_javalang(build_ast(filepath))
        m_decl = [
            x for x in ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'doAction'][0]
        m_decl_original = [
            x for x in ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'handleAction'][0]
        m_inv = [
            x for x in ast.get_subtree(m_decl).get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'handleAction'][0]
        is_matched = is_match_to_the_conditions(ast, m_inv, m_decl_original)
        self.assertEqual(is_matched, False)

    def test_is_valid_function_with_return_in_the_middle(self):
        m_decl_original = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'severalReturns'][0]
        m_inv = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_INVOCATION)
            if x.member == 'severalReturns'][0]
        is_matched = is_match_to_the_conditions(self.example_ast, m_inv, m_decl_original)
        self.assertEqual(is_matched, False)

    def test_inline_invocation_inside_var_declaration(self):
        filepath = self.current_directory / 'InlineExamples' / 'EntityResolver_cut.java'
        test_filepath = self.current_directory / 'InlineTestExamples' / 'EntityResolver_cut.java'
        algorithm_type = InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        body_start_line, body_end_line = self._get_lines(filepath, 'createDocumentBuilderFactory')
        self.assertEqual(body_start_line == 33, body_end_line == 40)
        algorithm_for_inlining().inline_function(filepath, 22, body_start_line, body_end_line, self.temp_filename)
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_filepath, encoding='utf-8') as test_ex:
            self.assertEqual(actual_file.read(), test_ex.read())

    def test_inline_inside_invokation_several_lines(self):
        filepath = self.current_directory / 'InlineExamples' / 'AbstractMarshaller_cut.java'
        test_filepath = self.current_directory / 'InlineTestExamples' / 'AbstractMarshaller_cut.java'
        algorithm_type = InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        body_start_line, body_end_line = self._get_lines(filepath, 'fireChildRemoved')
        self.assertEqual(body_start_line == 17, body_end_line == 20)

        algorithm_for_inlining().inline_function(filepath, 14, body_start_line, body_end_line, self.temp_filename)
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_filepath, encoding='utf-8') as test_ex:
            self.assertEqual(actual_file.read(), test_ex.read())

    def test_inline_strange_body2(self):
        filepath = self.current_directory / 'InlineExamples' / 'cut.java'
        test_filepath = self.current_directory / 'InlineTestExamples' / 'cut.java'
        algorithm_type = InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        body_start_line, body_end_line = self._get_lines(filepath, 'copy')
        algorithm_for_inlining().inline_function(filepath,
                                                 8,
                                                 body_start_line,
                                                 body_end_line,
                                                 self.temp_filename)
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_filepath, encoding='utf-8') as test_ex:
            self.assertEqual(actual_file.read(), test_ex.read())

    def test_inline_comments_at_the_end(self):
        filepath = self.current_directory / 'InlineExamples' / 'ObjectProperties_cut.java'
        test_filepath = self.current_directory / 'InlineTestExamples' / 'ObjectProperties_cut.java'
        algorithm_type = InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        body_start_line, body_end_line = self._get_lines(filepath, 'updateSashWidths')
        algorithm_for_inlining().inline_function(filepath, 43, body_start_line, body_end_line, self.temp_filename)
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_filepath, encoding='utf-8') as test_ex:
            self.assertEqual(actual_file.read(), test_ex.read())

    def test_method_body_lines_1(self):
        m_decl = [
            x for x in self.example_ast.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION)
            if x.name == 'closeServer'][0]
        body_bounds = method_body_lines(m_decl, self.filepath)
        self.assertEqual((21, 27), body_bounds)

    def test_start_end_inline_without_args(self):
        algorithm_type = InlineTypesAlgorithms.WITHOUT_RETURN_WITHOUT_ARGUMENTS
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        pred_inline_rel_bounds = algorithm_for_inlining().inline_function(self.filepath,
                                                                          30,
                                                                          21,
                                                                          27,
                                                                          self.temp_filename)
        self.assertEqual([30, 34], pred_inline_rel_bounds,
                         msg='Wrong inline bounds: {}'.format(pred_inline_rel_bounds))

    def test_inline_with_return_with_var_declaration(self):
        filepath = self.current_directory / 'InlineExamples' / 'Parameters.java'
        test_filepath = self.current_directory / 'InlineTestExamples' / 'Parameters_with_var_declaration.java'
        algorithm_type = InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        body_start_line, body_end_line = self._get_lines(filepath, 'btSelectProperty')
        self.assertEqual(body_start_line == 60, body_end_line == 65)
        algorithm_for_inlining().inline_function(
            filepath,
            112,
            body_start_line,
            body_end_line,
            self.temp_filename
        )
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_filepath, encoding='utf-8') as test_ex:
            self.assertMultiLineEqual(actual_file.read(), test_ex.read(), 'File are not matched')

    def test_inline_with_return_with_assigning(self):
        filepath = self.current_directory / 'InlineExamples' / 'Parameters.java'
        test_filepath = self.current_directory / 'InlineTestExamples/Parameters_without_return_without_assigning.java'
        algorithm_type = InlineTypesAlgorithms.WITH_RETURN_WITHOUT_ARGUMENTS
        algorithm_for_inlining = AlgorithmFactory().create_obj(algorithm_type)
        body_start_line, body_end_line = self._get_lines(filepath, 'cboComponent')
        self.assertEqual(body_start_line == 40, body_end_line == 45)
        algorithm_for_inlining().inline_function(
            filepath,
            113,
            body_start_line,
            body_end_line,
            self.temp_filename
        )
        with open(self.temp_filename, encoding='utf-8') as actual_file, \
                open(test_filepath, encoding='utf-8') as test_ex:
            self.assertMultiLineEqual(actual_file.read(), test_ex.read(), 'File are not matched')

    def test_check(self):
        old_filename = self.current_directory / 'InlineExamples/PainlessParser.java'
        new_filename = self.current_directory / 'InlineTestExamples/PainlessParser.java'
        ast = AST.build_from_javalang(build_ast(old_filename))
        class_decl = [
            x for x in ast.get_proxy_nodes(ASTNodeType.CLASS_DECLARATION)
            if x.name == 'PainlessParser'][0]
        inlined_function_declaration = [
            x for x in class_decl.methods
            if x.name == 'trailer'][0]
        result = find_lines_in_changed_file(
            new_full_filename=new_filename,
            original_func=inlined_function_declaration,
            class_name='PainlessParser')

        self.assertEqual(result['invocation_method_start_line'], 1022)
        self.assertEqual(result['invocation_method_end_line'], 1083)
