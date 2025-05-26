#!/usr/bin/env python3
"""
Lexy MCP Server - Clean modular implementation.
"""

import sys
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

from .config import Config
from .glossary import GlossaryManager
from .search import ExactSearch, FuzzySearch, AgenticSearch


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    # Initialize components
    glossary_manager = GlossaryManager(Config.GLOSSARY_PATH)
    exact_search = ExactSearch(glossary_manager)
    fuzzy_search = FuzzySearch(glossary_manager)
    agentic_search = AgenticSearch(glossary_manager, Config.DEFAULT_MODEL)
    
    # Create server
    server = FastMCP(
        name=Config.MCP_SERVER_NAME, 
        host=Config.MCP_HOST, 
        port=Config.MCP_PORT
    )
    
    # Register tools
    @server.tool()
    async def lookup_term(term: str) -> List[dict]:
        """
        Look up a specific term in the glossary with exact matching.
        
        Args:
            term: The term to look up
            
        Returns:
            List of matching terms (usually 1 for exact match, or suggestions if not found)
        """
        print(f"MCP Tool 'lookup_term' called with: term='{term}'")
        
        results = exact_search.lookup(term)
        response = [result.model_dump() for result in results]
        
        if results and results[0].match_type == "exact":
            print(f"Exact match found: {results[0].term}")
        else:
            print(f"No exact match, returning {len(results)} suggestions")
        
        return response

    @server.tool()
    async def batch_lookup_terms(terms: List[str]) -> dict:
        """
        Look up multiple terms at once to reduce round trips.
        
        Args:
            terms: List of terms to look up
            
        Returns:
            Dictionary mapping each term to its lookup results
        """
        print(f"MCP Tool 'batch_lookup_terms' called with {len(terms)} terms: {terms}")
        
        results = {}
        for term in terms:
            lookup_results = exact_search.lookup(term)
            results[term] = [result.model_dump() for result in lookup_results]
        
        exact_matches = sum(1 for term_results in results.values() 
                          if term_results and term_results[0].get('match_type') == 'exact')
        print(f"Batch lookup completed: {exact_matches}/{len(terms)} exact matches found")
        
        return results

    @server.tool()
    async def fuzzy_search_terms(query: str, threshold: int = 80) -> List[dict]:
        """
        Search for terms using fuzzy matching for typos and variations.
        
        Args:
            query: The search query
            threshold: Similarity threshold (0-100), default 80
            
        Returns:
            List of matching terms with similarity scores
        """
        print(f"MCP Tool 'fuzzy_search' called with: query='{query}', threshold={threshold}")
        
        results = fuzzy_search.search(query, threshold)
        response = [result.model_dump() for result in results]
        
        print(f"Fuzzy search found {len(results)} matches")
        return response

    @server.tool()
    async def smart_query(query: str, context: Optional[str] = None) -> List[dict]:
        """
        AI-powered contextual search across the glossary using natural language.
        
        Args:
            query: Natural language query describing what you're looking for
            context: Optional additional context to help with the search
            
        Returns:
            List of relevant terms found by AI analysis
        """
        print(f"MCP Tool 'smart_query' called with: query='{query}', context='{context}'")
        
        results = await agentic_search.search(query, context)
        response = [result.model_dump() for result in results]
        
        print(f"Smart query found {len(results)} relevant terms")
        return response

    @server.tool()
    async def list_terms(prefix: Optional[str] = None) -> List[str]:
        """
        List available terms in the glossary with optional filtering.
        
        Args:
            prefix: Optional prefix to filter terms (case-insensitive)
            
        Returns:
            List of term names matching the filters
        """
        print(f"MCP Tool 'list_terms' called with: prefix='{prefix}'")
        
        terms = glossary_manager.list_terms(prefix=prefix)
        
        print(f"Listed {len(terms)} terms")
        return terms
    
    return server


def main():
    """Main entry point."""
    print(f"Starting Lexy MCP Server...")
    print(f"Server: {Config.MCP_SERVER_NAME}")
    print(f"Host: {Config.MCP_HOST}:{Config.MCP_PORT}")
    print(f"AI Model: {Config.DEFAULT_MODEL}")
    print(f"Glossary: {Config.GLOSSARY_PATH}")
    
    # Check API keys
    if not Config.has_api_key_for_model(Config.DEFAULT_MODEL):
        print(Config.get_missing_key_warning(Config.DEFAULT_MODEL))
    
    try:
        server = create_server()
        server.run(transport="sse")
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 