"""
logger_wrapperのテスト
bin/src/logの必須フィールド要件を満たすことを確認
"""
import json
import sys
from io import StringIO
import pytest

from .logger_wrapper import log, info, error, result


class TestLoggerWrapper:
    """logger_wrapperがbin/src/logの仕様を満たすことを確認"""
    
    def test_log_output_has_required_fields(self):
        """log出力に必須フィールド（uri, message）が含まれる"""
        # stdout をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            # ログ出力
            log("INFO", "test.module", "Test message", extra="data")
            
            # 出力を取得
            output = captured_output.getvalue().strip()
            data = json.loads(output)
            
            # 必須フィールドの確認
            assert "uri" in data, "uri field is required by bin/src/log"
            assert "message" in data, "message field is required by bin/src/log"
            
            # uri の形式確認
            assert data["uri"].startswith("/rgl/"), f"uri should start with /rgl/, got: {data['uri']}"
            assert "test.module" in data["uri"], f"uri should contain module name, got: {data['uri']}"
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_info_shortcut_creates_valid_output(self):
        """infoショートカットが有効な出力を生成する"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            info("app.handler", "Processing request", request_id="123")
            
            output = captured_output.getvalue().strip()
            data = json.loads(output)
            
            # bin/src/logの必須フィールド
            assert "uri" in data
            assert "message" in data
            assert data["message"] == "Processing request"
            assert data["uri"] == "/rgl/app.handler"
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_error_output_format(self):
        """error関数が適切な形式で出力する"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            error("Database connection failed", details={"host": "localhost", "port": 5432})
            
            output = captured_output.getvalue().strip()
            data = json.loads(output)
            
            # 必須フィールド
            assert "uri" in data
            assert "message" in data
            assert data["message"] == "Database connection failed"
            
            # error特有のフィールド
            assert data.get("type") == "error"
            assert "details" in data
            assert data["details"]["host"] == "localhost"
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_result_output_format(self):
        """result関数が適切な形式で出力する"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            result({"status": "success", "count": 42})
            
            output = captured_output.getvalue().strip()
            data = json.loads(output)
            
            # 必須フィールド
            assert "uri" in data
            assert "message" in data
            
            # result特有のフィールド
            assert data.get("type") == "result"
            assert "data" in data
            assert data["data"]["count"] == 42
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_no_duplicate_level_field(self):
        """levelフィールドが重複しない"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            log("WARN", "test.module", "Warning message")
            
            output = captured_output.getvalue().strip()
            # bin/src/logが先にlevelを設定するので、追加のlevelフィールドがないことを確認
            assert output.count('"level"') == 1, "level field should appear only once"
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_module_preserved_for_compatibility(self):
        """後方互換性のためmoduleフィールドが保持される"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            info("my.module", "Test")
            
            output = captured_output.getvalue().strip()
            data = json.loads(output)
            
            # moduleフィールドが保持されている
            assert "module" in data
            assert data["module"] == "my.module"
            
        finally:
            sys.stdout = sys.__stdout__