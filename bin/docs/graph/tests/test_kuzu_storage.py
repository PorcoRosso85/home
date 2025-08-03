import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from domain.models import Document, Node, Edge
from infrastructure.persistence.kuzu_adapter import KuzuAdapter


class TestKuzuStorage:
    """Test KuzuDB adapter CRUD operations and VSS persistence."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def kuzu_adapter(self, temp_db_path):
        """Create KuzuAdapter instance with temporary database."""
        return KuzuAdapter(temp_db_path)
    
    def test_create_and_read_document(self, kuzu_adapter):
        """Test document creation and retrieval."""
        # Create document
        doc = Document(
            id="doc1",
            content="Test document content",
            metadata={"type": "test", "version": "1.0"}
        )
        kuzu_adapter.save_document(doc)
        
        # Read document
        retrieved = kuzu_adapter.get_document("doc1")
        assert retrieved is not None
        assert retrieved.id == "doc1"
        assert retrieved.content == "Test document content"
        assert retrieved.metadata == {"type": "test", "version": "1.0"}
    
    def test_update_document(self, kuzu_adapter):
        """Test document update operation."""
        # Create initial document
        doc = Document(id="doc1", content="Original content")
        kuzu_adapter.save_document(doc)
        
        # Update document
        updated_doc = Document(
            id="doc1",
            content="Updated content",
            metadata={"updated": True}
        )
        kuzu_adapter.save_document(updated_doc)
        
        # Verify update
        retrieved = kuzu_adapter.get_document("doc1")
        assert retrieved.content == "Updated content"
        assert retrieved.metadata == {"updated": True}
    
    def test_delete_document(self, kuzu_adapter):
        """Test document deletion."""
        # Create document
        doc = Document(id="doc1", content="To be deleted")
        kuzu_adapter.save_document(doc)
        
        # Delete document
        kuzu_adapter.delete_document("doc1")
        
        # Verify deletion
        retrieved = kuzu_adapter.get_document("doc1")
        assert retrieved is None
    
    def test_node_crud_operations(self, kuzu_adapter):
        """Test node CRUD operations."""
        # Create node
        node = Node(
            id="node1",
            type="concept",
            properties={"name": "Test Node", "weight": 0.8}
        )
        kuzu_adapter.save_node(node)
        
        # Read node
        retrieved = kuzu_adapter.get_node("node1")
        assert retrieved is not None
        assert retrieved.id == "node1"
        assert retrieved.type == "concept"
        assert retrieved.properties["name"] == "Test Node"
        
        # Update node
        node.properties["weight"] = 0.9
        kuzu_adapter.save_node(node)
        retrieved = kuzu_adapter.get_node("node1")
        assert retrieved.properties["weight"] == 0.9
        
        # Delete node
        kuzu_adapter.delete_node("node1")
        assert kuzu_adapter.get_node("node1") is None
    
    def test_edge_crud_operations(self, kuzu_adapter):
        """Test edge CRUD operations."""
        # Create nodes first
        node1 = Node(id="node1", type="concept")
        node2 = Node(id="node2", type="concept")
        kuzu_adapter.save_node(node1)
        kuzu_adapter.save_node(node2)
        
        # Create edge
        edge = Edge(
            source_id="node1",
            target_id="node2",
            type="relates_to",
            properties={"strength": 0.7}
        )
        kuzu_adapter.save_edge(edge)
        
        # Read edges
        edges = kuzu_adapter.get_edges_from_node("node1")
        assert len(edges) == 1
        assert edges[0].source_id == "node1"
        assert edges[0].target_id == "node2"
        assert edges[0].properties["strength"] == 0.7
    
    @patch('infrastructure.persistence.kuzu_adapter.EmbeddingService')
    def test_vss_initial_index_creation(self, mock_embedding_service, kuzu_adapter):
        """Test VSS index creation on first run."""
        # Mock embedding service
        mock_service = Mock()
        mock_service.get_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_embedding_service.return_value = mock_service
        
        # Create documents
        docs = [
            Document(id="doc1", content="First document"),
            Document(id="doc2", content="Second document"),
            Document(id="doc3", content="Third document")
        ]
        
        for doc in docs:
            kuzu_adapter.save_document(doc)
        
        # Build VSS index
        kuzu_adapter.build_vss_index()
        
        # Verify embeddings were created
        assert mock_service.get_embedding.call_count == 3
        
        # Verify index exists
        assert kuzu_adapter.has_vss_index()
    
    @patch('infrastructure.persistence.kuzu_adapter.EmbeddingService')
    def test_vss_skip_on_second_run(self, mock_embedding_service, kuzu_adapter):
        """Test VSS index skip behavior on second run."""
        # Mock embedding service
        mock_service = Mock()
        mock_service.get_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_embedding_service.return_value = mock_service
        
        # Create documents and build index
        doc = Document(id="doc1", content="Test document")
        kuzu_adapter.save_document(doc)
        kuzu_adapter.build_vss_index()
        
        # Reset call count
        mock_service.get_embedding.reset_mock()
        
        # Second run should skip
        kuzu_adapter.build_vss_index()
        
        # Verify no new embeddings were created
        assert mock_service.get_embedding.call_count == 0
    
    @patch('infrastructure.persistence.kuzu_adapter.EmbeddingService')
    def test_vss_embedding_retrieval(self, mock_embedding_service, kuzu_adapter):
        """Test embedding retrieval from VSS index."""
        # Mock embedding service
        mock_service = Mock()
        expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_service.get_embedding.return_value = expected_embedding
        mock_embedding_service.return_value = mock_service
        
        # Create document and build index
        doc = Document(id="doc1", content="Test document")
        kuzu_adapter.save_document(doc)
        kuzu_adapter.build_vss_index()
        
        # Retrieve embedding
        retrieved_embedding = kuzu_adapter.get_document_embedding("doc1")
        
        # Verify embedding
        assert retrieved_embedding == expected_embedding
    
    def test_list_all_documents(self, kuzu_adapter):
        """Test listing all documents."""
        # Create multiple documents
        docs = [
            Document(id=f"doc{i}", content=f"Document {i}")
            for i in range(5)
        ]
        
        for doc in docs:
            kuzu_adapter.save_document(doc)
        
        # List all documents
        all_docs = kuzu_adapter.list_documents()
        assert len(all_docs) == 5
        assert all(doc.id in [f"doc{i}" for i in range(5)] for doc in all_docs)
    
    def test_transaction_rollback(self, kuzu_adapter):
        """Test transaction rollback on error."""
        # Create document
        doc = Document(id="doc1", content="Original")
        kuzu_adapter.save_document(doc)
        
        # Attempt update that fails
        with pytest.raises(Exception):
            with kuzu_adapter.transaction():
                # Update document
                updated = Document(id="doc1", content="Updated")
                kuzu_adapter.save_document(updated)
                # Force error
                raise Exception("Simulated error")
        
        # Verify original document unchanged
        retrieved = kuzu_adapter.get_document("doc1")
        assert retrieved.content == "Original"