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
    
    def run_requirement_graph(self, input_data):
        """requirement/graphを実行して出力を取得"""
        result = subprocess.run(
            ["python", "-m", "requirement.graph"],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent  # requirement/まで戻る
        )
        
        # 最後の有効なJSON行を取得
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        
        return {"error": "No valid JSON output", "stderr": result.stderr}
    
    def test_with_parse_schema(self, schema_path, parse_schema_path, operation, expected_fields):
        """parse_schemaを使って出力を検証するヘルパー"""
        # 一時スクリプトを作成してrequirement/graphを実行
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(f"""#!/bin/bash
echo '{json.dumps(operation)}' | python -m requirement.graph
""")
            script_path = f.name
        
        os.chmod(script_path, 0o755)
        
        try:
            # parse_schemaのtest-producerで検証
            result = subprocess.run([
                "nix", "run", 
                f"{parse_schema_path}#test-producer",
                "--",
                str(schema_path),
                script_path
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            # 検証結果をチェック
            assert result.returncode == 0, f"Schema validation failed: {result.stderr}"
            assert "✅ Producer output is valid" in result.stdout
            
            # 期待されるフィールドの存在も確認（オプション）
            if expected_fields:
                output = self.run_requirement_graph(operation)
                for field in expected_fields:
                    assert field in output, f"Expected field '{field}' not found"
                    
        finally:
            os.unlink(script_path)
    
    def test_list_requirements_output_schema(self, schema_path, parse_schema_path):
        """list_requirements操作の出力がスキーマに準拠する"""
        operation = {
            "type": "template",
            "template": "list_requirements",
            "parameters": {"limit": 5}
        }
        
        self.test_with_parse_schema(
            schema_path, 
            parse_schema_path,
            operation,
            expected_fields=["message", "type", "data"]
        )
    
    def test_error_output_has_error_level(self, schema_path, parse_schema_path):
        """エラー出力はERRORレベルを持つ"""
        operation = {"type": "invalid_operation"}
        
        # エラー出力もスキーマに準拠することを確認
        self.test_with_parse_schema(
            schema_path, 
            parse_schema_path,
            operation,
            expected_fields=["message", "type", "level"]
        )
        
        # エラー固有の検証
        output = self.run_requirement_graph(operation)
        assert output.get("type") == "error"
        assert output.get("level") == "ERROR"
    
    def test_output_has_log_compatible_fields(self, schema_path, parse_schema_path):
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
            expected_fields=["message"]
        )
        
        # log互換フィールドの詳細検証
        output = self.run_requirement_graph(operation)
        
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
    
    def test_all_operations_comply_with_schema(self, schema_path, parse_schema_path):
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
                    expected_fields=None  # 個別検証は不要
                )
            except AssertionError as e:
                pytest.fail(f"Operation {op} produced invalid output: {e}")


if __name__ == "__main__":
    # pytestで実行
    pytest.main([__file__, "-v"])