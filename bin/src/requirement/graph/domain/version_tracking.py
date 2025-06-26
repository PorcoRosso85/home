"""
Version Tracking - 時系列追跡ドメインロジック
外部依存: なし
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .types import Decision, DecisionResult


def create_version_id(requirement_id: str, timestamp: Optional[datetime] = None) -> str:
    """
    バージョンIDを生成
    フォーマット: v_{timestamp}_{requirement_id}
    """
    if not timestamp:
        timestamp = datetime.now()
    return f"v_{timestamp.isoformat()}_{requirement_id}"


def create_location_uri(requirement_id: str) -> str:
    """
    LocationURIを生成
    階層はRELATIONとEntityAggregationViewで管理されるため、
    シンプルなURIフォーマットを使用
    
    例:
    - "req://rgl/requirements/{id}"
    """
    return f"req://rgl/requirements/{requirement_id}"


def parse_location_uri(uri: str) -> Dict[str, str]:
    """
    LocationURIをパース
    
    Returns:
        {
            "scheme": "req",
            "path": "/L0/vision/req_001",
            "hierarchy": ["L0", "vision"],
            "id": "req_001"
        }
    """
    if not uri.startswith("req://"):
        return {"error": "Invalid URI scheme"}
    
    path = uri[6:]  # "req://"を除去
    parts = path.split("/")
    
    return {
        "scheme": "req",
        "path": "/" + path,
        "hierarchy": parts[:-1] if len(parts) > 1 else [],
        "id": parts[-1] if parts else ""
    }


def create_requirement_snapshot(
    requirement: Decision,
    version_id: str,
    operation: str = "CREATE"
) -> Dict:
    """
    要件のスナップショットを作成
    
    Args:
        requirement: 要件データ
        version_id: バージョンID
        operation: "CREATE", "UPDATE", "DELETE"
    """
    snapshot_id = f"{requirement['id']}@{version_id}"
    
    return {
        "snapshot_id": snapshot_id,
        "requirement_id": requirement["id"],
        "version_id": version_id,
        "title": requirement["title"],
        "description": requirement["description"],
        "priority": requirement.get("priority", "medium"),
        "requirement_type": requirement.get("requirement_type", "functional"),
        "status": requirement["status"],
        "embedding": requirement["embedding"],
        "created_at": requirement["created_at"].isoformat(),
        "snapshot_at": datetime.now().isoformat(),
        "is_deleted": operation == "DELETE"
    }


def calculate_requirement_diff(
    old_snapshot: Dict,
    new_snapshot: Dict
) -> Dict[str, List[Tuple[str, any, any]]]:
    """
    2つのスナップショット間の差分を計算
    
    Returns:
        {
            "changed_fields": [("field_name", old_value, new_value), ...]
        }
    """
    changed_fields = []
    
    # 基本フィールドの比較
    for field in ["title", "description", "priority", "requirement_type", "status"]:
        if old_snapshot.get(field) != new_snapshot.get(field):
            changed_fields.append((field, old_snapshot.get(field), new_snapshot.get(field)))
    
    return {
        "changed_fields": changed_fields
    }


# Test cases (in-source test)
def test_create_version_id_generates_unique_id():
    """create_version_id_一意のID_生成される"""
    import time
    
    id1 = create_version_id("req_001")
    time.sleep(0.001)  # 少し待つ
    id2 = create_version_id("req_001")
    
    assert id1 != id2
    assert "req_001" in id1
    assert "req_001" in id2


def test_create_location_uri_generates_standard_uri():
    """create_location_uri_標準URI_生成される"""
    uri = create_location_uri("req_001")
    assert uri == "req://rgl/requirements/req_001"
    
    uri2 = create_location_uri("req_002")
    assert uri2 == "req://rgl/requirements/req_002"


def test_parse_location_uri_extracts_components():
    """parse_location_uri_URI解析_コンポーネント抽出"""
    result = parse_location_uri("req://rgl/requirements/req_001")
    
    assert result["scheme"] == "req"
    assert result["path"] == "/rgl/requirements/req_001"
    assert result["hierarchy"] == ["rgl", "requirements"]
    assert result["id"] == "req_001"


def test_calculate_requirement_diff_detects_changes():
    """calculate_requirement_diff_変更検出_差分を返す"""
    old = {
        "title": "Old Title",
        "description": "Old desc",
        "status": "proposed"
    }
    
    new = {
        "title": "New Title",
        "description": "Old desc",  # 変更なし
        "status": "approved"
    }
    
    diff = calculate_requirement_diff(old, new)
    
    assert len(diff["changed_fields"]) == 2
    assert ("title", "Old Title", "New Title") in diff["changed_fields"]
    assert ("status", "proposed", "approved") in diff["changed_fields"]
