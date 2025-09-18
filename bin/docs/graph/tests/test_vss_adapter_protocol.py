"""Test VSS adapter protocol definition and dependency injection.

This test ensures that VSSAdapter follows layered architecture by accepting
embedding functions via dependency injection instead of importing from application layer.
"""

from typing import Protocol, List, runtime_checkable
import pytest


@runtime_checkable
class EmbeddingFunction(Protocol):
    """Protocol for embedding generation functions."""
    
    def __call__(self, text: str) -> List[float]:
        """Generate embedding vector from text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        ...


def test_embedding_function_protocol_definition():
    """Test that EmbeddingFunction protocol is properly defined."""
    # Create a mock embedding function
    def mock_embedding(text: str) -> List[float]:
        """Simple mock that returns fixed-size embedding."""
        return [0.1, 0.2, 0.3] * 100  # 300-dim vector
    
    # Verify it implements the protocol
    assert isinstance(mock_embedding, EmbeddingFunction)
    
    # Test it works as expected
    result = mock_embedding("test text")
    assert len(result) == 300
    assert all(isinstance(x, float) for x in result)


def test_vss_adapter_accepts_embedding_function():
    """Test that VSSAdapter can accept embedding function via constructor."""
    from flake_graph.vss_adapter import VSSAdapter
    from flake_graph.kuzu_adapter import KuzuAdapter
    
    # Create mock embedding function
    def mock_embedding(text: str) -> List[float]:
        return [0.5] * 384  # Standard embedding size
    
    # Create kuzu adapter (mock or test instance)
    kuzu_adapter = KuzuAdapter(db_path=":memory:")
    
    # VSSAdapter should accept embedding_func parameter
    vss_adapter = VSSAdapter(
        kuzu_adapter=kuzu_adapter,
        embedding_func=mock_embedding  # Dependency injection
    )
    
    # Verify embedding function is stored
    assert hasattr(vss_adapter, '_embedding_func')
    assert vss_adapter._embedding_func is mock_embedding


def test_vss_adapter_uses_injected_embedding_function():
    """Test that VSSAdapter uses the injected embedding function instead of importing."""
    from flake_graph.vss_adapter import VSSAdapter
    from flake_graph.kuzu_adapter import KuzuAdapter
    
    # Track calls to embedding function
    call_count = 0
    embedded_texts = []
    
    def tracking_embedding(text: str) -> List[float]:
        nonlocal call_count, embedded_texts
        call_count += 1
        embedded_texts.append(text)
        return [float(i) for i in range(384)]
    
    kuzu_adapter = KuzuAdapter(db_path=":memory:")
    vss_adapter = VSSAdapter(
        kuzu_adapter=kuzu_adapter,
        embedding_func=tracking_embedding
    )
    
    # Test that indexing uses our injected function
    test_flakes = [{
        "path": "/test/flake",
        "description": "Test flake description",
        "readme_content": "Test readme content"
    }]
    
    vss_adapter.index_flakes(test_flakes)
    
    # Verify our function was called
    assert call_count > 0
    assert any("Test flake description" in text for text in embedded_texts)


def test_no_direct_import_from_application_layer():
    """Test that vss_adapter.py does not import from vss_kuzu.application."""
    import ast
    from pathlib import Path
    
    # Read the vss_adapter.py file
    vss_adapter_path = Path(__file__).parent.parent / "flake_graph" / "vss_adapter.py"
    
    with open(vss_adapter_path, 'r') as f:
        tree = ast.parse(f.read())
    
    # Check for imports from vss_kuzu.application
    forbidden_imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "vss_kuzu.application" in node.module:
                forbidden_imports.append((node.module, [n.name for n in node.names]))
    
    # This test will fail initially, showing we need to refactor
    assert len(forbidden_imports) == 0, f"Found forbidden imports from application layer: {forbidden_imports}"