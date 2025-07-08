"""
要件矛盾検出ルールのテスト
規約準拠：クラスを使わず、関数でテストを実装
"""
# import pytest  # pytestはnix run .#testで実行時に利用可能
from typing import Dict, Any
try:
    from .requirement_conflict_rules import (
        detect_numeric_threshold_conflicts,
        detect_temporal_conflicts,
        detect_exclusive_conflicts,
        detect_quality_conflicts,
        detect_all_conflicts,
        suggest_conflict_resolution,
        ConflictDetectionResult
    )
except ImportError:
    # 直接実行時
    from requirement_conflict_rules import (
        detect_numeric_threshold_conflicts,
        detect_temporal_conflicts,
        detect_exclusive_conflicts,
        detect_quality_conflicts,
        detect_all_conflicts,
        suggest_conflict_resolution,
        ConflictDetectionResult
    )


# テストデータ生成関数
def create_requirement(
    id: str,
    title: str = "Test Requirement",
    priority: int = 100,
    requirement_type: str = "functional",
    **kwargs
) -> Dict[str, Any]:
    """テスト用要件データを生成"""
    req = {
        "id": id,
        "title": title,
        "priority": priority,
        "requirement_type": requirement_type
    }
    req.update(kwargs)
    return req


# 数値的矛盾のテスト（TDT）
def test_numeric_threshold_conflicts_with_various_ratios():
    """様々な閾値での数値的矛盾検出"""
    test_cases = [
        # (requirements, threshold_ratio, expected_conflict)
        (
            # デフォルト閾値（2.0）でのテスト
            [
                create_requirement("REQ1", priority=250, 
                    numeric_constraints={"metric": "latency", "operator": "<", "value": 100, "unit": "ms"}),
                create_requirement("REQ2", priority=200,
                    numeric_constraints={"metric": "latency", "operator": "<", "value": 500, "unit": "ms"})
            ],
            2.0,
            True  # 5倍の差
        ),
        (
            # カスタム閾値（3.0）でのテスト
            [
                create_requirement("REQ3", numeric_constraints={"metric": "throughput", "operator": ">", "value": 1000, "unit": "req/s"}),
                create_requirement("REQ4", numeric_constraints={"metric": "throughput", "operator": ">", "value": 2500, "unit": "req/s"})
            ],
            3.0,
            False  # 2.5倍は3.0未満
        ),
        (
            # 同じ値なら矛盾なし
            [
                create_requirement("REQ5", numeric_constraints={"metric": "cpu", "operator": "<", "value": 80, "unit": "%"}),
                create_requirement("REQ6", numeric_constraints={"metric": "cpu", "operator": "<", "value": 80, "unit": "%"})
            ],
            2.0,
            False
        )
    ]
    
    for requirements, threshold, expected in test_cases:
        result = detect_numeric_threshold_conflicts(requirements, threshold)
        assert result["has_conflict"] == expected, f"Failed for threshold {threshold}"
        if expected:
            assert len(result["conflicts"]) > 0
            assert len(result["rule_violations"]) > 0


# 時間的矛盾のテスト
def test_temporal_conflicts_immediate_vs_longterm():
    """即時実装と長期計画の矛盾"""
    requirements = [
        create_requirement("TEMP1", 
            temporal_constraint={"timeline": "immediate", "duration": 0}),
        create_requirement("TEMP2",
            temporal_constraint={"timeline": "months", "duration": 6}),
        create_requirement("TEMP3",
            temporal_constraint={"timeline": "days", "duration": 7})
    ]
    
    result = detect_temporal_conflicts(requirements)
    
    assert result["has_conflict"] is True
    assert len(result["conflicts"]) == 1  # immediate vs months
    assert "immediate vs 6 months" in result["rule_violations"][0]


# 排他的選択のテスト
def test_exclusive_conflicts_deployment_choices():
    """デプロイメント選択の矛盾"""
    requirements = [
        create_requirement("EXC1",
            exclusive_constraint={"category": "deployment", "value": "cloud-only"}),
        create_requirement("EXC2",
            exclusive_constraint={"category": "deployment", "value": "on-premise"}),
        create_requirement("EXC3",
            exclusive_constraint={"category": "architecture", "value": "microservices"})
    ]
    
    result = detect_exclusive_conflicts(requirements)
    
    assert result["has_conflict"] is True
    conflicts = result["conflicts"]
    assert len(conflicts) == 1
    assert conflicts[0]["category"] == "deployment"
    assert set(conflicts[0]["values"]) == {"cloud-only", "on-premise"}


# 品質トレードオフのテスト
def test_quality_conflicts_performance_vs_security():
    """性能とセキュリティのトレードオフ"""
    requirements = [
        create_requirement("QUAL1",
            quality_attributes=["performance", "scalability"]),
        create_requirement("QUAL2",
            quality_attributes=["security", "reliability"]),
        create_requirement("QUAL3",
            quality_attributes=["usability"])
    ]
    
    result = detect_quality_conflicts(requirements)
    
    assert result["has_conflict"] is True
    assert any("performance vs security" in v for v in result["rule_violations"])


# 統合テスト（複数の矛盾タイプ）
def test_detect_all_conflicts_integration():
    """すべての矛盾タイプを統合的に検出"""
    requirements = [
        # 数値的矛盾
        create_requirement("INT1", priority=300,
            numeric_constraints={"metric": "response_time", "operator": "<", "value": 1, "unit": "s"}),
        create_requirement("INT2", priority=250,
            numeric_constraints={"metric": "response_time", "operator": "<", "value": 5, "unit": "s"}),
        # 時間的矛盾
        create_requirement("INT3",
            temporal_constraint={"timeline": "immediate", "duration": 0}),
        create_requirement("INT4",
            temporal_constraint={"timeline": "years", "duration": 2}),
        # 排他的選択
        create_requirement("INT5",
            exclusive_constraint={"category": "payment", "value": "free"}),
        create_requirement("INT6",
            exclusive_constraint={"category": "payment", "value": "subscription"})
    ]
    
    # カスタム設定でテスト
    config = {"numeric_threshold_ratio": 3.0}
    results = detect_all_conflicts(requirements, config=config)
    
    assert "numeric_threshold" in results
    assert results["numeric_threshold"]["has_conflict"] is True  # 5倍 > 3倍
    
    assert "temporal_incompatibility" in results
    assert results["temporal_incompatibility"]["has_conflict"] is True
    
    assert "exclusive_choice" in results
    assert results["exclusive_choice"]["has_conflict"] is True


# 矛盾解決提案のテスト
def test_conflict_resolution_suggestions():
    """矛盾タイプ別の解決提案"""
    test_cases = [
        ("numeric", {"ratio": 5.0, "values": [1, 5]}, ["中間値", "優先度", "段階的"]),
        ("temporal", {}, ["フェーズド", "MVP", "並行開発"]),
        ("exclusive", {}, ["ハイブリッド", "コンテキスト別", "移行パス"]),
        ("quality", {}, ["優先順位付け", "アーキテクチャ", "品質シナリオ"])
    ]
    
    for conflict_type, details, expected_keywords in test_cases:
        suggestions = suggest_conflict_resolution(conflict_type, details)
        assert len(suggestions) > 0
        assert any(keyword in " ".join(suggestions) for keyword in expected_keywords)


# プロパティベーステスト（概念的な実装）
def test_conflict_detection_properties():
    """矛盾検出の不変条件"""
    # 性質1: 空の要件リストは矛盾なし
    empty_result = detect_numeric_threshold_conflicts([])
    assert empty_result["has_conflict"] is False
    
    # 性質2: 1つの要件は矛盾なし
    single_req = [create_requirement("SINGLE", 
        numeric_constraints={"metric": "test", "operator": "=", "value": 100, "unit": "ms"})]
    single_result = detect_numeric_threshold_conflicts(single_req)
    assert single_result["has_conflict"] is False
    
    # 性質3: 矛盾検出は決定的（同じ入力で同じ出力）
    requirements = [
        create_requirement("PROP1", numeric_constraints={"metric": "test", "operator": "<", "value": 10, "unit": "s"}),
        create_requirement("PROP2", numeric_constraints={"metric": "test", "operator": "<", "value": 50, "unit": "s"})
    ]
    result1 = detect_numeric_threshold_conflicts(requirements)
    result2 = detect_numeric_threshold_conflicts(requirements)
    assert result1 == result2


# エッジケースのテスト
def test_edge_cases_null_and_missing_constraints():
    """制約が欠落している場合の処理"""
    requirements = [
        create_requirement("EDGE1"),  # 制約なし
        create_requirement("EDGE2", numeric_constraints=None),  # 明示的にNone
        create_requirement("EDGE3", numeric_constraints={"metric": "test", "operator": "=", "value": 100, "unit": "ms"})
    ]
    
    # エラーではなく、制約なしの要件を無視して処理
    result = detect_numeric_threshold_conflicts(requirements)
    assert result["has_conflict"] is False  # 1つしか制約がないので矛盾なし


if __name__ == "__main__":
    # 各テストを実行
    print("Running numeric threshold tests...")
    test_numeric_threshold_conflicts_with_various_ratios()
    print("✅ Numeric threshold tests passed")
    
    print("Running temporal conflict tests...")
    test_temporal_conflicts_immediate_vs_longterm()
    print("✅ Temporal conflict tests passed")
    
    print("Running exclusive conflict tests...")
    test_exclusive_conflicts_deployment_choices()
    print("✅ Exclusive conflict tests passed")
    
    print("Running quality conflict tests...")
    test_quality_conflicts_performance_vs_security()
    print("✅ Quality conflict tests passed")
    
    print("Running integration tests...")
    test_detect_all_conflicts_integration()
    print("✅ Integration tests passed")
    
    print("Running resolution suggestion tests...")
    test_conflict_resolution_suggestions()
    print("✅ Resolution suggestion tests passed")
    
    print("Running property tests...")
    test_conflict_detection_properties()
    print("✅ Property tests passed")
    
    print("Running edge case tests...")
    test_edge_cases_null_and_missing_constraints()
    print("✅ Edge case tests passed")
    
    print("\n🎉 All tests passed!")