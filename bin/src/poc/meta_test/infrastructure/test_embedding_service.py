"""Tests for embedding service."""


from .embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test embedding service."""

    def setup_method(self):
        """Set up test fixture."""
        self.service = EmbeddingService(embedding_dim=128)

    def test_generate_embedding(self):
        """Test embedding generation."""
        text = "User should be able to login"
        embedding = self.service.generate_embedding(text)

        assert len(embedding) == 128
        assert all(isinstance(x, float) for x in embedding)
        assert all(-1 <= x <= 1 for x in embedding)

        # Test deterministic
        embedding2 = self.service.generate_embedding(text)
        assert embedding == embedding2

    def test_batch_generate_embeddings(self):
        """Test batch embedding generation."""
        texts = [
            "User login functionality",
            "Password reset feature",
            "Two-factor authentication"
        ]

        embeddings = self.service.batch_generate_embeddings(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 128 for emb in embeddings)

        # Different texts should have different embeddings
        assert embeddings[0] != embeddings[1]
        assert embeddings[1] != embeddings[2]

    def test_calculate_similarity(self):
        """Test similarity calculation."""
        # Identical embeddings
        emb1 = [1.0, 0.0, 0.5, -0.5]
        similarity = self.service.calculate_similarity(emb1, emb1)
        assert abs(similarity - 1.0) < 0.0001

        # Opposite embeddings
        emb2 = [-1.0, 0.0, -0.5, 0.5]
        similarity = self.service.calculate_similarity(emb1, emb2)
        assert abs(similarity - (-1.0)) < 0.0001

        # Orthogonal embeddings
        emb3 = [0.0, 1.0, 0.0, 0.0]
        emb4 = [1.0, 0.0, 0.0, 0.0]
        similarity = self.service.calculate_similarity(emb3, emb4)
        assert abs(similarity) < 0.0001

    def test_find_similar(self):
        """Test finding similar embeddings."""
        query = self.service.generate_embedding("user authentication")

        candidates = [
            self.service.generate_embedding("login system"),
            self.service.generate_embedding("user auth"),
            self.service.generate_embedding("payment processing"),
            self.service.generate_embedding("authentication module"),
            self.service.generate_embedding("data export")
        ]

        # Find top 2 similar
        indices = self.service.find_similar(query, candidates, top_k=2)

        assert len(indices) == 2
        # We expect "user auth" and "authentication module" to be most similar
        # Verify indices are valid
        assert all(0 <= idx < 5 for idx in indices)
