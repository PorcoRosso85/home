"""
KuzuDB Repository - グラフデータベース永続化
依存: domain, application
外部依存: kuzu
"""
import os
import sys
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

# 相対インポートのみ使用
from ..domain.types import Decision, DecisionResult, DecisionNotFoundError, DecisionError
from .variables import get_db_path, LD_LIBRARY_PATH, should_skip_schema_check
from .logger import debug, info, warn, error


def create_kuzu_repository(db_path: str = None) -> Dict:
    """
    KuzuDBベースのリポジトリを作成
    
    Args:
        db_path: データベースパス（デフォルト: 環境依存）
                 - テスト環境: ":memory:" (インメモリ)
                 - 本番環境: RGL_DB_PATH または ~/.rgl/graph.db
        
    Returns:
        Repository関数の辞書
    """
    # データベースファクトリーを使用
    from .database_factory import create_database, create_connection
    
    # db_pathが明示的に指定されていない場合、環境に応じて決定
    if db_path is None:
        # テストモードかどうか判定
        is_test_mode = should_skip_schema_check()  # RGL_SKIP_SCHEMA_CHECK=true
        if is_test_mode:
            db_path = ":memory:"
            info("rgl.repo", "Test mode detected, using in-memory database")
        else:
            db_path = get_db_path()
            info("rgl.repo", "Production mode, using persistent database", db_path=db_path)
    
    debug("rgl.repo", "Using database path", path=str(db_path))
    
    # インメモリデータベースの判定
    in_memory = db_path == ":memory:"
    
    # データベースとコネクションの作成
    if in_memory:
        # テスト用: キャッシュなし、ユニークインスタンス
        db = create_database(in_memory=True, use_cache=False, test_unique=True)
    else:
        db = create_database(path=str(db_path))
    
    conn = create_connection(db)
    
    def init_schema():
        """スキーマ初期化 - graph/ddl/schema.cypherは事前適用済みと仮定"""
        # graph/ddl/schema.cypherが適用済みであることを前提とする
        # 必要に応じて存在確認のみ実施
        try:
            conn.execute("MATCH (n:RequirementEntity) RETURN count(n) LIMIT 1")
        except:
            raise RuntimeError("Schema not initialized. Run apply_ddl_schema.py first")
    
    # 初回はスキーマ作成（テスト時はスキップ可能）
    if not should_skip_schema_check():
        init_schema()
    
    # 階層処理用UDFを登録（削除済み）
    # from .hierarchy_udfs import register_hierarchy_udfs
    # register_hierarchy_udfs(conn)
    
    def save(decision: Decision, parent_id: Optional[str] = None, track_version: bool = True) -> DecisionResult:
        """要件を保存（バージョン追跡付き）"""
        try:
            # 既存の要件かチェック
            existing_check = conn.execute("""
                MATCH (r:RequirementEntity {id: $id})
                RETURN r
            """, {"id": decision["id"]})
            
            is_new = not existing_check.has_next()
            operation = "CREATE" if is_new else "UPDATE"
            
            # MERGE（存在しなければ作成、存在すれば更新）
            conn.execute("""
                MERGE (r:RequirementEntity {id: $id})
                SET r.title = $title,
                    r.description = $description,
                    r.priority = $priority,
                    r.requirement_type = $requirement_type,
                    r.status = $status,
                    r.embedding = $embedding,
                    r.created_at = $created_at
                RETURN r
            """, {
                "id": decision["id"],
                "title": decision["title"],
                "description": decision["description"],
                "priority": "medium",  # デフォルト値
                "requirement_type": "functional",  # デフォルト値
                "status": decision["status"],
                "embedding": decision["embedding"],
                "created_at": decision["created_at"].isoformat()
            })
            
            # バージョン追跡を有効にしている場合
            if track_version:
                # LocationURIを生成
                from ..domain.version_tracking import create_location_uri, create_version_id
                
                location_uri = create_location_uri(decision["id"])
                version_id = create_version_id(decision["id"])
                
                # LocationURIノードを作成
                conn.execute("""
                    MERGE (l:LocationURI {id: $uri})
                    RETURN l
                """, {"uri": location_uri})
                
                # 要件とLocationURIを関連付け（新スキーマ対応）
                conn.execute("""
                    MATCH (l:LocationURI {id: $uri}), (r:RequirementEntity {id: $req_id})
                    MERGE (l)-[:LOCATES {entity_type: 'requirement'}]->(r)
                """, {"uri": location_uri, "req_id": decision["id"]})
                
                # 変更フィールドを検出（既存要件の場合）
                changed_fields = []
                if not is_new:
                    # 既存の要件を取得して差分を計算
                    old_req = existing_check.get_next()[0] if existing_check.has_next() else None
                    if old_req:
                        for field in ["title", "description", "status", "priority"]:
                            if field in decision and old_req.get(field) != decision.get(field):
                                changed_fields.append({
                                    "field": field,
                                    "old_value": old_req.get(field),
                                    "new_value": decision.get(field)
                                })
                
                # VersionStateを作成
                conn.execute("""
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
                    "description": f"{operation} requirement {decision['id']}",
                    "reason": operation,
                    "operation": operation,
                    "author": "system",
                    "changed_fields": json.dumps(changed_fields) if changed_fields else None
                })
                
                # 要件とバージョンの関係を作成
                conn.execute("""
                    MATCH (r:RequirementEntity {id: $req_id}), (v:VersionState {id: $ver_id})
                    CREATE (r)-[:HAS_VERSION]->(v)
                """, {"req_id": decision["id"], "ver_id": version_id})
                
                # 前のバージョンとの関係を作成（既存要件の場合）
                if not is_new:
                    conn.execute("""
                        MATCH (v_new:VersionState {id: $new_version}),
                              (v_old:VersionState)<-[:HAS_VERSION]-(r:RequirementEntity {id: $req_id})
                        WHERE v_old.id <> $new_version
                        WITH v_new, v_old
                        ORDER BY v_old.timestamp DESC
                        LIMIT 1
                        CREATE (v_new)-[:FOLLOWS]->(v_old)
                    """, {"new_version": version_id, "req_id": decision["id"]})
                
                # バージョンと位置の関係を作成
                conn.execute("""
                    MATCH (v:VersionState {id: $version_id}), (l:LocationURI {id: $uri})
                    CREATE (v)-[:TRACKS_STATE_OF {entity_type: 'requirement'}]->(l)
                """, {"version_id": version_id, "uri": location_uri})
            
            # 親子関係を設定（LocationURI階層として）
            if parent_id and track_version:
                # 親の存在確認
                parent_check = conn.execute("""
                    MATCH (parent:RequirementEntity {id: $parent_id})
                    RETURN count(*) > 0 as parent_exists
                """, {"parent_id": parent_id})
                
                if not parent_check.has_next() or not parent_check.get_next()[0]:
                    return {
                        "type": "DecisionNotFoundError",
                        "message": f"Parent requirement {parent_id} not found",
                        "decision_id": parent_id
                    }
                
                # 親のLocationURIを取得して階層関係を作成
                parent_uri = location_uri.rsplit('/', 1)[0]  # 親パスを推定
                conn.execute("""
                    MATCH (parent:LocationURI {id: $parent_uri})
                    MATCH (child:LocationURI {id: $child_uri})
                    MERGE (parent)-[:CONTAINS_LOCATION {relation_type: 'hierarchy'}]->(child)
                """, {
                    "parent_uri": parent_uri, 
                    "child_uri": location_uri
                })
            
            return decision
            
        except Exception as e:
            return {
                "type": "DatabaseError",
                "message": f"Failed to save requirement: {str(e)}",
                "decision_id": decision["id"]
            }
    
    def find(requirement_id: str) -> DecisionResult:
        """IDで要件を検索"""
        try:
            result = conn.execute("""
                MATCH (r:RequirementEntity {id: $id})
                RETURN r
            """, {"id": requirement_id})
            
            if result.has_next():
                row = result.get_next()
                node = row[0]
                
                # KuzuDBのノードから辞書に変換
                from datetime import datetime
                return {
                    "id": node["id"],
                    "title": node["title"],
                    "description": node["description"],
                    "status": node["status"],
                    "created_at": datetime.fromisoformat(node["created_at"]),
                    "embedding": node["embedding"]
                }
            
            return {
                "type": "DecisionNotFoundError",
                "message": f"Requirement {requirement_id} not found",
                "decision_id": requirement_id
            }
            
        except Exception as e:
            return {
                "type": "DatabaseError",
                "message": f"Failed to find requirement: {str(e)}",
                "decision_id": requirement_id
            }
    
    def find_all() -> List[Decision]:
        """全要件を取得"""
        try:
            result = conn.execute("""
                MATCH (r:RequirementEntity)
                RETURN r
                ORDER BY r.created_at DESC
            """)
            
            requirements = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                
                from datetime import datetime
                requirements.append({
                    "id": node["id"],
                    "title": node["title"],
                    "description": node["description"],
                    "status": node["status"],
                    "created_at": datetime.fromisoformat(node["created_at"]),
                    "embedding": node["embedding"]
                })
            
            return requirements
            
        except Exception as e:
            return []
    
    def add_dependency(from_id: str, to_id: str, dependency_type: str = "depends_on", reason: str = "") -> Dict:
        """依存関係を追加"""
        try:
            # 自己依存チェック
            if from_id == to_id:
                return {
                    "type": "ConstraintViolationError",
                    "message": f"Self dependency not allowed: {from_id} -> {to_id}",
                    "constraint": "no_circular_dependency"
                }
            
            # 循環依存チェック
            # from_id → to_id を追加すると、to_id → ... → from_id のパスがあれば循環
            cycle_check = conn.execute("""
                MATCH (from:RequirementEntity {id: $to_id})-[:DEPENDS_ON*]->(to:RequirementEntity {id: $from_id})
                RETURN count(*) > 0 as has_cycle
            """, {"from_id": from_id, "to_id": to_id})
            
            if cycle_check.has_next() and cycle_check.get_next()[0]:
                return {
                    "type": "ConstraintViolationError",
                    "message": f"Circular dependency detected: {from_id} -> {to_id}",
                    "constraint": "no_circular_dependency"
                }
            
            # 依存関係作成
            conn.execute("""
                MATCH (from:RequirementEntity {id: $from_id})
                MATCH (to:RequirementEntity {id: $to_id})
                MERGE (from)-[:DEPENDS_ON {dependency_type: $type, reason: $reason}]->(to)
                RETURN from, to
            """, {
                "from_id": from_id,
                "to_id": to_id,
                "type": dependency_type,
                "reason": reason
            })
            
            return {"success": True, "from": from_id, "to": to_id}
            
        except Exception as e:
            return {
                "type": "DatabaseError",
                "message": f"Failed to add dependency: {str(e)}",
                "from_id": from_id,
                "to_id": to_id
            }
    
    def find_dependencies(requirement_id: str, depth: int = 1) -> List[Dict]:
        """依存関係を検索"""
        try:
            result = conn.execute(f"""
                MATCH path = (r:RequirementEntity {{id: $id}})-[:DEPENDS_ON*1..{depth}]->(dep:RequirementEntity)
                RETURN DISTINCT dep, length(path) as distance
                ORDER BY distance
            """, {"id": requirement_id})
            
            dependencies = []
            while result.has_next():
                row = result.get_next()
                if len(row) >= 2:
                    node = row[0]
                    distance = row[1]
                    
                    from datetime import datetime
                    dependencies.append({
                        "requirement": {
                            "id": node["id"],
                            "title": node["title"],
                            "description": node["description"],
                            "status": node["status"],
                            "created_at": datetime.fromisoformat(node["created_at"]),
                            "embedding": node["embedding"]
                        },
                        "distance": distance
                    })
            
            return dependencies
            
        except Exception as e:
            return []
    
    def search(query: str, threshold: float = 0.7) -> List[Decision]:
        """埋め込みベクトルを使った類似検索"""
        # TODO: ベクトル検索の実装
        # 簡易実装: タイトルと説明文で部分一致検索
        try:
            result = conn.execute("""
                MATCH (r:RequirementEntity)
                WHERE r.title CONTAINS $query OR r.description CONTAINS $query
                RETURN r
                ORDER BY r.created_at DESC
            """, {"query": query})
            
            requirements = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                
                from datetime import datetime
                requirements.append({
                    "id": node["id"],
                    "title": node["title"],
                    "description": node["description"],
                    "status": node["status"],
                    "created_at": datetime.fromisoformat(node["created_at"]),
                    "embedding": node["embedding"]
                })
            
            return requirements
            
        except Exception as e:
            return []
    
    def find_ancestors(requirement_id: str, depth: int = 10) -> List[Dict]:
        """要件の祖先（親・祖父母など）を探索"""
        try:
            # LocationURI階層を利用
            result = conn.execute(f"""
                MATCH (r:RequirementEntity {{id: $id}})
                MATCH (l:LocationURI)-[:LOCATES_LocationURI_RequirementEntity]->(r)
                MATCH path = (l)<-[:CONTAINS_LOCATION*1..{depth}]-(parent_l:LocationURI)
                MATCH (parent_l)-[:LOCATES_LocationURI_RequirementEntity]->(ancestor:RequirementEntity)
                RETURN DISTINCT ancestor, length(path) as distance
                ORDER BY distance
            """, {"id": requirement_id})
            
            ancestors = []
            while result.has_next():
                row = result.get_next()
                if len(row) >= 2:
                    node = row[0]
                    distance = row[1]
                    
                    from datetime import datetime
                    ancestors.append({
                        "requirement": {
                            "id": node["id"],
                            "title": node["title"],
                            "description": node["description"],
                            "status": node["status"],
                            "created_at": datetime.fromisoformat(node["created_at"]),
                            "embedding": node["embedding"]
                        },
                        "distance": distance
                    })
            
            return ancestors
            
        except Exception as e:
            return []
    
    def find_children(requirement_id: str, depth: int = 10) -> List[Dict]:
        """要件の子孫（子・孫など）を探索"""
        try:
            # LocationURI階層を利用
            result = conn.execute(f"""
                MATCH (r:RequirementEntity {{id: $id}})
                MATCH (l:LocationURI)-[:LOCATES_LocationURI_RequirementEntity]->(r)
                MATCH path = (l)-[:CONTAINS_LOCATION*1..{depth}]->(child_l:LocationURI)
                MATCH (child_l)-[:LOCATES_LocationURI_RequirementEntity]->(child:RequirementEntity)
                RETURN DISTINCT child, length(path) as distance
                ORDER BY distance, child.created_at DESC
            """, {"id": requirement_id})
            
            children = []
            while result.has_next():
                row = result.get_next()
                if len(row) >= 2:
                    node = row[0]
                    distance = row[1]
                    
                    from datetime import datetime
                    children.append({
                        "requirement": {
                            "id": node["id"],
                            "title": node["title"],
                            "description": node["description"],
                            "status": node["status"],
                            "created_at": datetime.fromisoformat(node["created_at"]),
                            "embedding": node["embedding"]
                        },
                        "distance": distance
                    })
            
            return children
            
        except Exception as e:
            return []
    
    def get_requirement_history(requirement_id: str, limit: int = 10) -> List[Dict]:
        """
        要件の変更履歴を取得
        
        Args:
            requirement_id: 要件ID
            limit: 取得する履歴の最大数
            
        Returns:
            変更履歴のリスト
        """
        try:
            result = conn.execute("""
                MATCH (r:RequirementEntity {id: $req_id})-[:HAS_VERSION]->(v:VersionState)
                RETURN r.id as requirement_id,
                       r.title as title,
                       r.description as description,
                       r.status as status,
                       r.priority as priority,
                       v.id as version_id,
                       v.timestamp as timestamp,
                       v.change_reason as change_reason,
                       v.author as author,
                       v.operation as operation,
                       v.changed_fields as changed_fields
                ORDER BY v.timestamp DESC
                LIMIT $limit
            """, {"req_id": requirement_id, "limit": limit})
            
            history = []
            while result.has_next():
                row = result.get_next()
                history.append({
                    "version_id": row[5],
                    "timestamp": row[6],
                    "author": row[8],
                    "change_reason": row[7],
                    "snapshot": {
                        "snapshot_id": row[0],
                        "title": row[1],
                        "description": row[2],
                        "status": row[3],
                        "snapshot_at": row[4]
                    }
                })
            
            return history
            
        except Exception as e:
            return []
    
    def get_requirement_at_version(requirement_id: str, timestamp: str) -> Optional[Dict]:
        """
        特定時点での要件状態を取得
        
        Args:
            requirement_id: 要件ID
            timestamp: 対象時刻（ISO形式）
            
        Returns:
            その時点での要件状態
        """
        try:
            result = conn.execute("""
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
                    "created_at": requirement.get("created_at"),
                    "embedding": requirement.get("embedding"),
                    "version_id": version["id"],
                    "timestamp": version["timestamp"]
                }
            
            return None
            
        except Exception as e:
            return None
    
    # CypherExecutorを作成
    from .cypher_executor import CypherExecutor
    executor = CypherExecutor(conn)
    
    return {
        "save": save,
        "find": find,
        "find_all": find_all,
        "search": search,
        "add_dependency": add_dependency,
        "find_dependencies": find_dependencies,
        "find_ancestors": find_ancestors,
        "find_children": find_children,
        "get_requirement_history": get_requirement_history,
        "get_requirement_at_version": get_requirement_at_version,
        "db": db,  # テスト用にDBオブジェクトも返す
        "connection": conn,  # LLM Hooks API用
        "execute": conn.execute,  # CypherExecutor用
        "executor": executor  # LLM Hooks API用
    }
