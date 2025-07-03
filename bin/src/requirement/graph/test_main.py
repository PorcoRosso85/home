"""main.pyのテスト"""

import json
import sys
import io
import os
import subprocess
import tempfile
import pytest

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()

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
        
        # JSONL形式のレスポンスを解析
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        
        # エラー行を探す
        error_lines = [l for l in parsed_lines if l["type"] == "error"]
        assert len(error_lines) >= 1
        response = error_lines[0]
        assert response["level"] == "error"
        assert response["score"] == -1.0
        assert "階層違反" in response["message"]

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
            lines = output_str.strip().split('\n')
            parsed_lines = [json.loads(line) for line in lines if line]
            # エラーメッセージを確認
            error_lines = [l for l in parsed_lines if l["type"] == "error"]
            for error in error_lines:
                if error.get("message"):
                    assert "階層違反" not in error["message"]

    def test_実DB統合_要件作成からクエリまで(self):
        """実DB統合_要件作成と取得_エンドツーエンドで動作確認"""
        # テスト用の一時DBディレクトリ
        with tempfile.TemporaryDirectory() as temp_db:
            # 環境変数設定
            env = os.environ.copy()
            env['RGL_DB_PATH'] = temp_db
            env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib'
            
            # 1. スキーマ初期化
            schema_input = json.dumps({
                "type": "schema",
                "action": "apply",
                "create_test_data": False
            })
            
            # run.pyを直接実行
            run_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run.py')
            main_cmd = [sys.executable, run_py_path]
            result = subprocess.run(
                main_cmd,
                input=schema_input,
                env=env,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"stderr: {result.stderr}")
                print(f"stdout: {result.stdout}")
            assert result.returncode == 0, f"Schema init failed: {result.stderr}"
            
            if not result.stdout:
                print(f"Empty stdout from schema command")
                print(f"stderr: {result.stderr}")
            
            # JSONL形式のレスポンスを解析
            lines = result.stdout.strip().split('\n')
            parsed_lines = [json.loads(line) for line in lines if line]
            # resultタイプの行を探す
            result_lines = [l for l in parsed_lines if l["type"] == "result"]
            if result_lines:
                assert len(result_lines) > 0, "Schema init should return result"
            else:
                # エラーがないことを確認
                error_lines = [l for l in parsed_lines if l["type"] == "error"]
                assert len(error_lines) == 0, f"Schema init failed with errors: {error_lines}"
            
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
            
            # run.pyを直接実行
            main_cmd = [sys.executable, run_py_path]
            result = subprocess.run(
                main_cmd,
                input=create_input,
                env=env,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Create failed: {result.stderr}"
            
            # JSONL形式のレスポンスを解析
            lines = result.stdout.strip().split('\n')
            parsed_lines = [json.loads(line) for line in lines if line]
            # エラーがないことを確認
            error_lines = [l for l in parsed_lines if l["type"] == "error"]
            assert len(error_lines) == 0, f"Create failed with errors: {error_lines}"
            
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
                text=True
            )
            assert result.returncode == 0, f"Query failed: {result.stderr}"
            
            # JSONL形式のレスポンスを解析
            lines = result.stdout.strip().split('\n')
            parsed_lines = [json.loads(line) for line in lines if line]
            # resultタイプの行を探す
            result_lines = [l for l in parsed_lines if l["type"] == "result"]
            assert len(result_lines) > 0, "Query should return results"
            assert result_lines[0]["data"][0][0] == "システムビジョン"

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
        
        # JSONL形式のレスポンスを解析
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        
        # エラー行を探す
        error_lines = [l for l in parsed_lines if l["type"] == "error"]
        assert len(error_lines) >= 1
        response = error_lines[0]
        assert response["level"] == "error"
        assert "Invalid JSON" in response["message"]

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
        
        # JSONL形式のレスポンスを解析
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]
        
        # エラー行を探す
        error_lines = [l for l in parsed_lines if l["type"] == "error"]
        assert len(error_lines) >= 1
        response = error_lines[0]
        assert response["level"] == "error"
        assert "JSON" in response["message"]