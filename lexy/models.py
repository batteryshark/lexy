"""
Data models for Lexy glossary service.
"""

from typing import List
from pydantic import BaseModel


class Definition(BaseModel):
    """A single definition with its own see-also references."""
    text: str
    see_also: List[str] = []


class GlossaryTerm(BaseModel):
    """A single glossary term with definitions and see-also references."""
    term: str
    definitions: List[Definition]


class TermResult(BaseModel):
    """A term result with metadata."""
    term: str
    definitions: List[Definition]
    confidence: float = 1.0  # 1.0 for exact matches, <1.0 for fuzzy matches
    match_type: str = "exact"  # "exact", "fuzzy", "suggestion", "agentic"
    
    @property
    def all_see_also(self) -> List[str]:
        """Get all see-also terms from all definitions."""
        all_terms = []
        for definition in self.definitions:
            all_terms.extend(definition.see_also)
        return list(set(all_terms))  # Remove duplicates
    
    @property
    def definition_texts(self) -> List[str]:
        """Get just the definition text strings for backward compatibility."""
        return [definition.text for definition in self.definitions] 