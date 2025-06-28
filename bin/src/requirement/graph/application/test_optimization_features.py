"""
Tests for Optimization Features
"""
from .optimization_features import (
    optimize_implementation_order_with_layers,
    find_critical_path,
    calculate_foundation_priority
)


def test_optimize_implementation_order_レイヤー順序_正しく並ぶ():
    """optimize_implementation_order_with_layers_DB→API→UI_正しい順序"""
    requirements = [
        {"id": "ui", "title": "UI"},
        {"id": "api", "title": "API"},
        {"id": "db", "title": "DB"}
    ]
    code_entities = [
        {"persistent_id": "ui_code", "type": "ui"},
        {"persistent_id": "api_code", "type": "api"},
        {"persistent_id": "db_code", "type": "database"}
    ]
    implementation_relations = [
        ("ui", "ui_code", "direct"),
        ("api", "api_code", "direct"),
        ("db", "db_code", "direct")
    ]
    dependencies = [
        ("ui", "api", "technical"),
        ("api", "db", "technical")
    ]
    
    result = optimize_implementation_order_with_layers(
        requirements, code_entities, implementation_relations, dependencies
    )
    
    assert result == ["db", "api", "ui"]


def test_find_critical_path_ダイヤモンド_最長パス():
    """find_critical_path_ダイヤモンド依存_最長パスを返す"""
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": [],
    }
    
    path = find_critical_path(graph)
    
    assert len(path) == 3
    assert path[0] == "A"
    assert path[-1] == "D"


def test_calculate_foundation_priority_共通基盤_高スコア():
    """calculate_foundation_priority_複数依存_高優先度"""
    requirements = [
        {"id": "A", "title": "A"},
        {"id": "B", "title": "B"},
        {"id": "common", "title": "Common"}
    ]
    dependencies = [
        ("A", "common"),
        ("B", "common")
    ]
    
    scores = calculate_foundation_priority(requirements, dependencies)
    
    assert scores["common"] > scores["A"]
    assert scores["common"] > scores["B"]