"""
Simplified performance measurement using log_py
stdout-only minimal implementation
"""
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
import functools

try:
    # log_pyが利用可能な場合
    import sys
    import os
    # 相対パスを絶対パスに変換
    log_py_path = os.path.join(os.path.dirname(__file__), "../../../telemetry/log_py")
    sys.path.insert(0, os.path.abspath(log_py_path))
    from log_py import log
    # log_pyのlogはlevelをデータ内に含める必要がある
    _original_log = log
    def log(level: str, data: dict):
        _original_log(level, data)
except ImportError:
    # フォールバック: 単純なprint
    import json
    from datetime import datetime
    
    def log(level: str, data: dict):
        """Fallback log function"""
        output = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            **data
        }
        # print文削除指示によりコメントアウト
        pass


@contextmanager
def measure_time(name: str, threshold: Optional[float] = None, **metadata):
    """
    最小限の時間計測実装
    
    Args:
        name: 計測名
        threshold: 閾値（秒）
        **metadata: 追加情報
        
    Example:
        with measure_time("database_query", threshold=1.0):
            result = query()
    """
    start_time = time.perf_counter()
    
    # 開始ログ
    log("INFO", {
        "message": f"Performance measurement started: {name}",
        "event": "perf_start",
        "name": name,
        "threshold": threshold,
        **metadata
    })
    
    try:
        yield
    finally:
        # 終了時間計測
        duration = time.perf_counter() - start_time
        
        # 結果ログ
        log_data = {
            "event": "perf_end",
            "name": name,
            "duration_seconds": duration,
            **metadata
        }
        
        # 閾値チェック
        if threshold and duration > threshold:
            log_data["threshold_exceeded"] = True
            log_data["threshold"] = threshold
            log_data["exceeded_by"] = duration - threshold
            log_data["message"] = f"Performance threshold exceeded: {name} took {duration:.3f}s (threshold: {threshold}s)"
            log_level = "WARN"
        else:
            log_data["message"] = f"Performance measurement completed: {name} took {duration:.3f}s"
            log_level = "INFO"
            
        log(log_level, log_data)


def measure_function(name: Optional[str] = None, threshold: Optional[float] = None):
    """
    関数計測デコレーター（最小実装）
    
    Example:
        @measure_function(threshold=0.5)
        def slow_function():
            time.sleep(1)
    """
    def decorator(func):
        measurement_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with measure_time(measurement_name, threshold):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# テスト用のサンプル関数
if __name__ == "__main__":
    # 基本的な使用例
    with measure_time("example_operation", threshold=0.5):
        time.sleep(0.3)
        
    with measure_time("slow_operation", threshold=0.1):
        time.sleep(0.2)
        
    @measure_function(threshold=0.1)
    def example_function():
        time.sleep(0.15)
        return "done"
        
    result = example_function()
