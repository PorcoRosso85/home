#!/usr/bin/env python3
"""
Test configuration for VSS Kuzu tests

Provides mock implementations for VECTOR extension functions to allow tests
to run without requiring the actual VECTOR extension to be installed.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, List, Tuple, Dict, Optional
import os


# Set environment variable to disable VECTOR extension checks in tests
os.environ['VSS_KUZU_MOCK_VECTOR'] = '1'


class MockKuzuConnection:
    """Mock KuzuDB connection with VECTOR extension support"""
    
    def __init__(self):
        self._tables = {}
        self._documents = {}
        self._vector_indices = {}
        self._executed_queries = []
    
    def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Mock execute method that simulates VECTOR extension operations"""
        self._executed_queries.append((query, params))
        
        # Handle INSTALL/LOAD EXTENSION
        if "INSTALL VECTOR" in query or "LOAD EXTENSION VECTOR" in query:
            return None
            
        # Handle CREATE NODE TABLE
        if "CREATE NODE TABLE" in query:
            return None
            
        # Handle CREATE VECTOR INDEX call
        if "CREATE_VECTOR_INDEX" in query:
            return None
            
        # Handle MERGE for document insertion
        if "MERGE" in query and params:
            doc_id = params.get("id")
            if doc_id:
                self._documents[doc_id] = {
                    "id": doc_id,
                    "content": params.get("content"),
                    "embedding": params.get("embedding")
                }
            return None
            
        # Handle QUERY_VECTOR_INDEX
        if "QUERY_VECTOR_INDEX" in query and params:
            # Return mock search results
            results = []
            query_vector = params.get("query_vector", [])
            limit = params.get("limit", 10)
            
            # Simulate returning some mock results
            for i, (doc_id, doc) in enumerate(list(self._documents.items())[:limit]):
                # Simple cosine similarity simulation (always returns same distance for testing)
                distance = 0.1 * (i + 1)
                results.append((doc, distance))
            
            return MockQueryResult(results)
            
        # Handle COUNT query
        if "COUNT" in query:
            return MockQueryResult([(len(self._documents),)])
            
        # Handle DROP TABLE
        if "DROP TABLE" in query:
            return None
            
        return None
    
    def close(self):
        """Mock close method"""
        pass


class MockQueryResult:
    """Mock query result object"""
    
    def __init__(self, results: List[Tuple]):
        self._results = results
        self._index = 0
    
    def has_next(self) -> bool:
        return self._index < len(self._results)
    
    def get_next(self) -> Tuple:
        if self._index < len(self._results):
            result = self._results[self._index]
            self._index += 1
            # Convert dict to mock node object for search results
            if isinstance(result[0], dict):
                node = Mock()
                node.get = lambda key: result[0].get(key)
                return (node, result[1])
            return result
        return None


class MockKuzuDatabase:
    """Mock KuzuDB database object"""
    
    def __init__(self, path: str):
        self.path = path


@pytest.fixture(autouse=True)
def mock_kuzu_imports():
    """Automatically mock kuzu_py imports for all tests"""
    
    def mock_create_database(path: str) -> MockKuzuDatabase:
        return MockKuzuDatabase(path)
    
    def mock_create_connection(database: Any) -> MockKuzuConnection:
        return MockKuzuConnection()
    
    with patch('vss_kuzu.infrastructure.create_database', mock_create_database), \
         patch('vss_kuzu.infrastructure.create_connection', mock_create_connection):
        yield


@pytest.fixture(autouse=True)
def mock_vector_extension_functions():
    """Mock VECTOR extension functions to simulate their behavior"""
    
    def mock_check_vector_extension(connection: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
        # Always return success in test environment
        return True, None
    
    def mock_initialize_vector_schema(
        connection: Any, 
        dimension: int,
        mu: int = 30,
        ml: int = 60,
        metric: str = 'cosine',
        efc: int = 200
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        # For MockKuzuConnection, simulate success
        if isinstance(connection, MockKuzuConnection):
            return True, None
        # For real connections, simulate VECTOR extension not available
        return False, {
            "error": "VECTOR extension not available",
            "details": {
                "extension": "VECTOR",
                "install_command": "INSTALL VECTOR",
                "raw_error": "Extension VECTOR has not been installed"
            }
        }
    
    def mock_search_similar_vectors(
        connection: Any,
        query_vector: List[float],
        limit: int = 10,
        efs: int = 200
    ) -> Tuple[bool, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        # For MockKuzuConnection, simulate success with mock results
        if isinstance(connection, MockKuzuConnection):
            results = []
            for i in range(min(3, limit)):
                results.append({
                    "id": f"doc{i+1}",
                    "content": f"Document {i+1}",
                    "distance": 0.1 * (i + 1),
                    "embedding": [0.1] * len(query_vector)
                })
            return True, results, None
        # For real connections, simulate VECTOR extension not available
        return False, [], {
            "error": "VECTOR extension not available or index not created",
            "details": {
                "extension": "VECTOR",
                "function": "QUERY_VECTOR_INDEX",
                "index_name": "doc_embedding_index",
                "install_command": "INSTALL VECTOR",
                "raw_error": "Function QUERY_VECTOR_INDEX does not exist"
            }
        }
    
    def mock_insert_documents_with_embeddings(
        connection: Any,
        documents: List[Tuple[str, str, List[float]]]
    ) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
        # For MockKuzuConnection, simulate successful insertion
        if isinstance(connection, MockKuzuConnection):
            for doc_id, content, embedding in documents:
                connection._documents[doc_id] = {
                    "id": doc_id,
                    "content": content,
                    "embedding": embedding
                }
            return True, len(documents), None
        # For other connections, return success
        return True, len(documents), None
    
    def mock_count_documents(connection: Any) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
        # For MockKuzuConnection, return document count
        if isinstance(connection, MockKuzuConnection):
            return True, len(connection._documents), None
        # For other connections, return 0
        return True, 0, None
    
    with patch('vss_kuzu.infrastructure.check_vector_extension', mock_check_vector_extension), \
         patch('vss_kuzu.infrastructure.initialize_vector_schema', mock_initialize_vector_schema), \
         patch('vss_kuzu.infrastructure.search_similar_vectors', mock_search_similar_vectors), \
         patch('vss_kuzu.infrastructure.insert_documents_with_embeddings', mock_insert_documents_with_embeddings), \
         patch('vss_kuzu.infrastructure.count_documents', mock_count_documents):
        yield


@pytest.fixture
def mock_connection():
    """Provide a mock connection for tests that need direct access"""
    return MockKuzuConnection()


@pytest.fixture
def sample_embeddings():
    """Provide sample embeddings for testing"""
    import random
    
    def generate_embedding(dimension: int = 256) -> List[float]:
        """Generate a random embedding vector"""
        return [random.random() for _ in range(dimension)]
    
    return {
        "doc1": generate_embedding(),
        "doc2": generate_embedding(),
        "doc3": generate_embedding(),
        "query": generate_embedding()
    }


@pytest.fixture
def sample_documents(sample_embeddings):
    """Provide sample documents with embeddings"""
    return [
        ("doc1", "This is the first document", sample_embeddings["doc1"]),
        ("doc2", "This is the second document", sample_embeddings["doc2"]),
        ("doc3", "This is the third document", sample_embeddings["doc3"])
    ]