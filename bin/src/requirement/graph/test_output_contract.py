#!/usr/bin/env python3
"""
requirement/graph出力の契約テスト（最小限設計）
parse_schema flakeを使用して1オブジェクトごとに検証

WARN: このテストは例外的にユーザーが許可したモックであり、規約非準拠である
理由: in-memoryデータベースのプロセス間共有が技術的に不可能なため、
      KuzuDBの環境変数のみをモックすることが承認された
"""
import json
import pytest
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any


class TestOutputContractWithParseSchema:
    """parse_schema flakeを使った出力契約テスト"""
    
    @pytest.fixture
    def schema_path(self):
        """出力スキーマファイルのパス"""
        return Path(__file__).parent / "output_schema.json"
    
    def validate_single_output_with_parse_schema(self, output_json: Dict[str, Any], schema_path: Path) -> bool:
        """1つのJSONオブジェクトをparse_schemaで検証"""
        # 一時ファイルに出力を保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(output_json, f)
            output_file = f.name
        
        try:
            # parse_schemaのtest-consumerを使用（単一JSONファイルの検証）
            result = subprocess.run([
                "nix", "run",
                "/home/nixos/bin/src/poc/parse_schema#test-consumer",
                "--",
                str(schema_path),
                output_file
            ], capture_output=True, text=True)
            
            return result.returncode == 0
        finally:
            os.unlink(output_file)
    
    def test_logger_wrapper_outputs(self, schema_path):
        """logger_wrapperの各関数の出力を1つずつ検証"""
        import io
        import sys
        from infrastructure.logger_wrapper import info, error, result, debug, warn
        
        test_cases = [
            # (関数, 引数, 説明)
            (info, ["test.module", "Info message"], "info関数の出力"),
            (debug, ["test.module", "Debug message"], "debug関数の出力"),
            (warn, ["test.module", "Warning message"], "warn関数の出力"),
            (error, ["Error message", {"code": 500}], "error関数の出力"),
            (result, [{"status": "success", "data": []}], "result関数の出力"),
        ]
        
        for func, args, description in test_cases:
            # 標準出力をキャプチャ
            captured = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = captured
            
            try:
                # 関数を実行
                func(*args)
                
                # 出力を取得
                sys.stdout = original_stdout
                captured.seek(0)
                output_line = captured.getvalue().strip()
                
                # JSONとしてパース
                output_json = json.loads(output_line)
                
                # parse_schemaで検証
                is_valid = self.validate_single_output_with_parse_schema(output_json, schema_path)
                assert is_valid, f"{description}がスキーマに準拠していません: {output_json}"
                
            finally:
                sys.stdout = original_stdout
    
    def test_main_error_output(self, schema_path):
        """mainモジュールのエラー出力を検証
        
        WARN: KuzuDBの環境変数のみモックを使用（ユーザー承認済み）
        """
        # 無効な操作でエラーを発生させる
        test_input = {"type": "invalid_operation"}
        
        # 環境変数を設定してサブプロセスで実行
        env = os.environ.copy()
        env["RGL_DATABASE_PATH"] = ":memory:"  # WARN: 承認されたモック
        
        result = subprocess.run(
            ["python", "-m", "requirement.graph"],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # 出力から各JSON行を検証
        output_lines = result.stdout.strip().split('\n')
        validated_count = 0
        
        for line in output_lines:
            if line.strip():
                try:
                    output_json = json.loads(line)
                    is_valid = self.validate_single_output_with_parse_schema(output_json, schema_path)
                    assert is_valid, f"出力がスキーマに準拠していません: {output_json}"
                    validated_count += 1
                except json.JSONDecodeError:
                    pass
        
        assert validated_count > 0, "有効なJSON出力がありません"
    
    def test_various_output_types(self, schema_path):
        """様々な出力タイプを個別に検証"""
        test_outputs = [
            {
                "message": "Test log message",
                "type": "log",
                "level": "INFO",
                "uri": "/rgl/test",
                "module": "test",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "message": "Operation completed",
                "type": "result",
                "data": {"status": "success"},
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "message": "An error occurred",
                "type": "error",
                "level": "ERROR",
                "uri": "/rgl/error",
                "module": "rgl.error",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        for i, output in enumerate(test_outputs):
            is_valid = self.validate_single_output_with_parse_schema(output, schema_path)
            assert is_valid, f"テスト出力{i+1}がスキーマに準拠していません: {output}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])