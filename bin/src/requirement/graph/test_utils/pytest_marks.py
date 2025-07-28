"""
Pytest custom marks and decorators for test categorization

使用例:
    from test_utils.pytest_marks import mark_slow, mark_vss_required
    
    @mark_slow(expected_time=15)
    def test_heavy_operation():
        # 15秒かかる処理
        pass
    
    @mark_vss_required
    def test_vector_search():
        # VSSサービスが必要なテスト
        pass
"""
import pytest
from typing import Optional, Callable
import functools


def mark_slow(expected_time: Optional[float] = None):
    """
    遅いテストをマーク（5秒以上）
    
    Args:
        expected_time: 予想実行時間（秒）
    """
    def decorator(func):
        marked = pytest.mark.slow(func)
        if expected_time and expected_time > 30:
            # 30秒以上なら very_slow も追加
            marked = pytest.mark.very_slow(marked)
        # メタデータとして予想時間を保存
        marked.expected_time = expected_time
        return marked
    return decorator


def mark_very_slow(expected_time: Optional[float] = None):
    """
    非常に遅いテストをマーク（30秒以上）
    
    Args:
        expected_time: 予想実行時間（秒）
    """
    def decorator(func):
        # very_slow は自動的に slow も含む
        marked = pytest.mark.very_slow(pytest.mark.slow(func))
        marked.expected_time = expected_time
        return marked
    return decorator


# シンプルなマーク（引数なし）
mark_e2e = pytest.mark.e2e
mark_integration = pytest.mark.integration
mark_unit = pytest.mark.unit
mark_vss_required = pytest.mark.vss_required
mark_flaky = pytest.mark.flaky


def mark_performance(threshold: float):
    """
    パフォーマンステストをマーク
    
    Args:
        threshold: 許容実行時間（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            if duration > threshold:
                pytest.fail(f"Performance test failed: {duration:.2f}s > {threshold}s threshold")
            return result
        return pytest.mark.performance(wrapper)
    return decorator


# 複合マーク
def mark_slow_e2e(expected_time: Optional[float] = None):
    """E2Eかつ遅いテスト"""
    def decorator(func):
        marked = mark_e2e(func)
        return mark_slow(expected_time)(marked)
    return decorator


def mark_slow_integration(expected_time: Optional[float] = None):
    """統合テストかつ遅いテスト"""
    def decorator(func):
        marked = mark_integration(func)
        return mark_slow(expected_time)(marked)
    return decorator


# カスタムスキップ条件
skip_if_no_vss = pytest.mark.skipif(
    "not config.getoption('--with-vss')",
    reason="VSS service not available (use --with-vss to enable)"
)


# テスト実行例
"""
# 遅いテストを除外
pytest -m "not slow"

# 非常に遅いテストのみ除外（通常の遅いテストは実行）
pytest -m "not very_slow"

# 高速なユニットテストのみ
pytest -m "unit and not slow"

# E2Eテストのうち遅くないものだけ
pytest -m "e2e and not slow"

# VSSが必要なテストをスキップ
pytest -m "not vss_required"

# パフォーマンステストのみ実行
pytest -m "performance"
"""