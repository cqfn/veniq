from dataclasses import dataclass, field
from typing import Tuple, Set

from veniq.ast_framework import ASTNode

Statement = ASTNode


@dataclass
class StatementSemantic:
    used_objects: Set[str] = field(default_factory=set)
    used_methods: Set[str] = field(default_factory=set)

    def is_similar(self, other: "StatementSemantic") -> bool:
        return len(self.used_objects & other.used_objects) != 0 or \
            len(self.used_methods & other.used_methods) != 0


ExtractionOpportunity = Tuple[Statement, ...]

OpportunityBenifit = int
