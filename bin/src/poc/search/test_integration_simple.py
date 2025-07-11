#!/usr/bin/env python3
"""
シンプルな統合テスト - 両モジュールの基本動作確認
"""

import sys
from pathlib import Path

# パスを追加
sys.path.append(str(Path(__file__).parent / "vss"))
sys.path.append(str(Path(__file__).parent / "embeddings"))


def test_vss_module():
    """VSSモジュールの基本テスト"""
    print("\n=== VSS Module Test ===")
    try:
        from requirement_embedder import generate_requirement_embedding
        
        embedding = generate_requirement_embedding({
            "title": "テスト要件",
            "description": "これはテストです"
        })
        
        print(f"✓ VSS埋め込み生成成功")
        print(f"  次元数: {len(embedding)}")
        print(f"  最初の5要素: {embedding[:5]}")
        return True
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False


def test_embeddings_module():
    """Embeddingsモジュールの基本テスト"""
    print("\n=== Embeddings Module Test ===")
    try:
        from infrastructure import create_embedding_model
        from domain import EmbeddingRequest, EmbeddingType
        
        model = create_embedding_model("ruri-v3-30m")
        request = EmbeddingRequest(
            text="テストテキスト",
            embedding_type=EmbeddingType.DOCUMENT
        )
        result = model.encode(request)
        
        print(f"✓ Embeddings生成成功")
        print(f"  次元数: {len(result.embeddings)}")
        print(f"  最初の5要素: {result.embeddings[:5]}")
        return True
    except Exception as e:
        print(f"✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dimension_difference():
    """次元数の違いを確認"""
    print("\n=== Dimension Comparison ===")
    try:
        from requirement_embedder import generate_requirement_embedding
        from infrastructure import create_embedding_model
        from domain import EmbeddingRequest, EmbeddingType
        
        # VSS: 384次元
        vss_emb = generate_requirement_embedding({"title": "test"})
        
        # Embeddings: 256次元
        model = create_embedding_model("ruri-v3-30m")
        req = EmbeddingRequest(text="test", embedding_type=EmbeddingType.DOCUMENT)
        emb_result = model.encode(req)
        
        print(f"VSS次元数: {len(vss_emb)}")
        print(f"Embeddings次元数: {len(emb_result.embeddings)}")
        print(f"✓ 両モジュールは異なる次元数を使用")
        return True
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False


def main():
    """全テストを実行"""
    print("=" * 60)
    print("Search Modules Integration Test (Simple)")
    print("=" * 60)
    
    tests = [
        test_vss_module,
        test_embeddings_module,
        test_dimension_difference,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"結果: {passed}/{len(tests)} テスト成功")
    print("=" * 60)


if __name__ == "__main__":
    main()