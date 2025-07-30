"""Embedding service for semantic similarity calculations."""

import hashlib


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self, embedding_dim: int = 256):
        """Initialize embedding service."""
        self.embedding_dim = embedding_dim
        # In real implementation, this would use a proper embedding model

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        # Generate deterministic pseudo-embedding
        # In production, this would use sentence-transformers or similar

        # Hash the text for deterministic output
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        # Generate pseudo-embedding based on hash
        embedding = []
        for i in range(self.embedding_dim):
            # Use different parts of hash for each dimension
            chunk = text_hash[i % len(text_hash):(i % len(text_hash)) + 2]
            value = int(chunk, 16) / 255.0  # Normalize to [0, 1]
            embedding.append(value - 0.5)  # Center around 0

        return embedding

    def batch_generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [self.generate_embedding(text) for text in texts]

    def calculate_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between embeddings."""
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have same dimension")

        # Calculate dot product and norms
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_similar(self,
                    query_embedding: list[float],
                    candidate_embeddings: list[list[float]],
                    top_k: int = 5) -> list[int]:
        """Find most similar embeddings to query."""
        similarities = [
            (i, self.calculate_similarity(query_embedding, candidate))
            for i, candidate in enumerate(candidate_embeddings)
        ]

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top-k indices
        return [idx for idx, _ in similarities[:top_k]]
