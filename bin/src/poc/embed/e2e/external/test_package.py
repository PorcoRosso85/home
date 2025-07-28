"""
External package test following nix_flake conventions
"""
def test_embed_package_importable():
    """Test that the package can be imported"""
    import embed_pkg
    assert embed_pkg is not None

def test_embedding_repository_available():
    """Test that embedding repository can be created"""
    from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone as create_embedding_repository
    # メモリDBでテスト
    repo = create_embedding_repository(":memory:")
    assert "save_with_embedding" in repo

def test_embedder_types_available():
    """Test that embedder types are available"""
    from embed_pkg.embeddings.base import create_embedder
    # エラーハンドリングのテスト
    result = create_embedder("invalid-model", "invalid-type")
    assert result.get("ok") is False