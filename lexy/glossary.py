"""
Glossary data management for Lexy.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any

from .models import GlossaryTerm, Definition


class GlossaryManager:
    """Manages loading and accessing glossary data."""
    
    def __init__(self, glossary_path: str):
        self.glossary_path = glossary_path
        self.glossary: Dict[str, Dict[str, Any]] = {}
        self.normalized_terms: Dict[str, str] = {}  # lowercase -> original case
        self.all_searchable_terms: List[str] = []  # For search processing
        self.load_glossary()
    
    def load_glossary(self):
        """Load glossary from YAML file."""
        try:
            if Path(self.glossary_path).exists():
                with open(self.glossary_path, 'r', encoding='utf-8') as f:
                    # Auto-detect format based on file extension
                    self.glossary = yaml.safe_load(f)
                        
                
                self._build_search_indexes()
                print(f"Loaded {len(self.glossary)} terms from {self.glossary_path}")
            else:
                print(f"Glossary file {self.glossary_path} not found, starting with empty glossary")
        except Exception as e:
            print(f"Error loading glossary: {e}")
            self.glossary = {}
            self.normalized_terms = {}
            self.all_searchable_terms = []
    
    def _build_search_indexes(self):
        """Build normalized lookup and searchable terms list."""
        self.normalized_terms = {}
        self.all_searchable_terms = []
        
        for term in self.glossary.keys():
            # Add main term
            self.normalized_terms[term.lower()] = term
            self.all_searchable_terms.append(term)
            
            # Add see-also terms for reverse lookup
            term_data = self.glossary[term]
            for definition in term_data.get('definitions', []):
                if isinstance(definition, dict) and 'see_also' in definition:
                    for see_also in definition['see_also']:
                        self.normalized_terms[see_also.lower()] = term
                        self.all_searchable_terms.append(see_also)
    
    def get_term_data(self, term: str) -> Dict[str, Any]:
        """Get raw term data from glossary."""
        return self.glossary.get(term, {})
    
    def get_term_object(self, term: str) -> GlossaryTerm:
        """Get a GlossaryTerm object from the new format."""
        term_data = self.get_term_data(term)
        if not term_data:
            return GlossaryTerm(term=term, definitions=[])
        
        # Convert dict definitions to Definition objects
        definitions = []
        for def_data in term_data.get('definitions', []):
            if isinstance(def_data, dict):
                definitions.append(Definition(
                    text=def_data.get('text', ''),
                    see_also=def_data.get('see_also', [])
                ))
            else:
                # Fallback for unexpected format
                definitions.append(Definition(text=str(def_data), see_also=[]))
        
        return GlossaryTerm(term=term, definitions=definitions)
    
    def term_exists(self, term: str) -> bool:
        """Check if a term exists in the glossary."""
        return term in self.glossary
    
    def get_original_term(self, normalized_term: str) -> str:
        """Get original term from normalized (lowercase) version."""
        return self.normalized_terms.get(normalized_term.lower(), normalized_term)
    
    def list_terms(self, prefix: str = None) -> List[str]:
        """List available terms with optional prefix filtering."""
        terms = list(self.glossary.keys())
        
        if prefix:
            prefix_lower = prefix.lower()
            terms = [term for term in terms if term.lower().startswith(prefix_lower)]
        
        return sorted(terms)
    
    def get_all_terms_text(self) -> str:
        """Get all terms and definitions as text for AI processing."""
        text_parts = []
        for term in self.glossary.keys():
            term_obj = self.get_term_object(term)
            definitions_text = "; ".join([def_.text for def_ in term_obj.definitions])
            text_parts.append(f"{term}: {definitions_text}")
            
            # Add see-also information
            all_see_also = []
            for definition in term_obj.definitions:
                all_see_also.extend(definition.see_also)
            
            if all_see_also:
                unique_see_also = list(set(all_see_also))
                text_parts.append(f"  (See also: {', '.join(unique_see_also)})")
        
        return "\n".join(text_parts)
    
    def save_glossary(self):
        """Save the current glossary to file."""
        try:
            with open(self.glossary_path, 'w', encoding='utf-8') as f:
                # Auto-detect format based on file extension
                yaml.dump(self.glossary, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"Saved glossary to {self.glossary_path}")
        except Exception as e:
            print(f"Error saving glossary: {e}") 