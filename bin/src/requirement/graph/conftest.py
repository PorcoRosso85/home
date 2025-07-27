"""
共通のテストフィクスチャ
高速なインメモリデータベースとサブプロセス最適化を提供
"""
import pytest
import tempfile
import subprocess
import json
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# パフォーマンス計測用
from test_utils.performance import PerformanceCollector, measure_time


def run_system_optimized(input_data: Dict[str, Any], db_path: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """最適化されたrun_system関数（タイムアウトとクリーンアップ付き）"""
    env = os.environ.copy()
    if db_path:
        env["RGL_DATABASE_PATH"] = db_path

    python_cmd = sys.executable
    
    # プロセスを作成
    process = subprocess.Popen(
        [python_cmd, "-m", "requirement.graph"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    try:
        # タイムアウト付きで実行
        stdout, stderr = process.communicate(
            input=json.dumps(input_data),
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        # タイムアウト時は強制終了
        process.kill()
        stdout, stderr = process.communicate()
        return {
            "error": "Process timeout",
            "stderr": stderr,
            "timeout": timeout
        }
    finally:
        # 確実にプロセスをクリーンアップ
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    # 結果をパース
    if stdout:
        lines = stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    
    return {"error": "No valid JSON output", "stderr": stderr}


@pytest.fixture
def inmemory_db():
    """インメモリデータベースを使用するフィクスチャ"""
    # KuzuDBは:memory:だけで独立したインスタンスを作成
    db_path = ":memory:"
    
    # スキーマ初期化
    result = run_system_optimized({"type": "schema", "action": "apply"}, db_path)
    if "error" in result:
        pytest.fail(f"Failed to initialize schema: {result}")
    
    yield db_path
    
    # インメモリDBは自動的にクリーンアップされる


@pytest.fixture
def file_db():
    """ファイルベースのデータベースを使用するフィクスチャ（必要な場合のみ）"""
    with tempfile.TemporaryDirectory() as db_dir:
        # スキーマ初期化
        result = run_system_optimized({"type": "schema", "action": "apply"}, db_dir)
        if "error" in result:
            pytest.fail(f"Failed to initialize schema: {result}")
        
        yield db_dir


@pytest.fixture
def run_system():
    """最適化されたrun_system関数を提供するフィクスチャ"""
    return run_system_optimized


# E2Eテストのマーカーを自動的に追加
import inspect

def pytest_collection_modifyitems(items):
    """run_systemを使用するテストに自動的にe2eマーカーを追加"""
    for item in items:
        # テスト関数のソースコードを確認
        if hasattr(item, "function"):
            try:
                source = inspect.getsource(item.function)
                if "run_system" in source:
                    item.add_marker(pytest.mark.e2e)
            except (OSError, TypeError):
                # ソースコードが取得できない場合はスキップ
                pass


# パフォーマンス計測フィクスチャ
@pytest.fixture(scope="session")
def perf_collector():
    """
    セッション全体のパフォーマンス計測
    
    使用例:
        def test_slow_operation(perf_collector):
            with perf_collector.measure("database_query", threshold=1.0):
                result = expensive_operation()
    """
    collector = PerformanceCollector("test_session")
    yield collector
    
    # セッション終了時にレポート出力
    report_path = Path("test_performance_report.json")
    report = collector.report(report_path)
    print(f"\nPerformance Report saved to: {report_path}")
    print(f"Total measurements: {report['total_measurements']}")
    
    # 遅いテストの警告
    slow_tests = []
    for name, stats in report["statistics"].items():
        if stats["max"] > 5.0:  # 5秒以上
            slow_tests.append((name, stats["max"]))
    
    if slow_tests:
        print("\n⚠️  Slow tests detected:")
        for name, duration in sorted(slow_tests, key=lambda x: x[1], reverse=True):
            print(f"  - {name}: {duration:.2f}s")


# リアルタイム実行時間表示（環境変数で有効化）
import time
from datetime import datetime

if os.environ.get("PYTEST_REALTIME", ""):
    test_start_times = {}
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(item):
        """各テストの開始時に呼ばれる"""
        test_start_times[item.nodeid] = time.time()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting: {item.nodeid}")
    
    @pytest.hookimpl(trylast=True)
    def pytest_runtest_teardown(item, nextitem):
        """各テストの終了時に呼ばれる"""
        if item.nodeid in test_start_times:
            duration = time.time() - test_start_times[item.nodeid]
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Finished: {item.nodeid} ({duration:.2f}s)")
            del test_start_times[item.nodeid]


@pytest.fixture
def measure():
    """
    個別テスト用の計測ヘルパー
    
    使用例:
        def test_something(measure):
            with measure("setup", threshold=0.5):
                prepare_data()
                
            with measure("main_operation", threshold=2.0):
                result = process_data()
    """
    collector = PerformanceCollector("single_test")
    
    def _measure(name: str, threshold: Optional[float] = None, **metadata):
        return collector.measure(name, threshold, **metadata)
    
    yield _measure
    
    # テスト終了時に統計を出力（verbose時のみ）
    if collector.measurements:
        print(f"\nTest performance summary:")
        for name, stats in collector.get_statistics().items():
            print(f"  {name}: {stats['mean']:.3f}s (n={stats['count']})")