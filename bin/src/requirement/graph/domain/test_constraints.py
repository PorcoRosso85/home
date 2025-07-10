"""
Tests for Constraints
"""
from .constraints import (
    validate_no_circular_dependency,
    validate_max_depth,
    validate_implementation_completeness
)


def test_validate_no_circular_dependency_with_cycle_returns_error():
    """validate_no_circular_dependency_循環あり_エラーを返す"""
    all_deps = {
        "A": ["B"],
        "B": ["C"],
        "C": []  # 現在Cに依存なし
    }

    # C -> A の依存を追加すると C->A->B->C の循環が発生
    result = validate_no_circular_dependency("C", ["A"], all_deps)

    # デバッグ出力
    print(f"Result: {result}")
    print(f"Result type: {type(result)}")
    if not isinstance(result, dict):
        print(f"ERROR: Expected dict but got {type(result)}")

        # 手動で循環チェック
        temp_deps = all_deps.copy()
        temp_deps["C"] = ["A"]
        print(f"temp_deps: {temp_deps}")

        # C -> A -> B -> C の経路が存在するはず
        path = ["C"]
        current = "C"
        visited = set()

        for _ in range(4):  # 最大4ステップ
            if current in visited:
                print(f"Already visited {current}")
                break
            visited.add(current)

            next_nodes = temp_deps.get(current, [])
            if next_nodes:
                current = next_nodes[0]
                path.append(current)
                if current == "C" and len(path) > 1:
                    print(f"Found cycle: {' -> '.join(path)}")
                    break
        else:
            print(f"No cycle found, path: {' -> '.join(path)}")

    assert isinstance(result, dict)
    assert result["type"] == "ConstraintViolationError"
    # 循環パスの順序は実装により異なる可能性がある
    assert any("C" in detail and "A" in detail and "B" in detail for detail in result["details"])


def test_validate_no_circular_dependency_without_cycle_returns_true():
    """validate_no_circular_dependency_循環なし_Trueを返す"""
    all_deps = {
        "A": ["B"],
        "B": ["C"],
        "C": []
    }

    # D -> B の依存は循環を作らない
    result = validate_no_circular_dependency("D", ["B"], all_deps)
    assert result == True


def test_validate_max_depth_exceeded_returns_error():
    """validate_max_depth_深さ超過_エラーを返す"""
    hierarchy = {
        "req_004": "req_003",
        "req_003": "req_002",
        "req_002": "req_001",
        "req_001": "req_000"
    }

    # req_005 -> req_004 で深さ5を超える
    result = validate_max_depth("req_005", "req_004", hierarchy, max_depth=5)

    assert isinstance(result, dict)
    assert result["type"] == "ConstraintViolationError"
    assert "Maximum hierarchy depth" in result["message"]


def test_validate_implementation_completeness_partial_returns_status():
    """validate_implementation_completeness_部分実装_ステータスを返す"""
    requirement = {"id": "req_001", "title": "Test"}
    implementations = [
        {"id": "impl_1", "status": "implemented"},
        {"id": "impl_2", "status": "in_progress"},
        {"id": "impl_3", "status": "implemented"}
    ]
    tests = [
        {"id": "test_1", "status": "passed"}
    ]

    result = validate_implementation_completeness(requirement, implementations, tests)

    assert result["total_items"] == 3
    assert result["implemented"] == 2
    assert result["tested"] == 1
    assert result["implementation_rate"] == 2/3
    assert result["test_coverage"] == 0.5
    assert result["is_complete"] == False
    assert "1 implementations pending" in result["missing"]
    assert "1 tests missing" in result["missing"]




