"""
要件バージョニング統合テスト（TDD Red）

要件の時系列管理を実現し、以下を保証する：
1. 要件の変更履歴が完全に追跡可能
2. 任意の時点の要件状態を復元可能
3. 変更理由と変更者が記録される
4. 現在の要件はLocationURI経由で一意にアクセス可能
"""
import pytest
from datetime import datetime, timezone, timedelta
import json
import sys
import io
import os
import tempfile
from pathlib import Path

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()


class TestVersioningIntegration:
    """バージョニング機能の統合テスト"""
    
    def setup_method(self):
        """各テストの前にスキーマを設定"""
        # スキーマを直接適用
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test.db")
        
        repo = create_kuzu_repository(str(self.test_db))
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
        
        success, results = schema_manager.apply_schema(str(schema_path))
        if not success:
            print("Schema setup failed:")
            for result in results:
                print(f"  {result}")
            raise RuntimeError("Failed to set up schema")
    
    def teardown_method(self):
        """各テストの後にクリーンアップ"""
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
    def test_要件作成時_自動的にバージョン1が作成される(self):
        """新規要件作成時にバージョン履歴が開始される"""
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
        
        # リポジトリとバージョニングサービスを作成
        repo = create_kuzu_repository(str(self.test_db))
        versioned_executor = create_versioned_cypher_executor(repo)
        
        # 新規要件を作成
        input_data = {
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'REQ-001',
                title: 'ユーザー認証機能',
                description: '安全なログイン機能を提供'
            })
            """
        }
        
        result = versioned_executor["execute"](input_data)
        
        # 結果を確認
        print(f"Result status: {result.get('status')}")
        print(f"Result data: {result.get('data')}")
        print(f"Result metadata: {result.get('metadata')}")
        
        if result.get('status') == 'error':
            print(f"Error: {result.get('error')}")
            print(f"Message: {result.get('message')}")
            assert False, f"Error: {result.get('message', result.get('error'))}"
        
        assert result.get('status') == 'success', "Expected success status"
        
        # 結果のメタデータを確認
        metadata = result.get("metadata", {})
        assert metadata.get("version") == 1, f"Expected version 1, got {metadata.get('version')}"
        assert "version_id" in metadata, "version_id not in metadata"
        assert "location_uri" in metadata, "location_uri not in metadata"
        
        # データ部分も確認
        data = result.get("data", [])
        assert data and len(data) > 0, "No data returned"
        # バージョニングされた結果の形式
        # [[entity_id, version_id, version, created_at]]
        assert len(data[0]) >= 3, f"Expected at least 3 fields, got {len(data[0])}"
        assert data[0][2] == 1, f"Expected version 1, got {data[0][2]}"  # version番号
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
    def test_要件更新時_新しいバージョンが作成される(self):
        """既存要件を更新すると新しいバージョンが作成される"""
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
        
        # リポジトリとバージョニングサービスを作成
        repo = create_kuzu_repository(str(self.test_db))
        versioned_executor = create_versioned_cypher_executor(repo)
        
        # 要件を更新
        input_data = {
            "type": "cypher",
            "query": """
            MATCH (r:RequirementEntity {id: 'REQ-001'})
            SET r.description = '二要素認証を含む安全なログイン機能'
            RETURN r
            """,
            "metadata": {
                "author": "security_team",
                "reason": "セキュリティ要件の強化"
            }
        }
        
        result = versioned_executor["execute"](input_data)
        
        # 結果を確認
        assert result.get('status') == 'success', f"Update failed: {result.get('message', result.get('error'))}"
        
        metadata = result.get("metadata", {})
        assert metadata.get("version") == 2, f"Expected version 2, got {metadata.get('version')}"
        assert result["previous_version"] == 1
        assert result["change_reason"] == "セキュリティ要件の強化"
        assert result["author"] == "security_team"
    
    @pytest.mark.skip(reason="Test refactoring needed for new interface")
    def test_要件履歴取得_全バージョンを時系列で取得(self):
        """要件の変更履歴を完全に取得できる"""
        from .main import main
        
        # 履歴を取得
        history_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (r:RequirementEntity {id: 'REQ-001'})
            RETURN r.history
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(history_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 履歴を確認
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        history = result_lines[0]["data"]["history"]
        assert len(history) >= 2
        assert history[0]["version"] == 1
        assert history[1]["version"] == 2
        assert history[1]["change_reason"] == "セキュリティ要件の強化"
    
    @pytest.mark.skip(reason="Test refactoring needed for new interface")
    def test_特定時点の要件復元_過去のバージョンを取得(self):
        """任意の時点の要件状態を復元できる"""
        from .main import main
        
        # 1時間前の状態を取得
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        restore_input = json.dumps({
            "type": "cypher",
            "query": f"""
            MATCH (r:RequirementEntity {{id: 'REQ-001'}})
            RETURN r.at_timestamp('{past_time.isoformat()}')
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(restore_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 過去の状態を確認
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        past_state = result_lines[0]["data"]
        assert past_state["version"] == 1
        assert past_state["description"] == "安全なログイン機能を提供"
    
    @pytest.mark.skip(reason="Test refactoring needed for new interface")
    def test_LocationURI経由アクセス_常に最新バージョンを返す(self):
        """LocationURI経由では常に最新バージョンが返される"""
        from .main import main
        
        # LocationURI経由でアクセス
        uri_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (l:LocationURI {id: 'req://REQ-001'})
            MATCH (l)-[:LOCATES {current: true}]->(r:RequirementEntity)
            RETURN r
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(uri_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 最新バージョンであることを確認
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        current = result_lines[0]["data"]
        assert current["version"] == 2
        assert current["description"] == "二要素認証を含む安全なログイン機能"
    
    @pytest.mark.skip(reason="Test refactoring needed for new interface")
    def test_バージョン間差分分析_変更内容を明確化(self):
        """バージョン間の具体的な変更内容を取得できる"""
        from .main import main
        
        # バージョン間の差分を取得
        diff_input = json.dumps({
            "type": "cypher",
            "query": """
            MATCH (r:RequirementEntity {id: 'REQ-001'})
            RETURN r.diff(1, 2)
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(diff_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 差分を確認
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        diff = result_lines[0]["data"]["diff"]
        assert diff["changed_fields"] == ["description"]
        assert diff["old_values"]["description"] == "安全なログイン機能を提供"
        assert diff["new_values"]["description"] == "二要素認証を含む安全なログイン機能"