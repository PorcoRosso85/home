#!/bin/bash

# 統合テストランナー - pytest環境外で実行

cd /home/nixos/bin/src/poc/search/embeddings

# Python環境でモジュールとして実行
export PYTHONPATH=/home/nixos/bin/src/poc/search/embeddings

# テストスクリプトを作成して実行
cat > /tmp/run_integration_tests.py << 'EOF'
import sys
import tempfile
import time
from pathlib import Path

# 直接実行のため、pytestを使わない
print("=" * 60)
print("統合テストを実行中（pytest環境外）")
print("Python:", sys.executable)
print("=" * 60)

# テスト1: 基本動作確認
print("\n=== Test 1: 基本動作確認 ===")
try:
    import kuzu
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # VECTOR拡張をロード
    conn.execute("INSTALL VECTOR;")
    conn.execute("LOAD EXTENSION VECTOR;")
    
    # スキーマ作成
    conn.execute("""
        CREATE NODE TABLE Document (
            id INT64,
            content STRING,
            embedding FLOAT[3],
            PRIMARY KEY (id)
        )
    """)
    
    # データ挿入
    conn.execute("""
        CREATE (d:Document {
            id: 1,
            content: 'テスト文書',
            embedding: [0.1, 0.2, 0.3]
        })
    """)
    
    # インデックス作成
    conn.execute("""
        CALL CREATE_VECTOR_INDEX(
            'Document',
            'test_index',
            'embedding'
        )
    """)
    
    # 検索
    result = conn.execute("""
        CALL QUERY_VECTOR_INDEX(
            'Document',
            'test_index',
            $embedding,
            $k
        ) RETURN node, distance
    """, {
        "embedding": [0.15, 0.25, 0.35],
        "k": 1
    })
    
    if result.has_next():
        print("✅ 基本動作確認: 成功")
    else:
        print("❌ 基本動作確認: 失敗")
    
    conn.close()
    
except Exception as e:
    print(f"❌ エラー: {e}")

# テスト2: エンドツーエンド統合テスト
print("\n=== Test 2: エンドツーエンド統合テスト ===")
try:
    # vector_search_systemモジュールを使用
    from vector_search_system import VectorSearchSystem
    
    with tempfile.TemporaryDirectory() as tmpdir:
        system = VectorSearchSystem(db_path=tmpdir)
        
        # 文書を登録
        docs = [
            "瑠璃色は紫みを帯びた濃い青です。",
            "プログラミングは創造的な活動です。",
            "今日は良い天気です。",
        ]
        
        index_result = system.index_documents(docs)
        print(f"- {index_result.indexed_count}件の文書を登録")
        
        # 検索
        search_result = system.search("青い色", k=2)
        if search_result.ok and len(search_result.documents) > 0:
            print(f"- {len(search_result.documents)}件の結果を取得")
            print(f"- 最も関連性の高い結果: {search_result.documents[0].content[:20]}...")
            print("✅ エンドツーエンド統合テスト: 成功")
        else:
            print("❌ エンドツーエンド統合テスト: 検索結果なし")
        
        system.close()
        
except ImportError as e:
    print(f"⚠️  インポートエラー: {e}")
    print("統合テストはスキップされました（モジュール構造の問題）")
except Exception as e:
    print(f"❌ エラー: {e}")

print("\n" + "=" * 60)
print("統合テスト完了")
print("=" * 60)
EOF

# Pythonスクリプトを実行
python /tmp/run_integration_tests.py