#!/usr/bin/env python
"""
佐藤さん（Tech Lead）による技術的なテストスクリプト
"""
import os
import sys
import json

# プロジェクトパスを設定
project_root = "/home/nixos/bin/src"
sys.path.insert(0, project_root)

# 環境変数を設定
os.environ["RGL_DB_PATH"] = "/tmp/test_rgl_sato_db"

from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema
from requirement.graph.main import main as rgl_main

def test_schema_init():
    """スキーマ初期化テスト"""
    print("=== スキーマ初期化テスト ===")
    result = apply_ddl_schema(create_test_data=False)
    print(f"スキーマ初期化結果: {result}")
    return result

def test_create_requirement():
    """要件作成テスト"""
    print("\n=== 要件作成テスト ===")
    
    # テスト用の要件データ
    requirements = [
        {
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "arch_001",
                "title": "マイクロサービスアーキテクチャ",
                "description": "システム全体をマイクロサービス化"
            }
        },
        {
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "arch_002",
                "title": "API Gateway",
                "description": "マイクロサービス用のAPIゲートウェイ実装"
            }
        },
        {
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": "arch_003",
                "title": "サービスメッシュ",
                "description": "Istioを使用したサービスメッシュの構築"
            }
        }
    ]
    
    for req in requirements:
        input_json = json.dumps(req)
        print(f"\n入力: {req['parameters']['title']}")
        
        # stdinの代わりに文字列から読み込む
        import io
        sys.stdin = io.StringIO(input_json)
        
        try:
            result = rgl_main()
            print(f"結果: 成功")
        except Exception as e:
            print(f"結果: エラー - {e}")

def test_add_dependency():
    """依存関係追加テスト"""
    print("\n=== 依存関係追加テスト ===")
    
    dependencies = [
        {"child_id": "arch_002", "parent_id": "arch_001"},
        {"child_id": "arch_003", "parent_id": "arch_001"},
    ]
    
    for dep in dependencies:
        input_data = {
            "type": "template",
            "template": "add_dependency",
            "parameters": dep
        }
        
        input_json = json.dumps(input_data)
        print(f"\n依存関係: {dep['child_id']} → {dep['parent_id']}")
        
        import io
        sys.stdin = io.StringIO(input_json)
        
        try:
            result = rgl_main()
            print(f"結果: 成功")
        except Exception as e:
            print(f"結果: エラー - {e}")

def test_duplicate_detection():
    """重複検出テスト"""
    print("\n=== 重複検出テスト ===")
    
    # 類似した要件を追加して重複検出を確認
    duplicate_req = {
        "type": "template",
        "template": "create_requirement",
        "parameters": {
            "id": "arch_004",
            "title": "マイクロサービスアーキテクチャー",  # arch_001と類似
            "description": "システムをマイクロサービスで構成"
        }
    }
    
    input_json = json.dumps(duplicate_req)
    print(f"類似要件: {duplicate_req['parameters']['title']}")
    
    import io
    sys.stdin = io.StringIO(input_json)
    
    try:
        result = rgl_main()
        print("結果: 重複が検出されるべきだが、システムが許可した")
    except Exception as e:
        print(f"結果: {e}")

def test_search():
    """検索機能テスト"""
    print("\n=== 検索機能テスト ===")
    
    search_query = {
        "type": "template",
        "template": "search_requirements",
        "parameters": {
            "query": "マイクロサービス",
            "limit": 5
        }
    }
    
    input_json = json.dumps(search_query)
    print(f"検索クエリ: {search_query['parameters']['query']}")
    
    import io
    sys.stdin = io.StringIO(input_json)
    
    try:
        result = rgl_main()
        print("結果: 検索成功")
    except Exception as e:
        print(f"結果: エラー - {e}")

if __name__ == "__main__":
    # テスト実行
    if test_schema_init():
        test_create_requirement()
        test_add_dependency()
        test_duplicate_detection()
        test_search()
    else:
        print("スキーマ初期化に失敗しました")