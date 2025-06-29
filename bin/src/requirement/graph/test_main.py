"""main.pyのテスト"""

import json
import sys
import io
import os
import subprocess
import tempfile
import pytest

# 環境変数をテスト用に設定
os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"
os.environ["RGL_DB_PATH"] = "/tmp/test_main.db"

from .main import main


class TestMain:
    """main関数のテスト"""
    
    def test_main_階層違反クエリ_エラーレスポンスとスコアマイナス1(self):
        """main_階層違反Cypherクエリ_適切なJSONエラーレスポンス"""
        # 標準入力をモック
        test_input = json.dumps({
            "type": "cypher",
            "query": """
            CREATE (task:RequirementEntity {
                id: 'test_task',
                title: 'タスク実装'
            }),
            (vision:RequirementEntity {
                id: 'test_vision',
                title: 'ビジョン'
            }),
            (task)-[:DEPENDS_ON]->(vision)
            """
        })
        
        # 標準出力をキャプチャ
        output = io.StringIO()
        
        # mainを実行（標準入出力を置き換え）
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        try:
            sys.stdin = io.StringIO(test_input)
            sys.stdout = output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # レスポンスを検証
        response = json.loads(output.getvalue())
        assert response["status"] == "error"
        assert response["score"] == -1.0
        assert "階層違反" in response["message"]
        assert "階層ルールに従ってください" in response["suggestion"]

    def test_main_正常クエリ_KuzuDB実行へ進む(self):
        """main_正常なCypherクエリ_階層検証を通過してDB実行へ"""
        test_input = json.dumps({
            "type": "cypher",
            "query": """
            CREATE (arch:RequirementEntity {
                id: 'test_arch',
                title: 'アーキテクチャ設計'
            }),
            (module:RequirementEntity {
                id: 'test_module',
                title: 'モジュール実装'
            }),
            (arch)-[:DEPENDS_ON]->(module)
            """
        })
        
        output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        try:
            sys.stdin = io.StringIO(test_input)
            sys.stdout = output
            # 環境変数が未設定の場合のエラーハンドリングも含む
            try:
                main()
            except EnvironmentError:
                # 環境変数未設定は想定内
                pass
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        
        # 階層違反エラーが出ていないことを確認
        output_str = output.getvalue()
        if output_str:
            response = json.loads(output_str)
            # 階層違反以外のエラー（環境変数など）は許容
            if response.get("message"):
                assert "階層違反" not in response["message"]

    def test_実DB統合_要件作成からクエリまで(self):
        """実DB統合_要件作成と取得_エンドツーエンドで動作確認"""
        # テスト用の一時DBディレクトリ
        with tempfile.TemporaryDirectory() as temp_db:
            # 環境変数設定
            env = os.environ.copy()
            env['RGL_DB_PATH'] = temp_db
            env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib'
            
            # 1. スキーマ初期化
            schema_cmd = [
                sys.executable, '-m', 
                'requirement.graph.infrastructure.apply_ddl_schema'
            ]
            result = subprocess.run(
                schema_cmd, 
                env=env, 
                capture_output=True, 
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            assert result.returncode == 0, f"Schema init failed: {result.stderr}"
            
            # 2. 要件を作成
            create_input = json.dumps({
                "type": "cypher",
                "query": """
                    CREATE (vision:RequirementEntity {
                        id: 'test_vision_db',
                        title: 'システムビジョン',
                        description: 'テスト用ビジョン',
                        priority: 2,
                        requirement_type: 'functional',
                        verification_required: true
                    })
                """
            })
            
            main_cmd = [sys.executable, '-m', 'requirement.graph.main']
            result = subprocess.run(
                main_cmd,
                input=create_input,
                env=env,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            assert result.returncode == 0, f"Create failed: {result.stderr}"
            
            create_response = json.loads(result.stdout)
            assert create_response["status"] == "success", f"Create failed: {create_response}"
            
            # 3. 作成した要件を取得
            query_input = json.dumps({
                "type": "cypher",
                "query": "MATCH (r:RequirementEntity {id: 'test_vision_db'}) RETURN r.title"
            })
            
            result = subprocess.run(
                main_cmd,
                input=query_input,
                env=env,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            assert result.returncode == 0, f"Query failed: {result.stderr}"
            
            query_response = json.loads(result.stdout)
            assert query_response["status"] == "success"
            assert query_response["data"][0][0] == "システムビジョン"

    def test_main_無効なJSON_エラーレスポンス(self):
        """main_無効なJSON入力_適切なエラーレスポンス"""
        test_input = "{ invalid json"
        
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
        
        response = json.loads(output.getvalue())
        assert response["status"] == "error"
        assert "score" not in response  # システムエラーにはスコアがない
        assert "Invalid JSON" in response["message"]
        assert "正しいJSON形式" in response["suggestion"]

    def test_main_空の入力_エラーレスポンス(self):
        """main_空の入力_適切なエラーレスポンス"""
        test_input = ""
        
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
        
        response = json.loads(output.getvalue())
        assert response["status"] == "error"
        assert "score" not in response  # システムエラーにはスコアがない
        assert "JSON" in response["message"]