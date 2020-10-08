from unittest import TestCase
from pathlib import Path

from veniq.utils.utils import flatten
from veniq.ast_framework import AST, ASTNodeType, build_ast
from veniq.ast_framework.java_class_decomposition import decompose_java_class
from veniq.metrics.ncss.ncss import NCSSMetric


class JavaClassDecompositionTestCase(TestCase):
    def test_strong_decomposition(self):
        class_ast = self._get_class_ast(
            "MethodUseOtherMethodExample.java", "MethodUseOtherMethod"
        )
        class_components = decompose_java_class(class_ast, "strong")
        self.assertEqual(len(class_components), 7)

    def test_weak_decomposition(self):
        class_ast = self._get_class_ast(
            "MethodUseOtherMethodExample.java", "MethodUseOtherMethod"
        )
        class_components = decompose_java_class(class_ast, "weak")
        self.assertEqual(len(class_components), 5)

    def test_ncss(self):
        test_data_folder = self._current_directory / "ncss"
        for filepath in test_data_folder.glob("*.java"):
            with self.subTest(f"Testing decomposition of {filepath}"):
                ast = build_ast(filepath)

                classes_ast = [
                    ast.get_subtree(node)
                    for node in ast.get_root().types
                    if node.node_type == ASTNodeType.CLASS_DECLARATION
                ]

                ncss_metric = NCSSMetric()

                # NCSS of a class may not be equal to sum of ncss of methods and fields
                # due to presence of nested classes. To bypass it we calculate NCSS only
                # of methods and fields.
                methods_ncss = 0
                fields_ncss = 0
                components_ncss = 0
                components_qty = 0

                for class_ast in classes_ast:
                    class_declaration = class_ast.get_root()

                    for method in class_declaration.methods:
                        methods_ncss += ncss_metric.value(class_ast.get_subtree(method))

                    for field in class_declaration.fields:
                        fields_ncss += ncss_metric.value(class_ast.get_subtree(field))

                    for component in decompose_java_class(class_ast, "strong"):
                        components_qty += 1
                        components_ncss += ncss_metric.value(component)

                # Each component has a CLASS_DECLARATION node. It increase NCSS of each component by 1.
                # To achieve equality we add number of components to the sum of NCSS of just methods and fields.
                self.assertEqual(methods_ncss + fields_ncss + components_qty, components_ncss)

    def test_ignore_setters(self):
        function_names = self._decompose_with_setter_functionality(ignore_setters=True)
        self.assertTrue('setSomething' not in function_names)
        self.assertTrue('setBitmap' not in function_names)

    def test_do_not_ignore_setters(self):
        function_names = self._decompose_with_setter_functionality(ignore_setters=False)
        self.assertTrue('setSomething' in function_names)
        self.assertTrue('setBitmap' in function_names)

    def test_ignore_getters(self):
        function_names = self._decompose_with_setter_functionality(ignore_getters=True)
        self.assertTrue('getWidth' not in function_names)

    def test_do_not_ignore_getters(self):
        function_names = self._decompose_with_setter_functionality(ignore_getters=False)
        self.assertTrue('getWidth' in function_names)

    @staticmethod
    def _get_class_ast(filename: str, class_name: str) -> AST:
        package_ast = build_ast(JavaClassDecompositionTestCase._current_directory / filename)
        package_declaration = package_ast.get_root()
        try:
            class_declaration = next(
                class_declaration
                for class_declaration in package_declaration.types
                if class_declaration.name == class_name
            )
            return package_ast.get_subtree(class_declaration)

        except StopIteration:
            raise ValueError(
                f"File '{filename}' does not have top level class '{class_name}'."
            )

    @staticmethod
    def _decompose_with_setter_functionality(ignore_getters=False, ignore_setters=False):
        ast = build_ast(JavaClassDecompositionTestCase._current_directory / "LottieImageAsset.java")
        classes_ast = [
            ast.get_subtree(node)
            for node in ast.get_root().types
            if node.node_type == ASTNodeType.CLASS_DECLARATION
        ]
        components = list(decompose_java_class(
            classes_ast[0],
            "strong",
            ignore_setters=ignore_setters,
            ignore_getters=ignore_getters))
        function_names = flatten([
            [x.name for x in list(c.get_proxy_nodes(ASTNodeType.METHOD_DECLARATION))]
            for c in components])
        return function_names

    _current_directory = Path(__file__).absolute().parent
