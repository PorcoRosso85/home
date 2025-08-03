"""Minimal integration test for Pyright LSP client."""

import pytest
import asyncio
from pathlib import Path
import tempfile
from graph_docs.pyright_client import PyrightLSPClient


@pytest.mark.asyncio
async def test_pyright_lsp_basic_flow():
    """Test basic Pyright LSP client flow: initialize, get symbols, shutdown."""
    # Create a temporary workspace with a simple Python file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "example.py"
        test_file.write_text("""
def hello():
    return "world"

class Example:
    def method(self):
        pass
""")
        
        # Test the client
        client = PyrightLSPClient()
        
        # Initialize
        await client.initialize(tmpdir)
        assert client.is_initialized
        
        # Get document symbols
        result = await client.get_document_symbols(str(test_file))
        
        # Basic assertions
        assert result['ok'] is True
        symbols = result['symbols']
        assert len(symbols) > 0
        symbol_names = [s['name'] for s in symbols]
        assert 'hello' in symbol_names
        assert 'Example' in symbol_names
        assert 'method' in symbol_names
        
        # Shutdown
        await client.shutdown()
        assert not client.is_initialized