"""
Configuration management for Lexy MCP Server.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for Lexy."""
    
    # Server Configuration
    MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "lexy-server")
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "3040"))
    
    # AI Model Configuration
    DEFAULT_MODEL = os.getenv("LEXY_MODEL", "openai:gpt-4o-mini")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Glossary Configuration
    GLOSSARY_PATH = os.getenv("GLOSSARY_PATH", "glossary.yaml")
    
    @classmethod
    def has_api_key_for_model(cls, model: str) -> bool:
        """Check if we have the required API key for the given model."""
        if model.startswith("openai:"):
            return cls.OPENAI_API_KEY is not None
        elif model.startswith(("gemini:", "google-gla:")):
            return cls.GEMINI_API_KEY is not None
        elif model.startswith("anthropic:"):
            return cls.ANTHROPIC_API_KEY is not None
        return False
    
    @classmethod
    def get_missing_key_warning(cls, model: str) -> str:
        """Get warning message for missing API key."""
        if model.startswith("openai:"):
            return "Warning: OPENAI_API_KEY not set but using OpenAI model"
        elif model.startswith(("gemini:", "google-gla:")):
            return "Warning: GEMINI_API_KEY not set but using Gemini model"
        elif model.startswith("anthropic:"):
            return "Warning: ANTHROPIC_API_KEY not set but using Anthropic model"
        return f"Warning: Unknown model type: {model}" 