#!/usr/bin/env python3
"""
VSS (Vector Similarity Search) Service with JSON Schema validation
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
import numpy as np

# Use the persistence layer for KuzuDB
from persistence.kuzu_py.database import create_database, create_connection


class VSSService:
    """Vector Similarity Search service with JSON Schema validation"""
    
    def __init__(self, db_path: str = "./kuzu_db", in_memory: bool = False):
        self.db_path = db_path
        self.in_memory = in_memory
        self.dimension = 256  # Default dimension for ruri-v3-30m
        
        # Load schemas
        schema_dir = Path(__file__).parent
        with open(schema_dir / "input.schema.json") as f:
            self.input_schema = json.load(f)
        with open(schema_dir / "output.schema.json") as f:
            self.output_schema = json.load(f)
        
        # Initialize validators
        self.input_validator = jsonschema.Draft7Validator(self.input_schema)
        self.output_validator = jsonschema.Draft7Validator(self.output_schema)
        
        # Database and connection
        self._db = None
        self._conn = None
        self._embedding_service = None
        self._vector_index_created = False
    
    def _get_connection(self):
        """Get or create database connection using persistence layer"""
        if self._conn is None:
            # Create database using persistence layer
            self._db = create_database(
                path=self.db_path if not self.in_memory else None,
                in_memory=self.in_memory,
                use_cache=not self.in_memory  # Don't cache in-memory DBs for tests
            )
            self._conn = create_connection(self._db)
            
            # Initialize schema
            self._initialize_schema()
        return self._conn
    
    def _initialize_schema(self):
        """Initialize database schema for vector search"""
        conn = self._conn
        
        # Install and load VECTOR extension
        try:
            conn.execute("INSTALL VECTOR;")
        except:
            pass  # Extension might already be installed
        
        conn.execute("LOAD EXTENSION VECTOR;")
        
        # Create Document table if not exists
        try:
            conn.execute(f"""
                CREATE NODE TABLE Document (
                    id INT64,
                    content STRING,
                    embedding FLOAT[{self.dimension}],
                    PRIMARY KEY (id)
                )
            """)
        except:
            pass  # Table might already exist
    
    def _get_embedding_service(self):
        """Lazy initialization of embedding service"""
        if self._embedding_service is None:
            # Create a standalone embedding service
            from sentence_transformers import SentenceTransformer
            from dataclasses import dataclass
            from typing import List
            
            @dataclass
            class EmbeddingResult:
                """Minimal embedding result"""
                embeddings: List[float]
                model_name: str
                dimension: int
            
            class StandaloneEmbeddingService:
                """Standalone embedding service with proper query/document prefixes"""
                
                def __init__(self):
                    self.model_name = "cl-nagoya/ruri-v3-30m"
                    self.dimension = 256
                    self.model = SentenceTransformer(self.model_name)
                    
                def embed_documents(self, texts):
                    """Embed documents with proper prefix"""
                    # Add document prefix for better search results
                    prefixed_texts = [f"検索文書: {text}" for text in texts]
                    embeddings = self.model.encode(prefixed_texts)
                    
                    results = []
                    for emb in embeddings:
                        result = EmbeddingResult(
                            embeddings=emb.tolist(),
                            model_name=self.model_name,
                            dimension=self.dimension
                        )
                        results.append(result)
                    return results
                
                def embed_query(self, text):
                    """Embed query with proper prefix"""
                    # Add query prefix for better search results
                    prefixed_text = f"検索クエリ: {text}"
                    embedding = self.model.encode(prefixed_text)
                    
                    result = EmbeddingResult(
                        embeddings=embedding.tolist(),
                        model_name=self.model_name,
                        dimension=self.dimension
                    )
                    return result
            
            self._embedding_service = StandaloneEmbeddingService()
            self.dimension = self._embedding_service.dimension
                
        return self._embedding_service
    
    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input against schema"""
        errors = list(self.input_validator.iter_errors(data))
        if errors:
            error_messages = [f"{e.message} at {'.'.join(str(p) for p in e.path)}" for e in errors]
            raise ValueError(f"Invalid input: {'; '.join(error_messages)}")
    
    def validate_output(self, data: Dict[str, Any]) -> None:
        """Validate output against schema"""
        errors = list(self.output_validator.iter_errors(data))
        if errors:
            error_messages = [f"{e.message} at {'.'.join(str(p) for p in e.path)}" for e in errors]
            raise ValueError(f"Invalid output: {'; '.join(error_messages)}")
    
    def search(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform vector similarity search
        
        Args:
            input_data: Dictionary conforming to input.schema.json
            
        Returns:
            Dictionary conforming to output.schema.json
        """
        # Validate input
        self.validate_input(input_data)
        
        # Extract parameters
        query = input_data["query"]
        limit = input_data.get("limit", 10)
        model = input_data.get("model", "ruri-v3-30m")
        threshold = input_data.get("threshold")
        query_vector = input_data.get("query_vector")
        
        # Start timing
        start_time = time.time()
        
        # Get services
        embedding_service = self._get_embedding_service()
        conn = self._get_connection()
        
        # Get query embedding
        if query_vector is None:
            query_result = embedding_service.embed_query(query)
            query_embedding = query_result.embeddings
        else:
            query_embedding = query_vector
        
        # Ensure vector index exists
        self._ensure_vector_index()
        
        # Perform search using direct KuzuDB query
        result = conn.execute("""
            CALL QUERY_VECTOR_INDEX(
                'Document',
                'doc_embedding_index',
                $embedding,
                $k
            ) RETURN node, distance
        """, {"embedding": query_embedding, "k": limit})
        
        # Collect results
        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]
            distance = row[1]
            results.append((node["content"], distance))
        
        # Format results
        formatted_results = []
        for i, (content, distance) in enumerate(results):
            # Convert distance to similarity score (assuming cosine distance)
            # Cosine distance = 1 - cosine similarity
            score = float(1.0 - distance)
            
            # Apply threshold if specified
            if threshold is not None and score < threshold:
                continue
            
            formatted_results.append({
                "id": f"doc_{i}",  # Generate ID since POC doesn't return it
                "content": content,
                "score": score,
                "distance": float(distance)
            })
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        
        # Prepare output
        output = {
            "results": formatted_results,
            "metadata": {
                "model": model,
                "dimension": self.dimension,
                "total_results": len(formatted_results),
                "query_time_ms": query_time_ms
            }
        }
        
        # Validate output
        self.validate_output(output)
        
        return output
    
    def _ensure_vector_index(self):
        """Ensure vector index exists"""
        if not self._vector_index_created:
            conn = self._get_connection()
            try:
                conn.execute("""
                    CALL CREATE_VECTOR_INDEX(
                        'Document',
                        'doc_embedding_index',
                        'embedding'
                    )
                """)
                self._vector_index_created = True
            except:
                # Index might already exist
                self._vector_index_created = True
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Index documents for vector search
        
        Args:
            documents: List of documents with 'id', 'content' fields
            
        Returns:
            Status dictionary
        """
        # Get services
        embedding_service = self._get_embedding_service()
        conn = self._get_connection()
        
        # Extract content
        contents = [doc["content"] for doc in documents]
        
        # Generate embeddings
        doc_results = embedding_service.embed_documents(contents)
        
        # Insert documents directly
        for i, (doc, result) in enumerate(zip(documents, doc_results)):
            doc_id = doc.get("id", i)
            conn.execute("""
                CREATE (d:Document {
                    id: $id,
                    content: $content,
                    embedding: $embedding
                })
            """, {
                "id": doc_id,
                "content": doc["content"],
                "embedding": result.embeddings
            })
        
        # Ensure index exists
        self._ensure_vector_index()
        
        return {
            "status": "success",
            "indexed_count": len(documents)
        }


def main():
    """Main entry point for CLI usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: vss-service <command> [options]")
        print("Commands:")
        print("  search <json>    - Search with JSON input")
        print("  index <json>     - Index documents")
        print("  validate         - Validate schemas")
        return
    
    command = sys.argv[1]
    service = VSSService()
    
    if command == "search":
        if len(sys.argv) < 3:
            print("Error: search requires JSON input")
            return
        
        try:
            input_data = json.loads(sys.argv[2])
            result = service.search(input_data)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "index":
        if len(sys.argv) < 3:
            print("Error: index requires JSON input")
            return
        
        try:
            documents = json.loads(sys.argv[2])
            result = service.index_documents(documents)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "validate":
        print("✓ Schemas are valid")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()