#!/usr/bin/env python3
"""
requirement/graph出力の契約テスト（parse_schema使用）
TDD Red Phase: 最初は失敗するテストを書く
"""
import subprocess
import json
import pytest
import tempfile
import os
from pathlib import Path
import time


class TestRequirementGraphOutputContract:
    """requirement/graphの出力がlog互換スキーマに準拠することを検証"""
    
    @pytest.fixture
    def schema_path(self):
        """出力スキーマファイルのパス"""
        return Path(__file__).parent / "output_schema.json"
    
    @pytest.fixture 
    def parse_schema_path(self):
        """parse_schemaのパス"""
        return Path(__file__).parent.parent.parent / "poc" / "parse_schema"
    
    @pytest.fixture
    def temp_db(self):
        """テスト用の一時データベース"""
        # インメモリデータベースを使用
        yield None  # インメモリの場合はNone
    
    def run_requirement_graph(self, input_data, db_path=None):
        """requirement/graphを実行して出力を取得"""
        import sys
        env = {**os.environ, "LOG_LEVEL": "*:ERROR"}  # ログレベルを上げて余計な出力を抑制
        if db_path:
            env["RGL_DATABASE_PATH"] = db_path
        else:
            # インメモリデータベースを使用
            env["RGL_DATABASE_PATH"] = ":memory:"
            
        result = subprocess.run(
            [sys.executable, "-m", "requirement.graph"],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,  # requirement/まで戻る
            env=env
        )
        
        # エラーチェック
        if result.returncode != 0:
            return {"error": "Process failed", "stderr": result.stderr}
        
        # 最後の有効なJSON行を取得
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        
        return {"error": "No valid JSON output", "stderr": result.stderr}
    
    def test_with_parse_schema(self, schema_path, parse_schema_path, operation, expected_fields, db_path=None):
        """parse_schemaを使って出力を検証するヘルパー"""
        # requirement/graphを直接実行して出力を取得
        output = self.run_requirement_graph(operation, db_path=db_path)
        
        # 一時ファイルにJSON出力を保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(output, f)
            output_file = f.name
        
        try:
            # parse_schemaのtest-consumerで検証（出力JSONを直接検証）
            result = subprocess.run([
                "nix", "run", 
                f"{parse_schema_path}#test-consumer",
                "--",
                str(schema_path),
                output_file
            ], capture_output=True, text=True)
            
            # 検証結果をチェック
            if result.returncode != 0:
                # エラー詳細を出力
                print(f"Schema validation failed for operation: {operation}")
                print(f"Output: {json.dumps(output, indent=2)}")
                print(f"Error: {result.stderr}")
            
            assert result.returncode == 0, f"Schema validation failed: {result.stderr}"
            
            # 期待されるフィールドの存在も確認（オプション）
            if expected_fields:
                for field in expected_fields:
                    assert field in output, f"Expected field '{field}' not found"
                    
        finally:
            os.unlink(output_file)
    
    def test_list_requirements_output_schema(self, schema_path, parse_schema_path, temp_db):
        """list_requirements操作の出力がスキーマに準拠する"""
        # まずスキーマを初期化
        schema_result = self.run_requirement_graph(
            {"type": "schema", "action": "apply"},
            db_path=temp_db
        )
        
        # スキーマ初期化の結果を確認
        if schema_result.get("type") == "error":
            pytest.skip(f"Schema initialization failed: {schema_result.get('message')}")
        
        time.sleep(0.1)  # スキーマ初期化待ち
        
        operation = {
            "type": "template",
            "template": "list_requirements",
            "parameters": {"limit": 5}
        }
        
        self.test_with_parse_schema(
            schema_path, 
            parse_schema_path,
            operation,
            expected_fields=["message", "type", "data"],
            db_path=temp_db
        )
    
    def test_error_output_has_error_level(self, schema_path, parse_schema_path, temp_db):
        """エラー出力はERRORレベルを持つ"""
        operation = {"type": "invalid_operation"}
        
        # エラー出力もスキーマに準拠することを確認
        self.test_with_parse_schema(
            schema_path, 
            parse_schema_path,
            operation,
            expected_fields=["message", "type", "level"],
            db_path=temp_db
        )
        
        # エラー固有の検証
        output = self.run_requirement_graph(operation, db_path=temp_db)
        assert output.get("type") == "error"
        assert output.get("level") == "ERROR"
    
    def test_output_has_log_compatible_fields(self, schema_path, parse_schema_path, temp_db):
        """出力はlog互換のフィールドを持つ"""
        operation = {
            "type": "template",
            "template": "find_requirement",
            "parameters": {"id": "test_001"}
        }
        
        self.test_with_parse_schema(
            schema_path,
            parse_schema_path,
            operation,
            expected_fields=["message"],
            db_path=temp_db
        )
        
        # log互換フィールドの詳細検証
        output = self.run_requirement_graph(operation, db_path=temp_db)
        
        # Optional but recommended fields
        if "timestamp" in output:
            # ISO 8601形式であること
            from datetime import datetime
            datetime.fromisoformat(output["timestamp"].replace('Z', '+00:00'))
        
        if "_loc" in output:
            # file:line形式であること
            assert ":" in output["_loc"]
            parts = output["_loc"].split(":")
            assert len(parts) >= 2
            assert parts[-1].isdigit()
    
    def test_all_operations_comply_with_schema(self, schema_path, parse_schema_path, temp_db):
        """すべての操作タイプが統一スキーマに準拠"""
        operations = [
            {"type": "template", "template": "list_requirements"},
            {"type": "template", "template": "create_requirement", 
             "parameters": {"id": "req_001", "title": "Test"}},
            {"type": "template", "template": "find_dependencies",
             "parameters": {"requirement_id": "req_001", "depth": 2}},
            {"type": "schema", "action": "apply"},
            {"type": "invalid"}  # エラーケース
        ]
        
        for op in operations:
            # 各操作をparse_schemaで検証
            try:
                self.test_with_parse_schema(
                    schema_path,
                    parse_schema_path,
                    op,
                    expected_fields=None,  # 個別検証は不要
                    db_path=temp_db
                )
            except AssertionError as e:
                pytest.fail(f"Operation {op} produced invalid output: {e}")


if __name__ == "__main__":
    # pytestで実行
    pytest.main([__file__, "-v"])