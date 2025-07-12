#!/usr/bin/env python
"""
POC Search統合の実動作確認テスト
POC searchの既存機能をrequirement/graphから利用
"""
import sys
import os

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, '/home/nixos/bin/src')

def test_poc_search_import():
    """POC searchモジュールのインポート確認"""
    try:
        from poc.search.infrastructure.search_service_factory import SearchServiceFactory
        print("✅ POC search import successful")
        
        # テスト用のサービス作成
        search_service = SearchServiceFactory.create_for_test()
        print(f"✅ SearchService created: {type(search_service)}")
        
        # インターフェースメソッドの確認
        methods = ['search_hybrid', 'search_vector', 'search_fulltext']
        for method in methods:
            if hasattr(search_service, method):
                print(f"✅ Method '{method}' available")
            else:
                print(f"❌ Method '{method}' NOT available")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_search_functionality():
    """ハイブリッド検索の動作確認"""
    try:
        from poc.search.infrastructure.search_service_factory import SearchServiceFactory
        
        # テスト用サービス作成
        search_service = SearchServiceFactory.create_for_test()
        
        # テストデータを追加（POC searchのインターフェースに従う）
        test_docs = [
            {
                "id": "req_001",
                "content": "ユーザー認証機能の実装",
                "metadata": {"title": "認証機能", "type": "functional"}
            },
            {
                "id": "req_002", 
                "content": "ユーザーログイン機能の実装",
                "metadata": {"title": "ログイン機能", "type": "functional"}
            }
        ]
        
        # ドキュメント追加（メソッドが存在する場合）
        if hasattr(search_service, 'add_documents'):
            search_service.add_documents(test_docs)
            print("✅ Test documents added")
        else:
            print("⚠️ add_documents method not available")
        
        # ハイブリッド検索実行
        results = search_service.search_hybrid("認証", k=5)
        print(f"✅ Hybrid search executed: {len(results)} results")
        
        for idx, result in enumerate(results):
            print(f"  Result {idx+1}: {result.get('id')} - Score: {result.get('score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_integration_class():
    """SearchIntegrationクラスの動作確認"""
    try:
        from application.search_integration import SearchIntegration
        
        # SearchIntegration作成
        search_integration = SearchIntegration()
        print(f"✅ SearchIntegration created: {search_integration.search_service is not None}")
        
        # 重複チェック機能
        duplicates = search_integration.check_duplicates("ユーザー認証機能", k=3, threshold=0.5)
        print(f"✅ Duplicate check executed: {len(duplicates)} duplicates found")
        
        return True
        
    except Exception as e:
        print(f"❌ SearchIntegration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== POC Search統合テスト ===\n")
    
    # 1. インポート確認
    print("1. POC Searchモジュールのインポート確認")
    import_ok = test_poc_search_import()
    print()
    
    # 2. ハイブリッド検索機能確認
    print("2. ハイブリッド検索の動作確認")
    hybrid_ok = test_hybrid_search_functionality()
    print()
    
    # 3. SearchIntegrationクラス確認
    print("3. SearchIntegrationクラスの動作確認")
    integration_ok = test_search_integration_class()
    print()
    
    # 結果サマリー
    print("=== テスト結果サマリー ===")
    print(f"POC Search import: {'✅ PASS' if import_ok else '❌ FAIL'}")
    print(f"Hybrid search: {'✅ PASS' if hybrid_ok else '❌ FAIL'}")
    print(f"SearchIntegration: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    
    all_passed = import_ok and hybrid_ok and integration_ok
    print(f"\n総合結果: {'✅ すべてのテストが成功' if all_passed else '❌ 一部のテストが失敗'}")