from unittest import TestCase, skip
from pathlib import Path

from veniq.ast_framework.java_package import JavaPackage


@skip('JavaClassField is deprecated')
class JavaClassFieldTestCase(TestCase):
    def test_field_name(self):
        java_package = JavaPackage(Path(__file__).parent.absolute() / 'TwoClasses.java')
        java_class = java_package.java_classes['Second']
        self.assertEqual(java_class.fields.keys(), {'x', 'y'})
