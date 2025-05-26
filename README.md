# Lexy - Agentic Lexicon MCP Service

![](lexy/logo.jpg "Lexy Logo")

Lexy is an intelligent glossary service built on the Model Context Protocol (MCP) that provides contextual term lookup and definition services to agentic systems and code assistants.

## Features

- **Exact Term Lookup**: Case-insensitive direct term resolution with see-also support
- **Fuzzy Search**: Advanced approximate matching for typos and variations using rapidfuzz
- **Smart Query**: AI-powered contextual search using PydanticAI for natural language queries
- **MCP Integration**: JSON-RPC based protocol for seamless LLM tool integration
- **Configurable**: Support for OpenAI and Gemini models via environment variables

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd lexy

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
```

### 2. Configuration

Edit `.env` file with your settings:

```bash
# AI Model (default: google-gla:gemini-2.0-flash)
LEXY_MODEL=google-gla:gemini-2.0-flash

# API Key (set the one matching your model)
#OPENAI_API_KEY=your_openai_api_key_here
#GEMINI_API_KEY=your_gemini_api_key_here

# Server settings (optional)
MCP_SERVER_NAME=lexy-server
MCP_HOST=0.0.0.0
MCP_PORT=3040

# Glossary file path (optional)
GLOSSARY_PATH=glossary.yaml
```

### 3. Start the MCP Server

```bash
python -m lexy
```

The server will start on `http://localhost:[PORT]` using Server-Sent Events (SSE) transport.

## MCP Tools

Lexy exposes five main tools via the Model Context Protocol:

### `lookup_term`
Direct term lookup with exact matching.

```json
{
  "name": "lookup_term",
  "arguments": {
    "term": "MCP"
  }
}
```

### `batch_lookup_terms`
Batch processing for multiple lookup_term operations.

```json
{
  "name": "batch_lookup_terms",
  "arguments" {
    "terms":["MCP", "sus"]
  }
}
```

**Response:**
```json
{
  "term": "MCP",
  "found": true,
  "definitions": ["Model Context Protocol. A JSON-RPC based protocol..."],
  "see_also": ["Model Context Protocol", "model context protocol"],
  "confidence": 1.0
}
```

### `fuzzy_search`
Approximate matching for typos and variations.

```json
{
  "name": "fuzzy_search",
  "arguments": {
    "query": "Kronus",
    "threshold": 80
  }
}
```

### `smart_query`
AI-powered contextual search using natural language.

```json
{
  "name": "smart_query",
  "arguments": {
    "query": "What are the current security projects?",
    "context": "Looking for project codenames"
  }
}
```

### `list_terms`
Browse available terms with optional filtering.

```json
{
  "name": "list_terms",
  "arguments": {
    "prefix": "S",
    "tag": "project"
  }
}
```

## Glossary Format

Lexy uses a structured YAML format where each definition has its own see-also references:

```yaml
Mid:
  definitions:
    - text: "Average or not that good."
      see_also:
        - "mediocre"
        - "meh"
        - "average"
```

### Features:
- **Multiple definitions**: Each term can have multiple definitions
- **Definition-specific see-also**: Each definition can have its own related terms and aliases
- **Semantic precision**: See-also relationships are tied to specific meanings, not the entire term
- **Case-insensitive lookup**: Terms are matched regardless of case
- **Bidirectional aliases**: See-also terms automatically resolve to the main term

## Integration Examples

### Using with Cursor/Claude

Add Lexy as an MCP server in your Claude configuration:

```json
{
  "mcpServers": {
    "lexy": {
      "command": "python",
      "args": ["-m","path/to/lexy"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Using with Other MCP Clients

Lexy follows the standard MCP protocol and can be used with any MCP-compatible client. Connect to:
- **Transport**: SSE (Server-Sent Events)
- **URL**: `http://localhost:3040/sse`

## Development

### Project Structure

```
├── lexy/                  # Core package modules
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Main MCP server entry point
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic data models
│   ├── glossary.py        # Glossary data management
│   └── search.py          # Search functionality (exact, fuzzy, agentic)
├── glossary.yaml          # Sample glossary data
├── requirements.txt       # Python dependencies
├── env.example            # Environment template
└──  README.md             # This file
```
