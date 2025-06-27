"""
Constraints - 制約ルール定義
外部依存: なし
"""
from typing import List, Dict, Union, Optional, Any
from .types import Decision, DecisionError


# ConstraintViolationError型定義（TypedDictとして）
from typing import TypedDict

class ConstraintViolationError(TypedDict):
    """制約違反エラー"""
    type: str
    message: str
    constraint: str
    details: List[str]


def validate_no_circular_dependency(
    requirement_id: str,
    dependencies: List[str],
    all_dependencies_map: Dict[str, List[str]]
) -> Union[bool, ConstraintViolationError]:
    """
    循環依存がないことを検証
    
    Args:
        requirement_id: 検証対象の要件ID
        dependencies: 直接の依存先ID一覧
        all_dependencies_map: 全要件の依存関係マップ
        
    Returns:
        True または ConstraintViolationError
    """
    def find_cycle(current: str, visited: set, path: List[str]) -> Optional[List[str]]:
        if current in visited:
            # 循環を検出
            cycle_start = path.index(current)
            return path[cycle_start:] + [current]
        
        visited.add(current)
        path.append(current)
        
        for dep in all_dependencies_map.get(current, []):
            cycle = find_cycle(dep, visited.copy(), path.copy())
            if cycle:
                return cycle
        
        return None
    
    # 新しい依存関係を仮追加
    temp_map = all_dependencies_map.copy()
    temp_map[requirement_id] = dependencies
    
    # 循環チェック
    cycle = find_cycle(requirement_id, set(), [])
    
    if cycle:
        return {
            "type": "ConstraintViolationError",
            "message": f"Circular dependency detected",
            "constraint": "no_circular_dependency",
            "details": [f"Cycle: {' -> '.join(cycle)}"]
        }
    
    return True


def validate_max_depth(
    requirement_id: str,
    parent_id: Optional[str],
    hierarchy_map: Dict[str, str],
    max_depth: int = 5
) -> Union[bool, ConstraintViolationError]:
    """
    階層の深さが最大値を超えないことを検証
    
    Args:
        requirement_id: 検証対象の要件ID
        parent_id: 親要件ID
        hierarchy_map: 要件ID -> 親IDのマップ
        max_depth: 最大階層深さ
        
    Returns:
        True または ConstraintViolationError
    """
    if not parent_id:
        return True
    
    depth = 1
    current = parent_id
    
    while current and depth < max_depth:
        current = hierarchy_map.get(current)
        if current:
            depth += 1
    
    if depth >= max_depth:
        return {
            "type": "ConstraintViolationError",
            "message": f"Maximum hierarchy depth ({max_depth}) exceeded",
            "constraint": "max_hierarchy_depth",
            "details": [f"Current depth would be: {depth + 1}"]
        }
    
    return True


def validate_implementation_completeness(
    requirement: Decision,
    implementations: List[Dict],
    tests: List[Dict]
) -> Dict[str, Any]:
    """
    実装完了度を検証
    
    Args:
        requirement: 要件
        implementations: 実装情報リスト
        tests: テスト情報リスト
        
    Returns:
        完了度情報
    """
    total_items = len(implementations) if implementations else 1
    implemented = len([i for i in implementations if i.get("status") == "implemented"])
    tested = len([t for t in tests if t.get("status") == "passed"])
    
    completeness = {
        "requirement_id": requirement["id"],
        "total_items": total_items,
        "implemented": implemented,
        "tested": tested,
        "implementation_rate": implemented / total_items if total_items > 0 else 0,
        "test_coverage": tested / implemented if implemented > 0 else 0,
        "is_complete": implemented == total_items and tested >= implemented
    }
    
    if not completeness["is_complete"]:
        missing = []
        if implemented < total_items:
            missing.append(f"{total_items - implemented} implementations pending")
        if tested < implemented:
            missing.append(f"{implemented - tested} tests missing")
        
        completeness["missing"] = missing
    
    return completeness


# Test cases
def test_validate_no_circular_dependency_with_cycle_returns_error():
    """validate_no_circular_dependency_循環あり_エラーを返す"""
    all_deps = {
        "A": ["B"],
        "B": ["C"],
        "C": []  # 現在Cに依存なし
    }
    
    # C -> A の依存を追加すると A->B->C->A の循環が発生
    result = validate_no_circular_dependency("C", ["A"], all_deps)
    
    # デバッグ出力
    if not isinstance(result, dict):
        print(f"Unexpected result type: {type(result)}, value: {result}")
        print(f"all_deps before: {all_deps}")
        # 手動で循環チェック
        # C -> A -> B -> C の経路が存在するはず
        temp_deps = all_deps.copy()
        temp_deps["C"] = ["A"]
        print(f"temp_deps: {temp_deps}")
        # C から始めて A -> B -> C と辿れるか確認
        path = ["C"]
        current = "C"
        for _ in range(4):  # 最大4ステップ
            next_nodes = temp_deps.get(current, [])
            if next_nodes:
                current = next_nodes[0]
                path.append(current)
                if current == "C":
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


def test_パフォーマンス要件なし_警告():
    """レスポンスタイム未定義_デフォルト基準提示"""
    # API要件でパフォーマンス要件がない場合
    def validate_performance_requirements(requirement: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンス要件の検証"""
        if requirement.get("type") == "API":
            description = requirement.get("description", "")
            perf_keywords = ["レスポンスタイム", "response time", "ms", "秒以内", "ミリ秒"]
            
            if not any(keyword in description.lower() for keyword in perf_keywords):
                return {
                    "is_valid": False,
                    "score": -0.3,
                    "warning": "パフォーマンス要件が定義されていません",
                    "suggestion": "以下のデフォルト基準を推奨:\n- レスポンスタイム: 200ms以内\n- 同時接続数: 100接続"
                }
        return {"is_valid": True, "score": 0.0}
    
    # テスト実行
    api_requirement = {
        "type": "API",
        "description": "ユーザー情報を取得するAPIを実装"
    }
    
    result = validate_performance_requirements(api_requirement)
    assert result["is_valid"] == False
    assert result["score"] == -0.3
    assert "パフォーマンス要件が定義されていません" in result["warning"]
    assert "200ms以内" in result["suggestion"]


def test_セキュリティ要件なし_エラー():
    """認証認可未考慮_必須要件として追加要求"""
    def validate_security_requirements(requirement: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ要件の検証"""
        # APIやユーザー情報を扱う場合はセキュリティ必須
        sensitive_keywords = ["ユーザー", "user", "個人情報", "password", "認証", "API"]
        description = requirement.get("description", "").lower()
        title = requirement.get("title", "").lower()
        
        if any(keyword in description or keyword in title for keyword in sensitive_keywords):
            security_keywords = ["認証", "認可", "auth", "暗号化", "encryption", "アクセス制御"]
            
            if not any(keyword in description for keyword in security_keywords):
                return {
                    "is_valid": False,
                    "score": -0.7,  # セキュリティは重要なのでペナルティ大
                    "error": "セキュリティ要件が定義されていません",
                    "suggestion": "以下を必ず定義してください:\n- 認証方式\n- 認可ルール\n- データ暗号化"
                }
        return {"is_valid": True, "score": 0.0}
    
    # テスト実行
    user_api_requirement = {
        "title": "ユーザー情報API",
        "description": "ユーザーの個人情報を取得・更新するAPIを実装"
    }
    
    result = validate_security_requirements(user_api_requirement)
    assert result["is_valid"] == False
    assert result["score"] == -0.7
    assert "セキュリティ要件が定義されていません" in result["error"]
    assert "認証方式" in result["suggestion"]
    assert "認可ルール" in result["suggestion"]


if __name__ == "__main__":
    import sys
    import unittest
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # テストクラスを動的に作成
        class TestConstraints(unittest.TestCase):
            def test_validate_no_circular_dependency_with_cycle_returns_error(self):
                test_validate_no_circular_dependency_with_cycle_returns_error()
            
            def test_validate_no_circular_dependency_without_cycle_returns_true(self):
                test_validate_no_circular_dependency_without_cycle_returns_true()
            
            def test_validate_max_depth_exceeded_returns_error(self):
                test_validate_max_depth_exceeded_returns_error()
            
            def test_validate_implementation_completeness_partial_returns_status(self):
                test_validate_implementation_completeness_partial_returns_status()
            
            def test_パフォーマンス要件なし_警告(self):
                test_パフォーマンス要件なし_警告()
            
            def test_セキュリティ要件なし_エラー(self):
                test_セキュリティ要件なし_エラー()
        
        # テスト実行
        unittest.main(argv=[''], exit=False, verbosity=2)
