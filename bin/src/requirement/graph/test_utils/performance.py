"""
Performance measurement utilities for tests

Features:
- Context manager for time measurement
- Function decorator for automatic measurement
- Performance data collection and reporting
- Structured logging for CI/CD integration
"""
import time
import json
import functools
import statistics
from contextlib import contextmanager
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

# 構造化ログ用のロガー設定
logger = logging.getLogger(__name__)


@dataclass
class Measurement:
    """単一の計測結果"""
    name: str
    duration_seconds: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON出力用の辞書形式"""
        return {
            "name": self.name,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class PerformanceCollector:
    """
    パフォーマンス計測の集約と分析
    
    Usage:
        collector = PerformanceCollector()
        
        with collector.measure("database_query"):
            # 重い処理
            pass
            
        collector.report()  # 統計情報を出力
    """
    
    def __init__(self, name: str = "test_performance"):
        self.name = name
        self.measurements: List[Measurement] = []
        
    def add_measurement(self, measurement: Measurement):
        """計測結果を追加"""
        self.measurements.append(measurement)
        
    @contextmanager
    def measure(self, name: str, threshold: Optional[float] = None, **metadata):
        """計測用コンテキストマネージャー"""
        start_time = time.perf_counter()
        timestamp = time.time()
        
        try:
            yield self
        finally:
            duration = time.perf_counter() - start_time
            measurement = Measurement(
                name=name,
                duration_seconds=duration,
                timestamp=timestamp,
                metadata=metadata
            )
            self.add_measurement(measurement)
            
            # 閾値チェック
            if threshold and duration > threshold:
                logger.warning(
                    f"Performance threshold exceeded for '{name}'",
                    extra={
                        "measurement_name": name,
                        "duration": duration,
                        "threshold": threshold,
                        "exceeded_by": duration - threshold
                    }
                )
    
    def get_statistics(self, name: Optional[str] = None) -> Dict[str, Any]:
        """統計情報を取得"""
        measurements = self.measurements
        if name:
            measurements = [m for m in measurements if m.name == name]
            
        if not measurements:
            return {}
            
        durations = [m.duration_seconds for m in measurements]
        
        stats = {
            "count": len(durations),
            "total": sum(durations),
            "min": min(durations),
            "max": max(durations),
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
        }
        
        if len(durations) >= 2:
            stats["stdev"] = statistics.stdev(durations)
            
        if len(durations) >= 5:
            # 95パーセンタイル
            sorted_durations = sorted(durations)
            p95_index = int(len(sorted_durations) * 0.95)
            stats["p95"] = sorted_durations[p95_index]
            
        return stats
    
    def report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        パフォーマンスレポートを生成
        
        Args:
            output_path: JSONファイルの出力先（Noneの場合は標準出力）
            
        Returns:
            レポート辞書
        """
        # 計測名でグループ化
        grouped = {}
        for m in self.measurements:
            if m.name not in grouped:
                grouped[m.name] = []
            grouped[m.name].append(m)
            
        # 各グループの統計情報
        report = {
            "name": self.name,
            "total_measurements": len(self.measurements),
            "statistics": {},
            "raw_measurements": [m.to_dict() for m in self.measurements]
        }
        
        for name in grouped:
            report["statistics"][name] = self.get_statistics(name)
            
        # 出力
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Performance report saved to {output_path}")
        else:
            logger.info("Performance Report", extra=report)
            
        return report


# グローバルコレクター（オプション）
_global_collector = PerformanceCollector("global")


@contextmanager
def measure_time(name: str, threshold: Optional[float] = None, 
                collector: Optional[PerformanceCollector] = None, **metadata):
    """
    時間計測のためのコンテキストマネージャー
    
    Args:
        name: 計測名
        threshold: 閾値（秒）。超過時に警告
        collector: 使用するコレクター（Noneの場合はグローバル）
        **metadata: 追加のメタデータ
        
    Example:
        with measure_time("database_query", threshold=1.0):
            result = expensive_query()
    """
    if collector is None:
        collector = _global_collector
        
    with collector.measure(name, threshold, **metadata):
        yield


def measure_function(threshold: Optional[float] = None, 
                    collector: Optional[PerformanceCollector] = None,
                    name: Optional[str] = None):
    """
    関数の実行時間を計測するデコレーター
    
    Args:
        threshold: 閾値（秒）
        collector: 使用するコレクター
        name: 計測名（Noneの場合は関数名）
        
    Example:
        @measure_function(threshold=0.5)
        def slow_function():
            time.sleep(1)
    """
    def decorator(func: Callable) -> Callable:
        measurement_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with measure_time(measurement_name, threshold, collector):
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


# pytest統合用のフィクスチャとして使用可能
def pytest_fixture_collector():
    """
    pytestフィクスチャとして使用
    
    Example in conftest.py:
        @pytest.fixture
        def perf_collector():
            from test_utils.performance import PerformanceCollector
            collector = PerformanceCollector("test_session")
            yield collector
            collector.report()  # テスト終了時にレポート
    """
    return PerformanceCollector("pytest_session")