from dataclasses import dataclass, field
from itertools import accumulate
from typing import Tuple, Set

from veniq.ast_framework import ASTNode

Statement = ASTNode


@dataclass
class StatementSemantic:
    used_objects: Set[str] = field(default_factory=set)
    used_methods: Set[str] = field(default_factory=set)

    def is_similar(self, other: "StatementSemantic") -> bool:
        return len(self.used_objects_unwrapped & other.used_objects_unwrapped) != 0 or \
            len(self.used_methods & other.used_methods) != 0

    @property
    def used_objects_unwrapped(self) -> Set[str]:
        """
        Turns each name from "a.b.c" to "a", "a.b", "a.b.c"
        """
        return {
            ".".join(name_parts)
            for object_name in self.used_objects
            for name_parts in accumulate([name_part] for name_part in object_name.split("."))
        }

    @property
    def used_based_objects(self) -> Set[str]:
        """
        Turns each name from "a.b.c" to "a"
        """
        return {
            object_name.split(".")[0]
            for object_name in self.used_objects
        }


ExtractionOpportunity = Tuple[Statement, ...]

OpportunityBenifit = int
