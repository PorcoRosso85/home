"""
ResourceConflictDetector - リソース競合検出
依存: なし
外部依存: なし

要件間のリソース競合（容量超過など）を検出
"""
from typing import List, Dict, Any, TypedDict


class ResourceConflict(TypedDict):
    """リソース競合の情報"""
    type: str
    resource: str
    total_requested: int
    available: int
    shortage: int


class ResourceConflictDetector:
    """要件間のリソース競合を検出"""
    
    def detect_resource_conflicts(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        要件リストからリソース競合を検出
        
        Args:
            requirements: 要件のリスト
            
        Returns:
            検出された競合のリスト
            
        Example:
            >>> detector = ResourceConflictDetector()
            >>> reqs = [
            ...     {"ID": "req1", "Metadata": {"resource_type": "db_connection", "required": 80}},
            ...     {"ID": "req2", "Metadata": {"resource_type": "db_connection", "required": 60}},
            ...     {"ID": "constraint", "Metadata": {"constraint_type": "resource_limit", "resource": "db_connection", "max": 100}}
            ... ]
            >>> conflicts = detector.detect_resource_conflicts(reqs)
            >>> len(conflicts) > 0
            True
        """
        conflicts = []
        
        # リソース制約を抽出
        resource_limits = self._extract_resource_limits(requirements)
        
        # リソース要求を集計
        resource_requests = self._aggregate_resource_requests(requirements)
        
        # 各リソースタイプで競合をチェック
        for resource_type, total_requested in resource_requests.items():
            limit = resource_limits.get(resource_type)
            
            if limit is not None and total_requested > limit:
                conflicts.append({
                    "type": "resource_overallocation",
                    "resource": resource_type,
                    "total_requested": total_requested,
                    "available": limit,
                    "shortage": total_requested - limit
                })
        
        return conflicts
    
    def _extract_resource_limits(self, requirements: List[Dict[str, Any]]) -> Dict[str, int]:
        """制約から利用可能なリソース上限を抽出"""
        limits = {}
        
        for req in requirements:
            metadata = req.get("Metadata", {})
            
            if metadata.get("constraint_type") == "resource_limit":
                resource = metadata.get("resource")
                max_value = metadata.get("max")
                
                if resource and max_value is not None:
                    limits[resource] = max_value
        
        return limits
    
    def _aggregate_resource_requests(self, requirements: List[Dict[str, Any]]) -> Dict[str, int]:
        """リソース要求を集計"""
        requests = {}
        
        for req in requirements:
            metadata = req.get("Metadata", {})
            resource_type = metadata.get("resource_type")
            required = metadata.get("required")
            
            if resource_type and required is not None:
                if resource_type not in requests:
                    requests[resource_type] = 0
                requests[resource_type] += required
        
        return requests


# In-source tests
def test_resource_conflict_detector_overallocation():
    """リソース超過割り当てを検出"""
    detector = ResourceConflictDetector()
    
    requirements = [
        {
            "ID": "resource_db_service_a",
            "Metadata": {"resource_type": "db_connection", "required": 80, "service": "service_a"}
        },
        {
            "ID": "resource_db_service_b",
            "Metadata": {"resource_type": "db_connection", "required": 60, "service": "service_b"}
        },
        {
            "ID": "constraint_db_max",
            "Metadata": {"constraint_type": "resource_limit", "resource": "db_connection", "max": 100}
        }
    ]
    
    conflicts = detector.detect_resource_conflicts(requirements)
    
    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "resource_overallocation"
    assert conflicts[0]["resource"] == "db_connection"
    assert conflicts[0]["total_requested"] == 140
    assert conflicts[0]["available"] == 100
    assert conflicts[0]["shortage"] == 40


def test_resource_conflict_detector_no_conflicts():
    """競合がない場合は空リストを返す"""
    detector = ResourceConflictDetector()
    
    requirements = [
        {
            "ID": "resource_db_service_a",
            "Metadata": {"resource_type": "db_connection", "required": 50}
        },
        {
            "ID": "resource_db_service_b",
            "Metadata": {"resource_type": "db_connection", "required": 40}
        },
        {
            "ID": "constraint_db_max",
            "Metadata": {"constraint_type": "resource_limit", "resource": "db_connection", "max": 100}
        }
    ]
    
    conflicts = detector.detect_resource_conflicts(requirements)
    assert len(conflicts) == 0


def test_resource_conflict_detector_multiple_resources():
    """複数リソースタイプでの競合検出"""
    detector = ResourceConflictDetector()
    
    requirements = [
        # DBコネクション
        {
            "ID": "req1",
            "Metadata": {"resource_type": "db_connection", "required": 80}
        },
        {
            "ID": "req2",
            "Metadata": {"resource_type": "db_connection", "required": 60}
        },
        {
            "ID": "constraint_db",
            "Metadata": {"constraint_type": "resource_limit", "resource": "db_connection", "max": 100}
        },
        # メモリ
        {
            "ID": "req3",
            "Metadata": {"resource_type": "memory_gb", "required": 16}
        },
        {
            "ID": "req4",
            "Metadata": {"resource_type": "memory_gb", "required": 32}
        },
        {
            "ID": "constraint_memory",
            "Metadata": {"constraint_type": "resource_limit", "resource": "memory_gb", "max": 64}
        }
    ]
    
    conflicts = detector.detect_resource_conflicts(requirements)
    
    # DBコネクションのみが競合
    assert len(conflicts) == 1
    assert conflicts[0]["resource"] == "db_connection"