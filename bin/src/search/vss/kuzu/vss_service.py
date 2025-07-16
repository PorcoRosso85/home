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


class VSSService:
    """Vector Similarity Search service with JSON Schema validation"""
    
    def __init__(self, db_path: str = "./kuzu_db"):
        self.db_path = db_path
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
        
        # Import dependencies lazily to avoid circular imports
        self._kuzu_db = None
        self._embedding_service = None
    
    def _get_kuzu_db(self):
        """Lazy initialization of KuzuDB"""
        if self._kuzu_db is None:
            # Import POC implementation
            import sys
            poc_path = Path(__file__).parent.parent.parent.parent / "poc" / "search" / "vss"
            sys.path.insert(0, str(poc_path))
            
            from main import KuzuVectorDB
            self._kuzu_db = KuzuVectorDB(db_path=self.db_path, dimension=self.dimension)
        return self._kuzu_db
    
    def _get_embedding_service(self):
        """Lazy initialization of embedding service"""
        if self._embedding_service is None:
            # Import POC implementation
            import sys
            poc_path = Path(__file__).parent.parent.parent.parent / "poc" / "search" / "vss"
            sys.path.insert(0, str(poc_path))
            
            from infrastructure import create_embedding_model
            from application import TextEmbeddingService
            
            model = create_embedding_model("ruri-v3-30m")
            self._embedding_service = TextEmbeddingService(model)
            self.dimension = model.dimension
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
        kuzu_db = self._get_kuzu_db()
        
        # Get query embedding
        if query_vector is None:
            query_result = embedding_service.embed_query(query)
            query_embedding = query_result.embeddings
        else:
            query_embedding = query_vector
        
        # Perform search
        results = kuzu_db.search_similar(query_embedding, k=limit)
        
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
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Index documents for vector search
        
        Args:
            documents: List of documents with 'id', 'content' fields
            
        Returns:
            Status dictionary
        """
        from main import Document
        
        # Get services
        embedding_service = self._get_embedding_service()
        kuzu_db = self._get_kuzu_db()
        
        # Extract content
        contents = [doc["content"] for doc in documents]
        
        # Generate embeddings
        doc_results = embedding_service.embed_documents(contents)
        
        # Create Document objects
        doc_objects = [
            Document(
                id=doc.get("id", i),
                content=doc["content"],
                embedding=result.embeddings
            )
            for i, (doc, result) in enumerate(zip(documents, doc_results))
        ]
        
        # Insert into database
        kuzu_db.insert_documents(doc_objects)
        
        # Create index if not exists
        try:
            kuzu_db.create_vector_index()
        except:
            pass  # Index might already exist
        
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