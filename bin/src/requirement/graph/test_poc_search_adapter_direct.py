"""POC Search Adapter直接テスト"""
import tempfile
import os
import sys

# POC searchパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from requirement.graph.application.poc_search_adapter import POCSearchAdapter
from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema


def test_poc_search_adapter_direct():
    """POC searchアダプターが正しく動作するか確認"""
    with tempfile.TemporaryDirectory() as db_dir:
        # スキーマを適用
        apply_ddl_schema(db_dir, create_test_data=False)

        # リポジトリを作成
        repository = create_kuzu_repository(db_dir)

        # POC searchアダプターを作成
        try:
            adapter = POCSearchAdapter(db_dir)
            print("✓ POC search adapter created successfully")
        except Exception as e:
            print(f"✗ Failed to create POC search adapter: {e}")
            return

        # 最初の要件を追加
        query = """
        CREATE (r:RequirementEntity {
            id: 'test_001',
            title: 'ユーザー認証システム',
            description: 'ログイン機能の実装',
            status: 'proposed',
            embedding: NULL
        })
        RETURN r
        """
        result = repository["execute"](query, {})
        print(f"✓ First requirement created: {result.get('status')}")

        # POC searchインデックスに追加
        added = adapter.add_to_index({
            "id": "test_001",
            "title": "ユーザー認証システム",
            "description": "ログイン機能の実装"
        })
        print(f"✓ Added to index: {added}")

        # 重複チェック
        duplicates = adapter.check_duplicates("認証システム ユーザーログイン機能", k=5, threshold=0.3)
        print(f"✓ Duplicates found: {len(duplicates)}")
        for dup in duplicates:
            print(f"  - {dup['id']}: {dup['title']} (score: {dup['score']:.3f})")


if __name__ == "__main__":
    test_poc_search_adapter_direct()
