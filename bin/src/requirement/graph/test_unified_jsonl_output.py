"""
統一JSONL出力フォーマットのテスト（TDD Red）

すべての出力をJSONL形式に統一：
- type: log, result, error, score
- level: trace, debug, info, warn, error 
- timestamp: ISO8601形式
- module: 出力元モジュール（ログの場合）
- message: メッセージ
- data: データ（結果の場合）
"""
import json
import sys
import io
import os
from datetime import datetime
import pytest

from .main import main


class TestUnifiedJSONLOutput:
    """統一JSONL出力フォーマットのテスト"""
    
    def test_正常なクエリ実行_JSONL形式で出力(self):
        """正常なクエリ実行時、ログと結果がJSONL形式で出力される"""
        # 環境変数を一時的に設定
        original_log_level = os.environ.get('RGL_LOG_LEVEL')
        os.environ['RGL_LOG_LEVEL'] = 'info'  # infoレベルに設定
        
        try:
            test_input = json.dumps({
                "type": "cypher",
                "query": "RETURN 1 as value"
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
        finally:
            # 環境変数を元に戻す
            if original_log_level is None:
                os.environ.pop('RGL_LOG_LEVEL', None)
            else:
                os.environ['RGL_LOG_LEVEL'] = original_log_level
        
        # 出力を行ごとに解析
        lines = output.getvalue().strip().split('\n')
        
        # デバッグ用: 実際の出力を表示
        if len(lines) < 2:
            print(f"Output lines: {lines}")
        
        assert len(lines) >= 1  # 最低でも結果（ログレベル設定によってはログがない場合がある）
        
        # 各行がJSON形式であることを確認
        parsed_lines = []
        for line in lines:
            if line:  # 空行をスキップ
                parsed = json.loads(line)
                parsed_lines.append(parsed)
                
                # 共通フィールドの確認
                assert "type" in parsed
                assert "timestamp" in parsed
                assert parsed["type"] in ["log", "result", "error", "score"]
                
                # タイムスタンプがISO8601形式
                datetime.fromisoformat(parsed["timestamp"].replace('Z', '+00:00'))
        
        # 結果行の確認
        result_lines = [l for l in parsed_lines if l["type"] == "result"]
        assert len(result_lines) == 1
        result = result_lines[0]
        assert "data" in result
        assert result["level"] == "info"
    
    def test_エラー発生時_JSONL形式でエラー出力(self):
        """エラー発生時もJSONL形式で出力される"""
        test_input = json.dumps({
            "type": "cypher",
            "query": "INVALID CYPHER QUERY"
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
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines]
        
        # エラー行の確認
        error_lines = [l for l in parsed_lines if l["type"] == "error"]
        assert len(error_lines) >= 1
        error = error_lines[0]
        assert error["level"] == "error"
        assert "message" in error
    
    def test_デバッグログ_環境変数で制御(self):
        """デバッグログが環境変数で制御される"""
        import os
        original_env = os.environ.get('RGL_LOG_LEVEL')
        
        try:
            # デバッグレベルを設定
            os.environ['RGL_LOG_LEVEL'] = 'debug'
            
            # loggerモジュールをリロード（環境変数の変更を反映するため）
            import importlib
            from .infrastructure import logger
            importlib.reload(logger)
            
            test_input = json.dumps({
                "type": "cypher",
                "query": "RETURN 1"
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
            
            lines = output.getvalue().strip().split('\n')
            parsed_lines = [json.loads(line) for line in lines]
            
            # ログの内容を確認（デバッグ用）
            print(f"Total lines: {len(parsed_lines)}")
            for line in parsed_lines:
                print(f"Type: {line['type']}, Level: {line.get('level', 'N/A')}, Message: {line.get('message', 'N/A')}")
            
            # すべてのログを確認
            all_logs = [l for l in parsed_lines if l["type"] == "log"]
            print(f"Total logs: {len(all_logs)}")
            
            # デバッグログが含まれることを確認
            debug_logs = [l for l in parsed_lines if l["type"] == "log" and l["level"] == "debug"]
            assert len(debug_logs) > 0, f"No debug logs found. All logs: {all_logs}"
            
            # ログに必須フィールドがあることを確認
            for log in debug_logs:
                assert "module" in log
                assert "message" in log
                assert "timestamp" in log
        finally:
            if original_env is None:
                os.environ.pop('RGL_LOG_LEVEL', None)
            else:
                os.environ['RGL_LOG_LEVEL'] = original_env
            
            # loggerモジュールを再度リロード（元の設定に戻すため）
            import importlib
            from .infrastructure import logger
            importlib.reload(logger)
    
    def test_摩擦検出結果_スコアタイプで出力(self):
        """摩擦検出結果がscoreタイプで出力される"""
        test_input = json.dumps({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'test_ambiguous',
                title: '使いやすいUI',
                description: '直感的で使いやすい'
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
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines]
        
        # スコア行の確認
        score_lines = [l for l in parsed_lines if l["type"] == "score"]
        if score_lines:  # CREATE操作なので摩擦検出が実行される
            score = score_lines[0]
            assert "level" in score
            assert "data" in score
            # dataには摩擦分析の結果が直接含まれる
            assert "frictions" in score["data"]
            assert "total" in score["data"]
    
    def test_stderrは使用しない(self):
        """stderrには何も出力されない"""
        test_input = json.dumps({
            "type": "cypher",
            "query": "RETURN 1"
        })
        
        output = io.StringIO()
        error_output = io.StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            sys.stdin = io.StringIO(test_input)
            sys.stdout = output
            sys.stderr = error_output
            main()
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        
        # stderrには何も出力されないことを確認
        assert error_output.getvalue() == ""
        
        # stdoutには出力があることを確認
        assert output.getvalue() != ""
    
    def test_階層違反エラー_JSONL形式(self):
        """階層違反エラーもJSONL形式で出力される"""
        test_input = json.dumps({
            "type": "cypher",
            "query": """
            CREATE (task:RequirementEntity {id: 'task', title: 'タスク実装'}),
                   (vision:RequirementEntity {id: 'vision', title: 'ビジョン'}),
                   (task)-[:DEPENDS_ON]->(vision)
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
        
        lines = output.getvalue().strip().split('\n')
        parsed_lines = [json.loads(line) for line in lines if line]  # 空行をスキップ
        
        # デバッグ用: 実際の出力を表示
        print(f"\nTotal lines: {len(parsed_lines)}")
        for line in parsed_lines:
            print(f"Type: {line['type']}, Level: {line.get('level', 'N/A')}, Message: {line.get('message', 'N/A')}")
        
        # エラー行の確認
        error_lines = [l for l in parsed_lines if l["type"] == "error"]
        assert len(error_lines) >= 1, f"No error lines found. All types: {[l['type'] for l in parsed_lines]}"
        error = error_lines[0]
        assert error["level"] == "error"
        assert "score" in error
        assert error["score"] == -1.0