"""
Tests for performance measurement utilities
"""
import time
import json
import pytest
from pathlib import Path
import tempfile

from test_utils.performance import (
    measure_time, 
    measure_function, 
    PerformanceCollector,
    Measurement
)


class TestMeasureTime:
    """measure_time context manager tests"""
    
    def test_basic_measurement(self):
        """基本的な時間計測が動作する"""
        collector = PerformanceCollector("test")
        
        with measure_time("test_operation", collector=collector):
            time.sleep(0.1)  # 100ms
            
        assert len(collector.measurements) == 1
        measurement = collector.measurements[0]
        assert measurement.name == "test_operation"
        assert 0.09 < measurement.duration_seconds < 0.15  # 誤差を考慮
        
    def test_threshold_warning(self, caplog):
        """閾値超過時に警告が出る"""
        collector = PerformanceCollector("test")
        
        with measure_time("slow_operation", threshold=0.05, collector=collector):
            time.sleep(0.1)
            
        # 警告ログが出力される
        assert "Performance threshold exceeded" in caplog.text
        
    def test_metadata_storage(self):
        """メタデータが正しく保存される"""
        collector = PerformanceCollector("test")
        
        with measure_time("operation", collector=collector, user="test_user", iteration=5):
            pass
            
        measurement = collector.measurements[0]
        assert measurement.metadata["user"] == "test_user"
        assert measurement.metadata["iteration"] == 5


class TestMeasureFunction:
    """measure_function decorator tests"""
    
    def test_function_decorator(self):
        """関数デコレーターが動作する"""
        collector = PerformanceCollector("test")
        
        @measure_function(collector=collector)
        def slow_function(duration):
            time.sleep(duration)
            return "done"
            
        result = slow_function(0.1)
        
        assert result == "done"
        assert len(collector.measurements) == 1
        assert collector.measurements[0].name == "slow_function"
        
    def test_custom_name(self):
        """カスタム名を指定できる"""
        collector = PerformanceCollector("test")
        
        @measure_function(collector=collector, name="custom_operation")
        def my_function():
            pass
            
        my_function()
        
        assert collector.measurements[0].name == "custom_operation"


class TestPerformanceCollector:
    """PerformanceCollector tests"""
    
    def test_statistics_calculation(self):
        """統計情報が正しく計算される"""
        collector = PerformanceCollector("test")
        
        # 複数の計測を追加
        for i in range(10):
            collector.add_measurement(
                Measurement(
                    name="operation",
                    duration_seconds=0.1 * (i + 1),  # 0.1, 0.2, ..., 1.0
                    timestamp=time.time()
                )
            )
            
        stats = collector.get_statistics("operation")
        
        assert stats["count"] == 10
        assert stats["min"] == 0.1
        assert stats["max"] == 1.0
        assert abs(stats["mean"] - 0.55) < 0.01  # 平均は0.55
        assert stats["median"] == 0.55
        assert "stdev" in stats
        assert "p95" in stats
        
    def test_grouped_statistics(self):
        """異なる操作の統計が分離される"""
        collector = PerformanceCollector("test")
        
        # 操作Aの計測
        for i in range(5):
            with collector.measure("operation_a"):
                time.sleep(0.01)
                
        # 操作Bの計測
        for i in range(3):
            with collector.measure("operation_b"):
                time.sleep(0.02)
                
        stats_a = collector.get_statistics("operation_a")
        stats_b = collector.get_statistics("operation_b")
        
        assert stats_a["count"] == 5
        assert stats_b["count"] == 3
        assert stats_a["mean"] < stats_b["mean"]  # Bの方が遅い
        
    def test_report_generation(self):
        """レポート生成が動作する"""
        collector = PerformanceCollector("test_session")
        
        with collector.measure("setup"):
            time.sleep(0.01)
            
        with collector.measure("test_1"):
            time.sleep(0.02)
            
        with collector.measure("teardown"):
            time.sleep(0.01)
            
        report = collector.report()
        
        assert report["name"] == "test_session"
        assert report["total_measurements"] == 3
        assert "statistics" in report
        assert "setup" in report["statistics"]
        assert "test_1" in report["statistics"]
        assert "teardown" in report["statistics"]
        assert len(report["raw_measurements"]) == 3
        
    def test_json_output(self):
        """JSONファイル出力が動作する"""
        collector = PerformanceCollector("test")
        
        with collector.measure("operation"):
            pass
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
            
        try:
            report = collector.report(output_path)
            
            # ファイルが作成される
            assert output_path.exists()
            
            # JSONとして読み込める
            with open(output_path) as f:
                loaded = json.load(f)
                
            assert loaded["name"] == report["name"]
            assert loaded["total_measurements"] == 1
            
        finally:
            output_path.unlink()


class TestPytestIntegration:
    """pytest統合のテスト"""
    
    def test_fixture_usage(self):
        """フィクスチャとして使用できる"""
        # conftest.pyでの使用例
        collector = PerformanceCollector("fixture_test")
        
        # テスト内での使用
        with collector.measure("test_case_1"):
            time.sleep(0.01)
            
        with collector.measure("test_case_2"):
            time.sleep(0.02)
            
        # セッション終了時
        report = collector.report()
        
        assert report["total_measurements"] == 2
        assert "test_case_1" in report["statistics"]
        assert "test_case_2" in report["statistics"]