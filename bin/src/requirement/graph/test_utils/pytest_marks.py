"""
Pytest marks for test categorization

ログレベルのような階層的なテスト分類システム:
- INSTANT: < 0.1秒（単体テスト、純粋関数）
- FAST: < 1秒（軽量な統合テスト）
- NORMAL: < 5秒（通常の統合テスト）
- SLOW: < 30秒（重い統合テスト、E2E）
- VERY_SLOW: >= 30秒（非常に重いE2E）

複数タグサポート:
- テストタイプ: unit, integration, e2e
- 依存関係: vss_required, db_required, network_required
- 信頼性: stable, flaky
- 環境: local_only, ci_only

使用例:
    from test_utils.pytest_marks import mark_test, TestSpeed, TestType, TestDependency
    
    @mark_test(
        speed=TestSpeed.SLOW,
        test_type=TestType.E2E,
        dependencies=[TestDependency.VSS, TestDependency.DB],
        tags=["smoke", "nightly"]
    )
    def test_complex_integration():
        pass
    
    # または実際の秒数で
    @mark_test(speed=38.5, test_type=TestType.E2E)
    def test_with_actual_time():
        pass
"""
import pytest
from typing import Optional, List, Union, Callable
from enum import Enum, auto
import functools


class TestSpeed(Enum):
    """テスト速度レベル（ログレベルのような階層）"""
    INSTANT = 0.1    # < 0.1秒
    FAST = 1.0       # < 1秒
    NORMAL = 5.0     # < 5秒
    SLOW = 30.0      # < 30秒
    VERY_SLOW = float('inf')  # >= 30秒


class TestType(Enum):
    """テストタイプ"""
    UNIT = auto()
    INTEGRATION = auto()
    E2E = auto()


class TestDependency(Enum):
    """テストの依存関係"""
    VSS = auto()
    DB = auto()
    NETWORK = auto()
    FILESYSTEM = auto()


class TestReliability(Enum):
    """テストの信頼性"""
    STABLE = auto()
    FLAKY = auto()
    EXPERIMENTAL = auto()


def mark_test(
    speed: Union[TestSpeed, float],
    test_type: TestType,
    dependencies: Optional[List[TestDependency]] = None,
    reliability: TestReliability = TestReliability.STABLE,
    tags: Optional[List[str]] = None
):
    """統合的なテストマーキング
    
    Args:
        speed: テスト速度レベルまたは実際の秒数
        test_type: テストタイプ
        dependencies: 依存関係のリスト
        reliability: テストの信頼性
        tags: 追加のカスタムタグ
    
    Example:
        @mark_test(
            speed=TestSpeed.SLOW,
            test_type=TestType.E2E,
            dependencies=[TestDependency.VSS, TestDependency.DB],
            reliability=TestReliability.FLAKY,
            tags=["smoke", "nightly"]
        )
        def test_complex_integration():
            pass
    """
    def decorator(func):
        # 速度マーク
        if isinstance(speed, (int, float)):
            # 実際の秒数から適切なレベルを判定
            if speed < TestSpeed.INSTANT.value:
                func = pytest.mark.instant(func)
            elif speed < TestSpeed.FAST.value:
                func = pytest.mark.fast(func)
            elif speed < TestSpeed.NORMAL.value:
                func = pytest.mark.normal(func)
            elif speed < TestSpeed.SLOW.value:
                func = pytest.mark.slow(func)
            else:
                func = pytest.mark.very_slow(func)
            func.expected_time = speed
        else:
            # TestSpeedレベルを直接使用
            func = getattr(pytest.mark, speed.name.lower())(func)
            func.expected_time = speed.value
        
        # テストタイプマーク
        func = getattr(pytest.mark, test_type.name.lower())(func)
        
        # 依存関係マーク
        if dependencies:
            for dep in dependencies:
                func = getattr(pytest.mark, f"{dep.name.lower()}_required")(func)
        
        # 信頼性マーク
        if reliability != TestReliability.STABLE:
            func = getattr(pytest.mark, reliability.name.lower())(func)
        
        # カスタムタグ
        if tags:
            for tag in tags:
                func = getattr(pytest.mark, tag)(func)
        
        return func
    return decorator


# 後方互換性のための既存マーク
def mark_slow(expected_time: Optional[float] = None):
    """遅いテストをマーク（5秒以上）"""
    def decorator(func):
        marked = pytest.mark.slow(func)
        if expected_time and expected_time > 30:
            marked = pytest.mark.very_slow(marked)
        marked.expected_time = expected_time
        return marked
    return decorator


def mark_very_slow(expected_time: Optional[float] = None):
    """非常に遅いテストをマーク（30秒以上）"""
    def decorator(func):
        marked = pytest.mark.slow(pytest.mark.very_slow(func))
        marked.expected_time = expected_time
        return marked
    return decorator


# 既存の単純マーク（後方互換性）
mark_e2e = pytest.mark.e2e
mark_integration = pytest.mark.integration
mark_unit = pytest.mark.unit
mark_vss_required = pytest.mark.vss_required
mark_flaky = pytest.mark.flaky

# 新しい階層的速度マーク
mark_instant = pytest.mark.instant
mark_fast = pytest.mark.fast
mark_normal = pytest.mark.normal

# 依存関係マーク
mark_db_required = pytest.mark.db_required
mark_network_required = pytest.mark.network_required
mark_filesystem_required = pytest.mark.filesystem_required

# 信頼性マーク
mark_stable = pytest.mark.stable
mark_experimental = pytest.mark.experimental


def mark_performance(threshold: float):
    """パフォーマンステストをマーク"""
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


# 複合マーク（後方互換性）
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
# 速度階層での実行
pytest -m "instant"           # 0.1秒未満のテストのみ
pytest -m "fast or instant"   # 1秒未満のテストのみ
pytest -m "not slow and not very_slow"  # 5秒未満のテストのみ
pytest -m "not very_slow"     # 30秒未満のテストのみ

# 複合条件
pytest -m "unit and (instant or fast)"  # 高速なユニットテストのみ
pytest -m "e2e and not very_slow"       # 30秒未満のE2Eテスト
pytest -m "integration and not vss_required"  # VSSを使わない統合テスト

# 信頼性での実行
pytest -m "not flaky"         # 安定したテストのみ
pytest -m "not experimental"  # 実験的でないテストのみ

# 依存関係での実行
pytest -m "not network_required"  # ネットワーク不要なテスト
pytest -m "not db_required"       # DB不要なテスト

# カスタムタグ
pytest -m "smoke"            # スモークテストのみ
pytest -m "nightly"          # ナイトリービルド用テスト
pytest -m "smoke and fast"   # 高速なスモークテスト
"""