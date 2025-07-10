"""
Version Tracking - 時系列追跡ドメインロジック
外部依存: なし
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime


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
            "path": "/rgl/requirements/req_001",
            "hierarchy": ["rgl", "requirements"],
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


def calculate_requirement_diff(
    old_requirement: Dict,
    new_requirement: Dict
) -> Dict[str, List[Tuple[str, any, any]]]:
    """
    2つの要件間の差分を計算
    
    Args:
        old_requirement: 古い要件データ
        new_requirement: 新しい要件データ
    
    Returns:
        {
            "changed_fields": [("field_name", old_value, new_value), ...]
        }
    """
    changed_fields = []

    # 基本フィールドの比較
    for field in ["title", "description", "priority", "requirement_type", "status"]:
        if old_requirement.get(field) != new_requirement.get(field):
            changed_fields.append((field, old_requirement.get(field), new_requirement.get(field)))

    return {
        "changed_fields": changed_fields
    }


