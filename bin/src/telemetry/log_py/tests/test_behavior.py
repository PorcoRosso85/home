#!/usr/bin/env python3
"""
全言語共通ログAPI仕様の振る舞いテスト

各言語実装を外部プロセスとして実行し、標準出力を検証する。
「壁の向こう側」原則に従い、実装の詳細には一切触れない。
"""
import subprocess
import json
import pytest
from pathlib import Path
import tempfile
import os


class TestLogAPISpecification:
    """log(level, data) → stdout の契約を検証"""
    
    @pytest.fixture
    def implementations(self):
        """テスト可能な言語実装のリスト"""
        impls = []
        
        # Python実装
        impls.append({
            "name": "python",
            "available": True,
            "run": self.run_python
        })
        
        # TypeScript実装
        deno_available = subprocess.run(
            ["which", "deno"],
            capture_output=True
        ).returncode == 0
        
        impls.append({
            "name": "typescript",
            "available": deno_available,
            "run": self.run_typescript
        })
        
        # 将来の実装用プレースホルダー
        # impls.append({
        #     "name": "go",
        #     "available": False,
        #     "run": self.run_go
        # })
        
        return impls
    
    def run_python(self, level: str, data: dict) -> tuple[str, int]:
        """Python実装を実行"""
        script = f"""
import sys
from log_py import log
log("{level}", {data})
"""
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        return result.stdout, result.returncode
    
    def run_typescript(self, level: str, data: dict) -> tuple[str, int]:
        """TypeScript実装を実行"""
        script = f"""
import {{ log }} from './mod.ts';
log("{level}", {json.dumps(data)});
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.ts',
            dir=Path(__file__).parent,
            delete=False
        ) as f:
            f.write(script)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ["deno", "run", "--allow-read", temp_file],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            return result.stdout, result.returncode
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.parametrize("level", ["INFO", "ERROR", "DEBUG", "WARN", "METRIC", "CUSTOM"])
    def test_arbitrary_log_levels(self, implementations, level):
        """仕様: 任意のログレベル文字列を使用可能"""
        data = {"uri": "/test", "message": "test message"}
        
        for impl in implementations:
            if not impl["available"]:
                pytest.skip(f"{impl['name']} not available")
                continue
                
            stdout, returncode = impl["run"](level, data)
            
            assert returncode == 0, f"{impl['name']} failed for level {level}"
            output = json.loads(stdout.strip())
            assert output["level"] == level, f"{impl['name']}: level mismatch"
    
    def test_required_fields(self, implementations):
        """仕様: uri と message は必須フィールド"""
        data = {
            "uri": "/api/endpoint",
            "message": "Required fields test"
        }
        
        for impl in implementations:
            if not impl["available"]:
                continue
                
            stdout, returncode = impl["run"]("INFO", data)
            
            assert returncode == 0, f"{impl['name']} failed"
            output = json.loads(stdout.strip())
            assert "uri" in output, f"{impl['name']}: missing uri"
            assert "message" in output, f"{impl['name']}: missing message"
            assert output["uri"] == data["uri"]
            assert output["message"] == data["message"]
    
    def test_field_extension(self, implementations):
        """仕様: 追加フィールドを自由に拡張可能"""
        data = {
            "uri": "/api/users",
            "message": "User created",
            "user_id": "123",
            "request_id": "req-456",
            "timestamp": "2024-01-01T00:00:00Z",
            "metadata": {
                "ip": "192.168.1.1",
                "user_agent": "test/1.0"
            }
        }
        
        for impl in implementations:
            if not impl["available"]:
                continue
                
            stdout, returncode = impl["run"]("INFO", data)
            
            assert returncode == 0, f"{impl['name']} failed"
            output = json.loads(stdout.strip())
            
            # すべてのフィールドが保持されている
            for key, value in data.items():
                assert key in output, f"{impl['name']}: missing {key}"
                assert output[key] == value, f"{impl['name']}: {key} value mismatch"
    
    def test_jsonl_format(self, implementations):
        """仕様: 出力は1行のJSON（JSONL形式）"""
        data = {
            "uri": "/test",
            "message": "Multi\nline\nmessage",
            "description": "Line 1\nLine 2\nLine 3"
        }
        
        for impl in implementations:
            if not impl["available"]:
                continue
                
            stdout, returncode = impl["run"]("INFO", data)
            
            assert returncode == 0, f"{impl['name']} failed"
            
            # 出力は正確に1行
            lines = stdout.strip().split('\n')
            assert len(lines) == 1, f"{impl['name']}: output is not single line"
            
            # 有効なJSONとして解析可能
            output = json.loads(lines[0])
            assert output["message"] == data["message"]
            assert output["description"] == data["description"]
    
    def test_level_data_merge(self, implementations):
        """仕様: level と data の内容がマージされて出力"""
        test_cases = [
            ("INFO", {"uri": "/", "message": "test"}),
            ("ERROR", {"uri": "/api", "message": "error", "code": 500}),
            ("METRIC", {"uri": "/metrics", "message": "latency", "value": 123.45})
        ]
        
        for impl in implementations:
            if not impl["available"]:
                continue
                
            for level, data in test_cases:
                stdout, returncode = impl["run"](level, data)
                
                assert returncode == 0, f"{impl['name']} failed"
                output = json.loads(stdout.strip())
                
                # levelが含まれている
                assert "level" in output
                assert output["level"] == level
                
                # dataのすべてのキーが含まれている
                for key, value in data.items():
                    assert key in output
                    assert output[key] == value
    
    def test_cross_language_compatibility(self, implementations):
        """仕様: 全言語で同一の入出力"""
        test_cases = [
            {
                "level": "INFO",
                "data": {"uri": "/api/health", "message": "Health check"}
            },
            {
                "level": "ERROR", 
                "data": {
                    "uri": "/api/users/123",
                    "message": "User not found",
                    "error_code": "USER_NOT_FOUND",
                    "user_id": "123"
                }
            },
            {
                "level": "METRIC",
                "data": {
                    "uri": "/api/search",
                    "message": "Search performed",
                    "query": "test query",
                    "results_count": 42,
                    "latency_ms": 125.5,
                    "cached": False,
                    "tags": ["search", "api", "v2"]
                }
            }
        ]
        
        available_impls = [impl for impl in implementations if impl["available"]]
        
        if len(available_impls) < 2:
            pytest.skip("Need at least 2 implementations for compatibility test")
        
        for test_case in test_cases:
            level = test_case["level"]
            data = test_case["data"]
            
            outputs = []
            for impl in available_impls:
                stdout, returncode = impl["run"](level, data)
                assert returncode == 0, f"{impl['name']} failed"
                
                output = json.loads(stdout.strip())
                outputs.append((impl["name"], output))
            
            # すべての実装で出力が同一
            first_name, first_output = outputs[0]
            for name, output in outputs[1:]:
                assert output == first_output, \
                    f"Output mismatch between {first_name} and {name}:\n" \
                    f"{first_name}: {json.dumps(first_output, sort_keys=True)}\n" \
                    f"{name}: {json.dumps(output, sort_keys=True)}"
    
    def test_to_jsonl_function(self, implementations):
        """仕様: to_jsonl関数は辞書をJSON文字列に変換"""
        # Python実装のみテスト（他言語も同様の関数を提供すべき）
        script = """
import sys
from log_py import to_jsonl

# 各種データ型のテスト
test_data = {
    "string": "value",
    "number": 42,
    "float": 3.14,
    "bool": True,
    "null": None,
    "list": [1, 2, 3],
    "nested": {"inner": "value"}
}

result = to_jsonl(test_data)
print(result)
"""
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        assert result.returncode == 0
        output = result.stdout.strip()
        
        # 改行なし
        assert '\n' not in output
        
        # 有効なJSON
        parsed = json.loads(output)
        assert parsed["string"] == "value"
        assert parsed["number"] == 42
        assert parsed["float"] == 3.14
        assert parsed["bool"] is True
        assert parsed["null"] is None
        assert parsed["list"] == [1, 2, 3]
        assert parsed["nested"]["inner"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])