"""
Lexy - Agentic Lexicon MCP Service

A modular glossary service for AI agents and code assistants.
"""

__version__ = "1.0.0"
__author__ = "Lexy Team"

from .glossary import GlossaryManager
from .search import ExactSearch, FuzzySearch, AgenticSearch
from .models import GlossaryTerm, TermResult

__all__ = [
    "GlossaryManager",
    "ExactSearch", 
    "FuzzySearch",
    "AgenticSearch",
    "GlossaryTerm",
    "TermResult"
] 