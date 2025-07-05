"""
Version Service - バージョン管理ユースケース
依存: domain層のみ
外部依存: なし
"""
import json
from typing import Dict, List, Optional, Callable, Tuple, Any
from datetime import datetime
from pathlib import Path


# Repository型定義（依存性注入用）
VersionRepository = Dict[str, Callable]


def load_template(category: str, name: str) -> str:
    """Cypherテンプレートを読み込む"""
    template_path = Path(__file__).parent.parent / "query" / category / f"{name}.cypher"
    if template_path.exists():
        return template_path.read_text()
    else:
        raise FileNotFoundError(f"Template not found: {template_path}")


def create_version_service(repository: VersionRepository):
    """
    VersionServiceを作成（依存性注入）
    
    Args:
        repository: execute, save_requirement, find_requirement メソッドを持つ辞書
    
    Returns:
        VersionService関数の辞書
    """
    
    def create_versioned_requirement(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        バージョン付きで新規要件を作成
        
        Args:
            data: 要件データ（id, title, description必須）
            
        Returns:
            作成結果（entity_id, version_id, location_uri, version）
        """
        template = load_template("dml", "create_versioned_requirement")
        
        params = {
            "req_id": data["id"],
            "title": data["title"],
            "description": data.get("description", ""),
            "status": data.get("status", "draft"),
            "priority": data.get("priority", 1),
            "author": data.get("author", "system"),
            "reason": data.get("reason", "Initial creation"),
            "timestamp": datetime.now().isoformat()
        }
        
        result = repository["execute"](template, params)
        if result.has_next():
            row = result.get_next()
            return {
                "entity_id": row[0],
                "version_id": row[1],
                "location_uri": row[2],
                "version": 1,
                "created_at": datetime.now().isoformat(),
                "author": params["author"]
            }
        else:
            raise RuntimeError("Failed to create versioned requirement")
    
    def update_versioned_requirement(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        既存要件を更新（新バージョン作成）
        
        Args:
            data: 更新データ（id必須、変更したいフィールドのみ）
            
        Returns:
            更新結果（entity_id, version_id, version, previous_version）
        """
        template = load_template("dml", "update_versioned_requirement")
        
        params = {
            "req_id": data["id"],
            "title": data.get("title"),
            "description": data.get("description"),
            "status": data.get("status"),
            "priority": data.get("priority"),
            "author": data.get("author", "system"),
            "reason": data.get("reason", "Update"),
            "timestamp": datetime.now().isoformat()
        }
        
        result = repository["execute"](template, params)
        if result.has_next():
            row = result.get_next()
            
            # 現在のバージョンを取得
            version_query = """
            MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
            MATCH (l)-[:LOCATES]->(r:RequirementEntity)
            MATCH (r)-[:HAS_VERSION]->(v:VersionState)
            RETURN count(v) as version_count
            """
            version_result = repository["execute"](version_query, {"req_id": data["id"]})
            version_count = version_result.get_next()[0] if version_result.has_next() else 2
            
            return {
                "entity_id": row[0],
                "version_id": row[1],
                "version": version_count,
                "previous_version": version_count - 1,
                "updated_at": datetime.now().isoformat(),
                "author": params["author"],
                "change_reason": params["reason"]
            }
        else:
            raise RuntimeError("Failed to update versioned requirement")
    
    def get_requirement_history(req_id: str) -> List[Dict[str, Any]]:
        """
        要件の変更履歴を取得
        
        Args:
            req_id: 要件ID
            
        Returns:
            バージョン履歴のリスト
        """
        # テンプレートを使用
        template = load_template("dql", "get_requirement_history")
        
        result = repository["execute"](template, {"req_id": req_id})
        history = []
        version_num = 1
        
        while result.has_next():
            row = result.get_next()
            history.append({
                "version": version_num,
                "entity_id": row[0],
                "version_id": row[5],
                "title": row[1],
                "description": row[2],
                "status": row[3],
                "priority": row[4],
                "operation": row[6],
                "author": row[7],
                "change_reason": row[8],
                "timestamp": row[9]
            })
            version_num += 1
        
        return history
    
    def get_requirement_at_timestamp(req_id: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """
        特定時点の要件状態を取得
        
        Args:
            req_id: 要件ID
            timestamp: ISO形式のタイムスタンプ
            
        Returns:
            その時点の要件状態
        """
        template = load_template("dql", "get_requirement_at_timestamp")
        
        result = repository["execute"](template, {"req_id": req_id, "timestamp": timestamp})
        
        if result.has_next():
            row = result.get_next()
            requirement = row[0]
            version = row[1]
            
            # バージョン番号を計算
            version_query = """
            MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
            MATCH (l)-[:LOCATES]->(r:RequirementEntity)
            MATCH (r)-[:HAS_VERSION]->(v:VersionState)
            WHERE v.timestamp <= $timestamp
            RETURN count(v) as version_count
            """
            version_result = repository["execute"](version_query, {"req_id": req_id, "timestamp": timestamp})
            version_count = version_result.get_next()[0] if version_result.has_next() else 1
            
            return {
                "id": req_id,
                "title": requirement.get("title"),
                "description": requirement.get("description"),
                "status": requirement.get("status"),
                "priority": requirement.get("priority"),
                "version": version_count,
                "timestamp": version.get("timestamp")
            }
        else:
            return None
    
    def get_version_diff(req_id: str, from_version: int, to_version: int) -> Dict[str, Any]:
        """
        バージョン間の差分を取得
        
        Args:
            req_id: 要件ID
            from_version: 比較元バージョン番号
            to_version: 比較先バージョン番号
            
        Returns:
            差分情報
        """
        # 履歴を取得
        history = get_requirement_history(req_id)
        
        if from_version > len(history) or to_version > len(history):
            raise ValueError("Invalid version number")
        
        from_state = history[from_version - 1]
        to_state = history[to_version - 1]
        
        # 変更されたフィールドを検出
        changed_fields = []
        old_values = {}
        new_values = {}
        
        for field in ["title", "description", "status", "priority"]:
            if from_state.get(field) != to_state.get(field):
                changed_fields.append(field)
                old_values[field] = from_state.get(field)
                new_values[field] = to_state.get(field)
        
        return {
            "req_id": req_id,
            "from_version": from_version,
            "to_version": to_version,
            "changed_fields": changed_fields,
            "old_values": old_values,
            "new_values": new_values,
            "change_reason": to_state.get("change_reason"),
            "author": to_state.get("author"),
            "timestamp": to_state.get("timestamp")
        }
    
    return {
        "create_versioned_requirement": create_versioned_requirement,
        "update_versioned_requirement": update_versioned_requirement,
        "get_requirement_history": get_requirement_history,
        "get_requirement_at_timestamp": get_requirement_at_timestamp,
        "get_version_diff": get_version_diff
    }


