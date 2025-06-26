"""
Version Service - バージョン管理ユースケース
依存: domain層のみ
外部依存: なし
"""
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime
from ..domain.types import Decision, DecisionResult
from ..domain.version_tracking import (
    create_version_id,
    create_location_uri,
    parse_location_uri,
    create_requirement_snapshot,
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
        location_uri = create_location_uri(requirement_id, requirement.get("tags", []))
        
        # LocationURIノードを作成
        repository["execute"]("""
            MERGE (l:LocationURI {id: $uri})
            RETURN l
        """, {"uri": location_uri})
        
        # 要件とLocationURIを関連付け
        repository["execute"]("""
            MATCH (l:LocationURI {id: $uri}), (r:RequirementEntity {id: $req_id})
            MERGE (l)-[:LOCATED_WITH_REQUIREMENT {entity_type: 'requirement'}]->(r)
        """, {"uri": location_uri, "req_id": requirement_id})
        
        # VersionStateを作成
        repository["execute"]("""
            CREATE (v:VersionState {
                id: $version_id,
                timestamp: $timestamp,
                description: $description,
                change_reason: $reason,
                author: $author
            })
            RETURN v
        """, {
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "description": f"{operation} requirement {requirement_id}",
            "reason": reason or operation,
            "author": author
        })
        
        # 前のバージョンとの関係を作成
        repository["execute"]("""
            MATCH (v_new:VersionState {id: $new_version}),
                  (v_old:VersionState)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI {id: $uri})
            WHERE v_old.id <> $new_version
            WITH v_new, v_old
            ORDER BY v_old.timestamp DESC
            LIMIT 1
            CREATE (v_new)-[:FOLLOWS]->(v_old)
        """, {"new_version": version_id, "uri": location_uri})
        
        # バージョンと位置の関係を作成
        repository["execute"]("""
            MATCH (v:VersionState {id: $version_id}), (l:LocationURI {id: $uri})
            CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY {operation: $operation}]->(l)
        """, {"version_id": version_id, "uri": location_uri, "operation": operation})
        
        # スナップショットを作成
        snapshot = create_requirement_snapshot(requirement, version_id, operation)
        snapshot_id = snapshot["snapshot_id"]
        
        repository["execute"]("""
            CREATE (s:RequirementSnapshot {
                snapshot_id: $snapshot_id,
                requirement_id: $requirement_id,
                version_id: $version_id,
                title: $title,
                description: $description,
                priority: $priority,
                requirement_type: $requirement_type,
                status: $status,
                tags: $tags,
                embedding: $embedding,
                created_at: $created_at,
                snapshot_at: $snapshot_at,
                is_deleted: $is_deleted
            })
            RETURN s
        """, snapshot)
        
        # スナップショット関係を作成
        repository["execute"]("""
            MATCH (r:RequirementEntity {id: $req_id}), (s:RequirementSnapshot {snapshot_id: $snap_id})
            CREATE (r)-[:HAS_SNAPSHOT]->(s)
        """, {"req_id": requirement_id, "snap_id": snapshot_id})
        
        repository["execute"]("""
            MATCH (s:RequirementSnapshot {snapshot_id: $snap_id}), (v:VersionState {id: $ver_id})
            CREATE (s)-[:SNAPSHOT_OF_VERSION]->(v)
        """, {"snap_id": snapshot_id, "ver_id": version_id})
        
        return {
            "version_id": version_id,
            "snapshot_id": snapshot_id,
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
            MATCH (r:RequirementEntity {id: $req_id})-[:HAS_SNAPSHOT]->(s:RequirementSnapshot)
                  -[:SNAPSHOT_OF_VERSION]->(v:VersionState)
            RETURN s, v
            ORDER BY v.timestamp DESC
            LIMIT $limit
        """, {"req_id": requirement_id, "limit": limit})
        
        history = []
        while result.has_next():
            snapshot, version = result.get_next()
            history.append({
                "version_id": version["id"],
                "timestamp": version["timestamp"],
                "author": version["author"],
                "change_reason": version["change_reason"],
                "snapshot": snapshot
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
        result = repository["execute"]("""
            MATCH (s:RequirementSnapshot)-[:SNAPSHOT_OF_VERSION]->(v:VersionState)
            WHERE s.requirement_id = $req_id AND v.timestamp <= $target_time
            RETURN s
            ORDER BY v.timestamp DESC
            LIMIT 1
        """, {"req_id": requirement_id, "target_time": timestamp})
        
        if result.has_next():
            return result.get_next()[0]
        
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
        # 両方のスナップショットを取得
        result = repository["execute"]("""
            MATCH (s1:RequirementSnapshot {requirement_id: $req_id, version_id: $v1}),
                  (s2:RequirementSnapshot {requirement_id: $req_id, version_id: $v2})
            RETURN s1, s2
        """, {"req_id": requirement_id, "v1": version1_id, "v2": version2_id})
        
        if not result.has_next():
            return {"error": "Versions not found"}
        
        snapshot1, snapshot2 = result.get_next()
        
        return calculate_requirement_diff(snapshot1, snapshot2)
    
    return {
        "track_requirement_change": track_requirement_change,
        "get_requirement_history": get_requirement_history,
        "get_requirement_at_version": get_requirement_at_version,
        "calculate_version_diff": calculate_version_diff
    }


# Test cases (in-source test)
def test_version_service_track_change_creates_version():
    """version_service_track_change_バージョン作成_成功を返す"""
    # モックリポジトリ
    executions = []
    requirements = {
        "req_001": {
            "id": "req_001",
            "title": "Test Requirement",
            "description": "Test description",
            "status": "proposed",
            "tags": ["L0_vision"],
            "embedding": [0.1] * 50,
            "created_at": datetime.now()
        }
    }
    
    def mock_execute(query, params=None):
        executions.append((query, params))
        return MockResult([])
    
    def mock_find(req_id):
        return requirements.get(req_id, {"type": "NotFoundError"})
    
    repository = {
        "execute": mock_execute,
        "find_requirement": mock_find,
        "save_requirement": lambda r: r
    }
    
    service = create_version_service(repository)
    
    # 変更を追跡
    result = service["track_requirement_change"]("req_001", "UPDATE", "test_user", "Updated description")
    
    assert "version_id" in result
    assert "snapshot_id" in result
    assert "location_uri" in result
    assert result["status"] == "tracked"
    assert len(executions) > 5  # 複数のクエリが実行される


def test_version_service_history_returns_sorted_versions():
    """version_service_history_履歴取得_時系列順で返す"""
    # モックデータ
    history_data = [
        ({
            "snapshot_id": "req_001@v1",
            "title": "Version 1"
        }, {
            "id": "v1",
            "timestamp": "2024-01-01T00:00:00",
            "author": "user1",
            "change_reason": "Initial"
        }),
        ({
            "snapshot_id": "req_001@v2",
            "title": "Version 2"
        }, {
            "id": "v2",
            "timestamp": "2024-01-02T00:00:00",
            "author": "user2",
            "change_reason": "Update"
        })
    ]
    
    def mock_execute(query, params=None):
        if "ORDER BY v.timestamp DESC" in query:
            return create_mock_result(history_data)
        return create_mock_result([])
    
    repository = {
        "execute": mock_execute,
        "find_requirement": lambda id: {},
        "save_requirement": lambda r: r
    }
    
    service = create_version_service(repository)
    
    # 履歴を取得
    history = service["get_requirement_history"]("req_001")
    
    assert len(history) == 2
    assert history[0]["version_id"] == "v1"
    assert history[1]["version_id"] == "v2"


# テスト用ヘルパー関数
def create_mock_result(data):
    """テスト用のモック結果オブジェクトを作成"""
    items = data if isinstance(data, list) else [data]
    index = [0]  # クロージャで状態を保持
    
    def has_next():
        return index[0] < len(items)
    
    def get_next():
        if has_next():
            result = items[index[0]]
            index[0] += 1
            return result
        return None
    
    # オブジェクト風のアクセスを提供
    mock = type('MockResult', (), {
        'has_next': has_next,
        'get_next': get_next,
        '_data': items
    })()
    
    return mock
