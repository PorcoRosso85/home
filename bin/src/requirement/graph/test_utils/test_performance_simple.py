"""
Tests for performance_simple.py
TDD RED phase - テストファースト開発
"""
import pytest
import time
import json
import sys
from io import StringIO
from unittest.mock import patch
from contextlib import redirect_stdout

# テスト対象をインポート
from test_utils.performance_simple import measure_time, measure_function


class TestMeasureTime:
    """measure_time関数のテスト"""
    
    def test_basic_measurement(self):
        """基本的な計測が動作すること"""
        # 標準出力をキャプチャ
        output = StringIO()
        with redirect_stdout(output):
            with measure_time("test_operation"):
                time.sleep(0.01)  # 短い処理
        
        # 出力されたJSONを検証
        lines = output.getvalue().strip().split('\n')
        assert len(lines) == 2  # 開始と終了の2行
        
        # 開始ログの検証
        start_log = json.loads(lines[0])
        assert start_log["event"] == "perf_start"
        assert start_log["name"] == "test_operation"
        assert start_log["message"].startswith("Performance measurement started:")
        
        # 終了ログの検証
        end_log = json.loads(lines[1])
        assert end_log["event"] == "perf_end"
        assert end_log["name"] == "test_operation"
        assert "duration_seconds" in end_log
        assert end_log["duration_seconds"] > 0
        assert end_log["message"].startswith("Performance measurement completed:")
    
    def test_threshold_not_exceeded(self):
        """閾値を超えない場合の動作"""
        output = StringIO()
        with redirect_stdout(output):
            with measure_time("fast_operation", threshold=1.0):
                time.sleep(0.01)
        
        lines = output.getvalue().strip().split('\n')
        end_log = json.loads(lines[-1])
        
        assert "level" not in end_log or end_log["level"] == "INFO"
        assert "threshold_exceeded" not in end_log
        assert "exceeded_by" not in end_log
    
    def test_threshold_exceeded(self):
        """閾値を超えた場合の警告"""
        output = StringIO()
        with redirect_stdout(output):
            with measure_time("slow_operation", threshold=0.01):
                time.sleep(0.05)
        
        lines = output.getvalue().strip().split('\n')
        end_log = json.loads(lines[-1])
        
        assert "level" not in end_log or end_log["level"] == "WARN"
        assert end_log["threshold_exceeded"] is True
        assert end_log["threshold"] == 0.01
        assert "exceeded_by" in end_log
        assert end_log["exceeded_by"] > 0
        assert "Performance threshold exceeded" in end_log["message"]
    
    def test_with_metadata(self):
        """メタデータ付き計測"""
        output = StringIO()
        with redirect_stdout(output):
            with measure_time("db_query", query_type="SELECT", table="requirements"):
                pass
        
        lines = output.getvalue().strip().split('\n')
        start_log = json.loads(lines[0])
        end_log = json.loads(lines[1])
        
        # メタデータが両方のログに含まれること
        assert start_log["query_type"] == "SELECT"
        assert start_log["table"] == "requirements"
        assert end_log["query_type"] == "SELECT"
        assert end_log["table"] == "requirements"
    
    def test_exception_handling(self):
        """例外が発生しても計測が完了すること"""
        output = StringIO()
        
        with pytest.raises(ValueError):
            with redirect_stdout(output):
                with measure_time("failing_operation"):
                    raise ValueError("Test error")
        
        # 例外が発生してもログが出力されること
        lines = output.getvalue().strip().split('\n')
        assert len(lines) == 2
        end_log = json.loads(lines[-1])
        assert end_log["event"] == "perf_end"
        assert "duration_seconds" in end_log


class TestMeasureFunction:
    """measure_functionデコレーターのテスト"""
    
    def test_basic_decorator(self):
        """基本的なデコレーター動作"""
        output = StringIO()
        
        @measure_function()
        def test_func():
            time.sleep(0.01)
            return "result"
        
        with redirect_stdout(output):
            result = test_func()
        
        assert result == "result"
        
        lines = output.getvalue().strip().split('\n')
        end_log = json.loads(lines[-1])
        assert end_log["name"] == "test_func"
        assert end_log["event"] == "perf_end"
    
    def test_decorator_with_custom_name(self):
        """カスタム名前付きデコレーター"""
        output = StringIO()
        
        @measure_function(name="custom_operation")
        def some_function():
            return 42
        
        with redirect_stdout(output):
            result = some_function()
        
        assert result == 42
        
        lines = output.getvalue().strip().split('\n')
        end_log = json.loads(lines[-1])
        assert end_log["name"] == "custom_operation"
    
    def test_decorator_with_threshold(self):
        """閾値付きデコレーター"""
        output = StringIO()
        
        @measure_function(threshold=0.01)
        def slow_function():
            time.sleep(0.05)
            return "slow"
        
        with redirect_stdout(output):
            result = slow_function()
        
        assert result == "slow"
        
        lines = output.getvalue().strip().split('\n')
        end_log = json.loads(lines[-1])
        assert "level" not in end_log or end_log["level"] == "WARN"
        assert end_log["threshold_exceeded"] is True
    
    def test_decorator_preserves_function_metadata(self):
        """デコレーターが関数のメタデータを保持すること"""
        @measure_function()
        def documented_function():
            """This is a docstring"""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a docstring"
    
    def test_decorator_with_arguments(self):
        """引数付き関数のデコレーター"""
        output = StringIO()
        
        @measure_function(name="add_operation")
        def add(a, b, offset=0):
            return a + b + offset
        
        with redirect_stdout(output):
            result = add(1, 2, offset=3)
        
        assert result == 6
        
        lines = output.getvalue().strip().split('\n')
        end_log = json.loads(lines[-1])
        assert end_log["name"] == "add_operation"


class TestLogPyIntegration:
    """log_pyとの統合テスト"""
    
    def test_log_py_format_compatibility(self):
        """log_py形式の互換性確認"""
        output = StringIO()
        
        with redirect_stdout(output):
            with measure_time("compatibility_test"):
                pass
        
        lines = output.getvalue().strip().split('\n')
        
        # 各行が有効なJSONであること
        for line in lines:
            log_entry = json.loads(line)
            # log_pyの実装ではlevelとtimestampは自動付与されない
            # フォールバック実装でのみtimestampとlevelが含まれる
            assert "message" in log_entry
            assert "event" in log_entry
            assert "name" in log_entry


# パフォーマンステスト用のヘルパー
def test_performance_measurement_overhead():
    """計測自体のオーバーヘッドが小さいこと"""
    # 計測なしの場合
    start = time.perf_counter()
    for _ in range(100):
        time.sleep(0.001)
    baseline = time.perf_counter() - start
    
    # 計測ありの場合
    output = StringIO()
    start = time.perf_counter()
    with redirect_stdout(output):
        for _ in range(100):
            with measure_time("overhead_test"):
                time.sleep(0.001)
    measured = time.perf_counter() - start
    
    # オーバーヘッドは10%以下であること
    overhead_ratio = (measured - baseline) / baseline
    assert overhead_ratio < 0.1, f"Overhead too high: {overhead_ratio:.2%}"