#!/usr/bin/env python3
"""
全言語共通ログ実装の振る舞いテスト

「壁の向こう側」原則に従い、各言語実装を外部プロセスとして実行し、
その標準出力を検証する統合テスト。
"""
import subprocess
import json
import pytest
from pathlib import Path


class TestLogBehavior:
    """全言語実装の共通振る舞いを検証"""
    
    @pytest.fixture
    def test_data(self):
        """テスト用の共通データ"""
        return {
            "uri": "/api/test",
            "message": "Test message",
            "extra": "data"
        }
    
    def run_command(self, cmd: list[str], env=None) -> tuple[str, str, int]:
        """コマンドを実行して出力を取得"""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )
        return result.stdout, result.stderr, result.returncode
    
    @pytest.mark.parametrize("lang,cmd_template", [
        ("python", ["python3", "-c", "from __init__ import log; log({level}, {data})"]),
        ("typescript", ["deno", "eval", "import {{log}} from './mod.ts'; log({level}, {data})"]),
    ])
    def test_log_outputs_jsonl(self, lang, cmd_template, test_data):
        """各言語実装がJSONL形式で出力することを検証"""
        # コマンド構築
        level = '"INFO"'
        data_str = json.dumps(test_data)
        cmd = [
            part.format(level=level, data=data_str) if "{" in part else part
            for part in cmd_template
        ]
        
        # 実行
        stdout, stderr, returncode = self.run_command(cmd)
        
        # 検証
        assert returncode == 0, f"{lang} failed: {stderr}"
        assert stdout.strip(), f"{lang} produced no output"
        
        # JSONL形式の検証
        output = json.loads(stdout.strip())
        assert output["level"] == "INFO"
        assert output["uri"] == test_data["uri"]
        assert output["message"] == test_data["message"]
        assert output["extra"] == test_data["extra"]
    
    def test_python_log_behavior(self, test_data):
        """Python実装の振る舞い検証"""
        script = f"""
import sys
sys.path.insert(0, '.')
from __init__ import log
log("ERROR", {test_data})
"""
        stdout, stderr, returncode = self.run_command(["python3", "-c", script])
        
        assert returncode == 0
        output = json.loads(stdout.strip())
        assert output["level"] == "ERROR"
        assert all(output[k] == test_data[k] for k in test_data)
    
    def test_typescript_log_behavior(self, test_data):
        """TypeScript実装の振る舞い検証"""
        script = f"""
import {{ log }} from './mod.ts';
log("WARN", {json.dumps(test_data)});
"""
        # 一時ファイルに書き込んで実行
        test_file = Path("test_temp.ts")
        test_file.write_text(script)
        
        try:
            stdout, stderr, returncode = self.run_command(["deno", "run", str(test_file)])
            
            assert returncode == 0, f"TypeScript failed: {stderr}"
            output = json.loads(stdout.strip())
            assert output["level"] == "WARN"
            assert all(output[k] == test_data[k] for k in test_data)
        finally:
            test_file.unlink(missing_ok=True)
    
    @pytest.mark.parametrize("level", ["INFO", "ERROR", "DEBUG", "METRIC", "CUSTOM"])
    def test_arbitrary_log_levels(self, level):
        """任意のログレベルが使用可能"""
        # Python実装でテスト
        script = f"""
import sys
sys.path.insert(0, '.')
from __init__ import log
log("{level}", {{"uri": "/test", "message": "test"}})
"""
        stdout, _, returncode = self.run_command(["python3", "-c", script])
        
        assert returncode == 0
        output = json.loads(stdout.strip())
        assert output["level"] == level
    
    def test_required_fields(self):
        """必須フィールド（uri, message）の確認"""
        # 必須フィールドがある場合
        script = """
import sys
sys.path.insert(0, '.')
from __init__ import log
log("INFO", {"uri": "/test", "message": "test"})
"""
        stdout, _, returncode = self.run_command(["python3", "-c", script])
        assert returncode == 0
        
        output = json.loads(stdout.strip())
        assert "uri" in output
        assert "message" in output
    
    def test_field_extension(self):
        """フィールド拡張が可能"""
        extended_data = {
            "uri": "/api/users",
            "message": "User created",
            "user_id": "123",
            "request_id": "req-456",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        script = f"""
import sys
sys.path.insert(0, '.')
from __init__ import log
log("INFO", {extended_data})
"""
        stdout, _, returncode = self.run_command(["python3", "-c", script])
        
        assert returncode == 0
        output = json.loads(stdout.strip())
        
        # すべての拡張フィールドが保持されている
        for key, value in extended_data.items():
            assert output[key] == value
    
    def test_jsonl_single_line(self):
        """出力が1行のJSONであること"""
        script = """
import sys
sys.path.insert(0, '.')
from __init__ import log
log("INFO", {"uri": "/test", "message": "multi\\nline\\ntest"})
"""
        stdout, _, _ = self.run_command(["python3", "-c", script])
        
        # 改行が1つだけ（最後の改行）
        assert stdout.count('\n') == 1
        assert stdout.endswith('\n')
    
    def test_to_jsonl_function(self):
        """to_jsonl関数の動作確認"""
        script = """
import sys
sys.path.insert(0, '.')
from __init__ import to_jsonl
result = to_jsonl({"key": "value", "nested": {"inner": "data"}})
print(result)
"""
        stdout, _, returncode = self.run_command(["python3", "-c", script])
        
        assert returncode == 0
        # 改行なしのJSON
        assert '\n' not in stdout.strip()
        # 有効なJSON
        parsed = json.loads(stdout.strip())
        assert parsed["key"] == "value"
        assert parsed["nested"]["inner"] == "data"


class TestCrossLanguageCompatibility:
    """言語間の互換性テスト"""
    
    def test_output_format_consistency(self):
        """全言語で同じ入力に対して同じ形式の出力"""
        test_input = {
            "uri": "/api/health",
            "message": "Health check",
            "status": "ok",
            "latency_ms": 42
        }
        
        outputs = []
        
        # Python
        script = f"""
import sys
sys.path.insert(0, '.')
from __init__ import log
log("METRIC", {test_input})
"""
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            outputs.append(("python", json.loads(result.stdout.strip())))
        
        # TypeScript (if available)
        ts_script = f"""
import {{ log }} from './mod.ts';
log("METRIC", {json.dumps(test_input)});
"""
        test_file = Path("test_compat.ts")
        test_file.write_text(ts_script)
        
        try:
            result = subprocess.run(
                ["deno", "run", str(test_file)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                outputs.append(("typescript", json.loads(result.stdout.strip())))
        except FileNotFoundError:
            # Deno not installed
            pass
        finally:
            test_file.unlink(missing_ok=True)
        
        # 全実装で同じキーと値を持つことを確認
        if len(outputs) > 1:
            first_lang, first_output = outputs[0]
            for lang, output in outputs[1:]:
                assert output == first_output, f"{lang} output differs from {first_lang}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])