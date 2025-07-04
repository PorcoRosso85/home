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

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()


class TestVersioningIntegration:
    """バージョニング機能の統合テスト"""
    
    def setup_method(self):
        """各テストの前にスキーマを設定"""
        # スキーマ作成を実行
        schema_input = json.dumps({
            "type": "schema",
            "action": "apply"
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(schema_input)
            sys.stdout = output
            from .main import main
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # スキーマ作成結果を確認
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        
        # "message": "Schema applied successfully" を探す
        success = False
        for line in parsed_lines:
            if line.get("type") == "result" and line.get("data", {}).get("message") == "Schema applied successfully":
                success = True
                break
        
        if not success:
            print("Schema setup output:")
            for line in parsed_lines:
                print(f"  {line}")
            # エラーメッセージを詳しく見る
            error_lines = [l for l in parsed_lines if l.get("type") == "error"]
            if error_lines:
                print("\nErrors found:")
                for err in error_lines:
                    print(f"  {err}")
            raise RuntimeError("Failed to set up schema")
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
    def test_要件作成時_自動的にバージョン1が作成される(self):
        """新規要件作成時にバージョン履歴が開始される"""
        from .main import main
        
        # 新規要件を作成
        test_input = json.dumps({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'REQ-001',
                title: 'ユーザー認証機能',
                description: '安全なログイン機能を提供'
            })
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(test_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # JSONL出力を解析
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        
        # デバッグ用出力
        print(f"Total lines: {len(parsed_lines)}")
        for line in parsed_lines:
            print(f"Type: {line['type']}, Level: {line.get('level', 'N/A')}")
            if line['type'] == 'result':
                print(f"Data: {line.get('data')}")
                print(f"Metadata: {line.get('metadata')}")
            elif line['type'] == 'error':
                print(f"Message: {line.get('message')}")
                print(f"Details: {line.get('details')}")
            elif line['type'] == 'log':
                print(f"Log: {line.get('message')}")
        
        # 結果を確認
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        error_lines = [l for l in parsed_lines if l["type"] == "error"]
        
        if error_lines:
            print("\nERRORS FOUND:")
            for err in error_lines:
                print(f"- {err.get('message')}")
            assert False, "Errors found during execution"
        
        assert len(result_lines) == 1, f"Expected 1 result, got {len(result_lines)}"
        
        # 結果のメタデータを確認
        result_line = result_lines[0]
        metadata = result_line.get("metadata", {})
        assert metadata.get("version") == 1, f"Expected version 1, got {metadata.get('version')}"
        assert "version_id" in metadata, "version_id not in metadata"
        assert "location_uri" in metadata, "location_uri not in metadata"
        
        # データ部分も確認
        data = result_line.get("data", [])
        assert data and len(data) > 0, "No data returned"
        # バージョニングされた結果の形式
        # [[entity_id, version_id, version, created_at]]
        assert len(data[0]) >= 3, f"Expected at least 3 fields, got {len(data[0])}"
        assert data[0][2] == 1, f"Expected version 1, got {data[0][2]}"  # version番号
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
    def test_要件更新時_新しいバージョンが作成される(self):
        """既存要件を更新すると新しいバージョンが作成される"""
        from .main import main
        
        # 要件を更新
        update_input = json.dumps({
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
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(update_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 結果を確認
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        
        result = result_lines[0]["data"]
        assert result["version"] == 2
        assert result["previous_version"] == 1
        assert result["change_reason"] == "セキュリティ要件の強化"
        assert result["author"] == "security_team"
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
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
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
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
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
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
    
    #@pytest.mark.skip(reason="TDD Red: バージョニング統合待ち")
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