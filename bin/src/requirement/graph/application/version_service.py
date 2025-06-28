"""
Version Service - バージョン管理ユースケース
依存: domain層のみ
外部依存: なし
"""
import json
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime
from ..domain.types import Decision, DecisionResult
from ..domain.version_tracking import (
    create_version_id,
    create_location_uri,
    parse_location_uri,
    calculate_requirement_diff
)


# Repository型定義（依存性注入用）
VersionRepository = Dict[str, Callable]


def create_version_service(repository: VersionRepository):
    """
    VersionServiceを作成（依存性注入）
    
    Args:
        repository: execute, save_requirement, find_requirement メソッドを持つ辞書
    
    Returns:
        VersionService関数の辞書
    """
    
    def track_requirement_change(
        requirement_id: str,
        operation: str = "UPDATE",
        author: str = "system",
        reason: Optional[str] = None
    ) -> Dict:
        """
        要件の変更を追跡
        
        Args:
            requirement_id: 要件ID
            operation: "CREATE", "UPDATE", "DELETE"
            author: 変更者
            reason: 変更理由
            
        Returns:
            {"version_id": str, "snapshot_id": str, "status": "tracked"}
        """
        # 現在の要件を取得
        req_result = repository["find_requirement"](requirement_id)
        if "type" in req_result and "Error" in req_result["type"]:
            return {"error": f"Requirement {requirement_id} not found"}
        
        requirement = req_result
        
        # バージョンIDを生成
        version_id = create_version_id(requirement_id)
        
        # LocationURIを生成または取得
        location_uri = create_location_uri(requirement_id)
        
        # LocationURIノードを作成
        repository["execute"]("""
            MERGE (l:LocationURI {id: $uri})
            RETURN l
        """, {"uri": location_uri})
        
        # 要件とLocationURIを関連付け
        repository["execute"]("""
            MATCH (l:LocationURI {id: $uri}), (r:RequirementEntity {id: $req_id})
            MERGE (l)-[:LOCATES {entity_type: 'requirement'}]->(r)
        """, {"uri": location_uri, "req_id": requirement_id})
        
        # 変更フィールドを検出
        changed_fields = []
        if operation == "UPDATE":
            # 以前のバージョンと比較して変更フィールドを検出
            # 簡易実装：ここでは空リストとする
            # 実際には以前の状態を取得して比較する必要がある
            pass
        
        # VersionStateを作成
        repository["execute"]("""
            CREATE (v:VersionState {
                id: $version_id,
                timestamp: $timestamp,
                description: $description,
                change_reason: $reason,
                operation: $operation,
                author: $author,
                changed_fields: $changed_fields,
                progress_percentage: 0.0
            })
            RETURN v
        """, {
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "description": f"{operation} requirement {requirement_id}",
            "reason": reason or operation,
            "operation": operation,
            "author": author,
            "changed_fields": json.dumps(changed_fields) if changed_fields else None
        })
        
        # 要件とバージョンの関係を作成
        repository["execute"]("""
            MATCH (r:RequirementEntity {id: $req_id}), (v:VersionState {id: $ver_id})
            CREATE (r)-[:HAS_VERSION]->(v)
        """, {"req_id": requirement_id, "ver_id": version_id})
        
        # 前のバージョンとの関係を作成
        repository["execute"]("""
            MATCH (v_new:VersionState {id: $new_version}),
                  (v_old:VersionState)<-[:HAS_VERSION]-(r:RequirementEntity {id: $req_id})
            WHERE v_old.id <> $new_version
            WITH v_new, v_old
            ORDER BY v_old.timestamp DESC
            LIMIT 1
            CREATE (v_new)-[:FOLLOWS]->(v_old)
        """, {"new_version": version_id, "req_id": requirement_id})
        
        # バージョンと位置の関係を作成
        repository["execute"]("""
            MATCH (v:VersionState {id: $version_id}), (l:LocationURI {id: $uri})
            CREATE (v)-[:TRACKS_STATE_OF {entity_type: 'requirement'}]->(l)
        """, {"version_id": version_id, "uri": location_uri})
        
        return {
            "version_id": version_id,
            "location_uri": location_uri,
            "status": "tracked"
        }
    
    def get_requirement_history(requirement_id: str, limit: int = 10) -> List[Dict]:
        """
        要件の変更履歴を取得
        
        Args:
            requirement_id: 要件ID
            limit: 取得する履歴の最大数
            
        Returns:
            変更履歴のリスト
        """
        result = repository["execute"]("""
            MATCH (r:RequirementEntity {id: $req_id})-[:HAS_VERSION]->(v:VersionState)
            RETURN r, v
            ORDER BY v.timestamp DESC
            LIMIT $limit
        """, {"req_id": requirement_id, "limit": limit})
        
        history = []
        while result.has_next():
            requirement, version = result.get_next()
            history.append({
                "version_id": version["id"],
                "timestamp": version["timestamp"],
                "author": version.get("author", "system"),
                "change_reason": version.get("change_reason", ""),
                "operation": version.get("operation", "UPDATE"),
                "changed_fields": json.loads(version.get("changed_fields", "[]")) if version.get("changed_fields") else [],
                "requirement_state": {
                    "id": requirement["id"],
                    "title": requirement["title"],
                    "description": requirement["description"],
                    "status": requirement.get("status", "proposed"),
                    "priority": requirement.get("priority", "medium")
                }
            })
        
        return history
    
    def get_requirement_at_version(requirement_id: str, timestamp: str) -> Optional[Dict]:
        """
        特定時点での要件状態を取得
        
        Args:
            requirement_id: 要件ID
            timestamp: 対象時刻（ISO形式）
            
        Returns:
            その時点での要件状態、見つからない場合はNone
        """
        # 指定時刻以前の最新バージョンを取得
        result = repository["execute"]("""
            MATCH (r:RequirementEntity {id: $req_id})-[:HAS_VERSION]->(v:VersionState)
            WHERE v.timestamp <= $target_time
            RETURN r, v
            ORDER BY v.timestamp DESC
            LIMIT 1
        """, {"req_id": requirement_id, "target_time": timestamp})
        
        if result.has_next():
            requirement, version = result.get_next()
            return {
                "id": requirement["id"],
                "title": requirement["title"],
                "description": requirement["description"],
                "status": requirement.get("status", "proposed"),
                "priority": requirement.get("priority", "medium"),
                "requirement_type": requirement.get("requirement_type", "functional"),
                "version_info": {
                    "version_id": version["id"],
                    "timestamp": version["timestamp"],
                    "operation": version.get("operation", "UPDATE")
                }
            }
        
        return None
    
    def calculate_version_diff(requirement_id: str, version1_id: str, version2_id: str) -> Dict:
        """
        2つのバージョン間の差分を計算
        
        Args:
            requirement_id: 要件ID
            version1_id: 比較元バージョンID
            version2_id: 比較先バージョンID
            
        Returns:
            差分情報
        """
        # 両方のバージョン時点の要件を取得
        result1 = repository["execute"]("""
            MATCH (v:VersionState {id: $ver_id})
            RETURN v.timestamp as timestamp
        """, {"ver_id": version1_id})
        
        result2 = repository["execute"]("""
            MATCH (v:VersionState {id: $ver_id})
            RETURN v.timestamp as timestamp
        """, {"ver_id": version2_id})
        
        if not result1.has_next() or not result2.has_next():
            return {"error": "Versions not found"}
        
        timestamp1 = result1.get_next()[0]
        timestamp2 = result2.get_next()[0]
        
        # 各タイムスタンプ時点の要件状態を取得
        req1 = get_requirement_at_version(requirement_id, timestamp1)
        req2 = get_requirement_at_version(requirement_id, timestamp2)
        
        if not req1 or not req2:
            return {"error": "Requirement states not found"}
        
        return calculate_requirement_diff(req1, req2)
    
    return {
        "track_requirement_change": track_requirement_change,
        "get_requirement_history": get_requirement_history,
        "get_requirement_at_version": get_requirement_at_version,
        "calculate_version_diff": calculate_version_diff
    }


