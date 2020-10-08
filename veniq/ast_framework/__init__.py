from .ast_node_type import ASTNodeType  # noqa: F401
from .ast_node import ASTNode  # noqa: F401
from .ast import AST  # noqa: F401
from .builder import build_ast  # noqa: F401

# register all standard computed fields from 'computed_fields_catalog'
from veniq.ast_framework.computed_fields_catalog.standard_fields import (
    register_standard_computed_properties,
)

register_standard_computed_properties()
