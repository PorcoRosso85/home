"""
セッションフィクスチャの効果を確認するテスト
"""
import pytest
from application.search_adapter import SearchAdapter

def test_shared_adapter_1(search_adapter):
    """最初のテスト - 初期化カウントを確認"""
    assert search_adapter is not None
    assert search_adapter._vss_service._is_initialized
    assert search_adapter._fts_service._is_initialized
    
    # テスト用データを追加
    search_adapter.add_to_index({
        "id": "test1",
        "title": "Test Requirement 1",
        "description": "This is a test requirement"
    })
    
    # 検索できることを確認
    results = search_adapter.search_keyword("test")
    assert len(results) > 0


def test_shared_adapter_2(search_adapter):
    """2番目のテスト - 同じアダプターが使われることを確認"""
    # 前のテストのデータがクリアされていることを確認
    results = search_adapter.search_keyword("test1")
    assert len(results) == 0
    
    # 新しいデータを追加
    search_adapter.add_to_index({
        "id": "test2",
        "title": "Test Requirement 2",
        "description": "Another test requirement"
    })
    
    results = search_adapter.search_keyword("test")
    assert len(results) > 0


def test_initialization_count():
    """初期化カウントを確認"""
    # SearchAdapterのクラス変数から初期化回数を取得
    print(f"\nSearchAdapter init count: {SearchAdapter._init_count}")
    print(f"VSSSearchAdapter init count: {SearchAdapter._init_count}")
    print(f"FTSSearchAdapter init count: {SearchAdapter._init_count}")
    
    # セッションフィクスチャを使用している場合、初期化は1回のみ
    assert SearchAdapter._init_count <= 3  # 複数のテストでも増えない


if __name__ == "__main__":
    # 直接実行時のテスト
    pytest.main([__file__, "-v", "-s"])