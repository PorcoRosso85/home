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


