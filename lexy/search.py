"""
Search functionality for Lexy glossary service.
"""

from typing import List, Optional
from rapidfuzz import fuzz, process
from pydantic_ai import Agent, RunContext

from .models import TermResult
from .glossary import GlossaryManager


class ExactSearch:
    """Handles exact term lookups with case-insensitive matching."""

    def __init__(self, glossary_manager: GlossaryManager):
        self.glossary = glossary_manager

    def lookup(self, term: str) -> List[TermResult]:
        """Exact term lookup with case-insensitive matching."""
        normalized_term = term.lower()

        if normalized_term in self.glossary.normalized_terms:
            original_term = self.glossary.normalized_terms[normalized_term]
            term_obj = self.glossary.get_term_object(original_term)

            return [TermResult(
                term=original_term,
                definitions=term_obj.definitions,
                confidence=1.0,
                match_type="exact"
            )]

        # If not found, provide fuzzy suggestions as potential matches
        fuzzy_search = FuzzySearch(self.glossary)
        suggestions = fuzzy_search.search(term, threshold=60)[:3]  # Top 3 suggestions

        # Mark them as suggestions
        for suggestion in suggestions:
            suggestion.match_type = "suggestion"

        return suggestions


class FuzzySearch:
    """Handles fuzzy matching using rapidfuzz for typos and variations."""

    def __init__(self, glossary_manager: GlossaryManager):
        self.glossary = glossary_manager

    def search(self, query: str, threshold: int = 80) -> List[TermResult]:
        """Fuzzy search with similarity scoring using rapidfuzz."""
        if not self.glossary.all_searchable_terms:
            return []

        results = []
        seen_terms = set()

        # Use rapidfuzz to find matches
        matches = process.extract(
            query,
            self.glossary.all_searchable_terms,
            scorer=fuzz.WRatio,
            limit=10,  # Get more matches to filter
            score_cutoff=threshold
        )

        for match_text, score, _ in matches:
            # Get the original term this match belongs to
            original_term = self.glossary.get_original_term(match_text)

            # Avoid duplicates
            if original_term in seen_terms:
                continue
            seen_terms.add(original_term)

            # Only include if it's actually in our glossary
            if self.glossary.term_exists(original_term):
                term_obj = self.glossary.get_term_object(original_term)
                results.append(TermResult(
                    term=original_term,
                    definitions=term_obj.definitions,
                    confidence=score / 100.0,  # Convert to 0-1 scale
                    match_type="fuzzy"
                ))

        # Sort by confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results

    def get_suggestions(self, query: str, threshold: int = 80, max_suggestions: int = 5) -> List[str]:
        """Get fuzzy matching suggestions using rapidfuzz."""
        if not self.glossary.all_searchable_terms:
            return []

        # Use rapidfuzz to find the best matches
        matches = process.extract(
            query,
            self.glossary.all_searchable_terms,
            scorer=fuzz.WRatio,  # Weighted ratio for better results
            limit=max_suggestions,
            score_cutoff=threshold
        )

        # Convert matches to original terms and deduplicate
        suggestions = []
        seen_terms = set()

        for match_text, score, _ in matches:
            # Get the original term this match belongs to
            original_term = self.glossary.get_original_term(match_text)
            if original_term not in seen_terms:
                suggestions.append(original_term)
                seen_terms.add(original_term)

        return suggestions


class AgenticSearch:
    """Handles AI-powered contextual search using PydanticAI."""

    def __init__(self, glossary_manager: GlossaryManager, model: str = "google-gla:gemini-2.0-flash"):
        self.glossary = glossary_manager
        self.model = model
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the PydanticAI agent if possible."""
        try:
            self.agent = Agent(
                self.model,
                deps_type=str,  # Will pass glossary text as dependency
                output_type=List[str],
                system_prompt=(
                    'You are a glossary search expert. Given a user query and a glossary of terms, '
                    'find the most relevant terms that match the user\'s intent. '
                    'Consider synonyms, related concepts, context, and partial matches. '
                    'Return a list of term names (exact matches from the glossary) that are most relevant. '
                    'Return at most 5 terms, ordered by relevance.'
                ),
            )

            @self.agent.tool
            async def search_glossary_content(ctx: RunContext[str], query: str) -> str:
                """Search through the glossary content for relevant terms."""
                return f"User query: {query}\n\nGlossary content:\n{ctx.deps}"

        except Exception as e:
            print(f"Warning: Could not initialize AI agent: {e}")
            self.agent = None

    async def search(self, query: str, context: Optional[str] = None) -> List[TermResult]:
        """AI-powered contextual search across the glossary."""
        if self.agent is None:
            # Fallback to fuzzy search
            print("AI agent not available, falling back to fuzzy search")
            fuzzy_search = FuzzySearch(self.glossary)
            results = fuzzy_search.search(query, threshold=60)[:3]
            # Mark as agentic fallback
            for result in results:
                result.match_type = "agentic_fallback"
            return results

        try:
            # Prepare the search query with context
            full_query = query
            if context:
                full_query = f"{query} (Context: {context})"

            # Get glossary content for AI analysis
            glossary_text = self.glossary.get_all_terms_text()

            # Run AI agent to find relevant terms
            result = await self.agent.run(full_query, deps=glossary_text)
            relevant_terms = result.output

            # Look up the full details for each relevant term
            responses = []

            for term in relevant_terms:
                if self.glossary.term_exists(term):
                    term_obj = self.glossary.get_term_object(term)
                    responses.append(TermResult(
                        term=term,
                        definitions=term_obj.definitions,
                        confidence=1.0,  # AI found it relevant
                        match_type="agentic"
                    ))

            return responses

        except Exception as e:
            print(f"Error in agentic search: {e}")
            # Fallback to fuzzy search
            fuzzy_search = FuzzySearch(self.glossary)
            results = fuzzy_search.search(query, threshold=60)[:3]
            # Mark as agentic fallback
            for result in results:
                result.match_type = "agentic_fallback"
            return results
