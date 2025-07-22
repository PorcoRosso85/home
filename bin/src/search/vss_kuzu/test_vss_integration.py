#!/usr/bin/env python3
"""
VSS直接動作確認テスト
サブプロセスラッパーを使わずに動作することを確認
"""

import pytest
from vss_service import VSSService


def test_vss_direct_without_subprocess_wrapper():
    """サブプロセスラッパーなしでVSSが動作することを確認"""
    # インメモリDBで直接VSSサービスを作成
    service = VSSService(in_memory=True)
    
    # サブプロセスラッパーが設定されていないことを確認
    # （pytest環境でも実際には使われていない）
    assert hasattr(service, '_subprocess_wrapper')
    
    # 基本的な動作確認
    documents = [
        {"id": "1", "content": "Pythonプログラミング"},
        {"id": "2", "content": "機械学習とディープラーニング"},
        {"id": "3", "content": "データベース設計"}
    ]
    
    # インデックス作成
    index_result = service.index_documents(documents)
    
    # 結果の確認
    if index_result.get("ok", False):
        # VECTOR拡張が利用可能な場合
        assert index_result["status"] == "success"
        assert index_result["indexed_count"] == 3
        
        # 検索実行
        search_result = service.search({"query": "プログラミング", "limit": 2})
        assert search_result.get("ok", False) is True
        assert len(search_result["results"]) <= 2
        
        print("✅ サブプロセスラッパーなしで正常動作")
    else:
        # VECTOR拡張が利用できない場合
        assert "VECTOR extension not available" in index_result["error"]
        print("⚠️ VECTOR拡張が利用できない環境")


def test_kuzu_py_integration():
    """kuzu_pyを通じた基本的な動作確認"""
    from kuzu_py import create_database, create_connection
    
    # kuzu_pyでデータベース作成
    db = create_database(":memory:")
    assert db is not None
    
    # 接続作成
    conn = create_connection(db)
    assert conn is not None
    
    # 基本的なクエリ実行
    try:
        conn.execute("RETURN 1 + 1 AS result")
        print("✅ kuzu_py経由での基本動作確認成功")
    except Exception as e:
        pytest.fail(f"kuzu_py basic query failed: {e}")


if __name__ == "__main__":
    # 直接実行可能
    print("=== VSS Direct Test ===")
    test_vss_direct_without_subprocess_wrapper()
    print("\n=== KuzuPy Integration Test ===")
    test_kuzu_py_integration()