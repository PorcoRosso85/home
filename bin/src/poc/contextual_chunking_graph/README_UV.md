# Contextual Chunking Graph-Powered RAG with UV

This is a POC version of the Contextual Chunking Graph-Powered RAG system, configured to work with `uv` for Python package management.

## Prerequisites

1. **Python 3.8+**
2. **uv** - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **API Keys** for:
   - OpenAI
   - Anthropic (Claude)
   - Cohere
   - LlamaCloud (for PDF parsing)

## Quick Start

1. **Configure API Keys**:
   ```bash
   cp sample.env .env
   # Edit .env and add your actual API keys
   ```

2. **Run with the simple runner**:
   ```bash
   python run.py
   ```

## Manual Setup with UV

If you prefer to set up manually:

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Run the application**:
   ```bash
   uv run python -m contextual_chunking_graph.main
   ```

## Alternative Run Methods

1. **Using the installed script**:
   ```bash
   uv run contextual-rag
   ```

2. **Direct module execution**:
   ```bash
   uv run python src/contextual_chunking_graph/main.py
   ```

## Project Structure

```
contextual_chunking_graph/
├── src/contextual_chunking_graph/    # Package source
│   ├── __init__.py                   # Package initialization
│   ├── main.py                       # Entry point
│   └── rag.py                        # Core RAG implementation
├── pyproject.toml                    # UV/Python project configuration
├── .env                              # Environment variables
├── run.py                            # Simple runner script
└── README_UV.md                      # This file
```

## Features

- **Hybrid Search**: Combines FAISS vector search with BM25 keyword search
- **Knowledge Graph**: Builds and traverses concept graphs for better context
- **Contextual Chunking**: Preserves context across document boundaries
- **Answer Verification**: Ensures complete answers through context expansion
- **Visualization**: Shows graph traversal paths and relationships

## Usage

1. Start the application using any of the run methods above
2. When prompted, enter the path to your PDF file
3. Wait for the system to process the document and build the knowledge graph
4. Enter your questions about the document
5. Type 'exit' to quit

The system will display the answer along with token usage and cost information.

## Development

To contribute or modify:

1. **Install dev dependencies**:
   ```bash
   uv sync --extra dev
   ```

2. **Run formatting**:
   ```bash
   uv run black .
   uv run isort .
   ```

3. **Run tests** (if any):
   ```bash
   uv run pytest
   ```

## Troubleshooting

- **Missing API keys**: Make sure all required API keys are set in the `.env` file
- **UV not found**: Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Dependencies failing**: Try `uv sync --force-reinstall`
- **PDF parsing errors**: Ensure your LlamaCloud API key is valid and the PDF is readable