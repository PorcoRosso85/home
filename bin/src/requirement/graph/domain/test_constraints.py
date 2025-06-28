"""
Tests for Constraints
"""
from typing import Dict, Any
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