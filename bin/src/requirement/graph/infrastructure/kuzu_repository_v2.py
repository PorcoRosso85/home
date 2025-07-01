"""
KuzuDB Repository v2 - 規約準拠版
依存: domain, application
外部依存: kuzu

環境変数管理を統一し、/orgモードに対応
"""
import os
import sys
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from ..domain.types import Decision, DecisionResult, DecisionNotFoundError, DecisionError
from .variables.env import load_environment, get_db_path, parse_bool
from .variables.paths import get_kuzu_module_path
from .logger import debug, info, warn, error


def create_kuzu_repository(env_config: Optional[Dict] = None) -> Dict:
    """
    KuzuDBベースのリポジトリを作成（環境変数設定を注入）
    
    Args:
        env_config: 環境設定（テスト用にオプション）
        
    Returns:
        Repository関数の辞書
        
    Example:
        >>> env_config = load_environment()
        >>> repo = create_kuzu_repository(env_config)
        >>> repo["save"](decision)
    """
    # 環境設定のロード
    if env_config is None:
        env_config = load_environment()
    
    db_path = get_db_path(env_config)
    ld_library_path = env_config["ld_library_path"]
    
    info("rgl.repo.v2", "Creating KuzuDB repository", db_path=db_path, org_mode=env_config.get("rgl_org_mode"))
    
    # KuzuDBのインポート
    try:
        kuzu_path = get_kuzu_module_path()
        if kuzu_path:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "kuzu", 
                os.path.join(kuzu_path, "__init__.py")
            )
            kuzu = importlib.util.module_from_spec(spec)
            sys.modules['kuzu'] = kuzu
            spec.loader.exec_module(kuzu)
            debug("rgl.repo.v2", "KuzuDB module loaded successfully")
        else:
            import kuzu
            debug("rgl.repo.v2", "KuzuDB module imported normally")
    except Exception as e:
        error("rgl.repo.v2", "KuzuDB import failed", error=str(e), ld_path=ld_library_path)
        raise ImportError(
            f"KuzuDB import failed: {e}\n"
            f"LD_LIBRARY_PATH is set to: {ld_library_path}"
        )
    
    # ディレクトリ作成
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # データベース作成
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    
    def init_schema():
        """スキーマ初期化"""
        try:
            conn.execute("MATCH (n:RequirementEntity) RETURN count(n) LIMIT 1")
        except:
            raise RuntimeError("Schema not initialized. Run apply_ddl_schema.py first")
    
    # スキーマチェック（環境変数で制御）
    if not parse_bool(env_config.get("rgl_skip_schema_check")):
        init_schema()
    
    # 階層処理用UDFを登録
    from .hierarchy_udfs import register_hierarchy_udfs
    register_hierarchy_udfs(conn)
    
    def save(decision: Decision, parent_id: Optional[str] = None, track_version: bool = True) -> DecisionResult:
        """要件を保存（バージョン追跡付き）"""
        try:
            # 既存の要件かチェック
            existing_check = conn.execute("""
                MATCH (r:RequirementEntity {id: $id})
                RETURN r
            """, {"id": decision["id"]})
            
            existing = existing_check.get_next() if existing_check.has_next() else None
            
            if existing:
                # 更新
                conn.execute("""
                    MATCH (r:RequirementEntity {id: $id})
                    SET r.title = $title,
                        r.description = $description,
                        r.status = $status
                    RETURN r
                """, {
                    "id": decision["id"],
                    "title": decision["title"],
                    "description": decision["description"],
                    "status": decision["status"]
                })
                operation = "UPDATE"
            else:
                # 新規作成
                conn.execute("""
                    CREATE (r:RequirementEntity {
                        id: $id,
                        title: $title,
                        description: $description,
                        status: $status,
                        created_at: $created_at
                    })
                    RETURN r
                """, {
                    "id": decision["id"],
                    "title": decision["title"],
                    "description": decision["description"],
                    "status": decision["status"],
                    "created_at": decision["created_at"].isoformat()
                })
                operation = "CREATE"
            
            info("rgl.repo.v2", f"Decision {operation.lower()}d", id=decision["id"])
            
            # バージョン追跡
            if track_version:
                version_id = f"ver_{decision['id']}_{int(datetime.now().timestamp())}"
                conn.execute("""
                    CREATE (v:VersionState {
                        id: $version_id,
                        timestamp: $timestamp,
                        description: $description,
                        operation: $operation
                    })
                """, {
                    "version_id": version_id,
                    "timestamp": datetime.now().isoformat(),
                    "description": f"{operation} decision {decision['id']}",
                    "operation": operation
                })
                
                conn.execute("""
                    MATCH (r:RequirementEntity {id: $id}), (v:VersionState {id: $version_id})
                    CREATE (r)-[:HAS_VERSION]->(v)
                """, {
                    "id": decision["id"],
                    "version_id": version_id
                })
            
            return decision
            
        except Exception as e:
            error("rgl.repo.v2", "Save failed", error=str(e))
            return {
                "type": "InvalidDecisionError",
                "message": f"Failed to save decision: {str(e)}",
                "details": [str(e)]
            }
    
    def find_by_id(decision_id: str) -> Union[Decision, DecisionNotFoundError]:
        """IDで要件を検索"""
        try:
            result = conn.execute("""
                MATCH (r:RequirementEntity {id: $id})
                RETURN r
            """, {"id": decision_id})
            
            if result.has_next():
                row = result.get_next()
                req = row[0]
                
                return {
                    "id": req["id"],
                    "title": req["title"],
                    "description": req["description"],
                    "status": req["status"],
                    "created_at": datetime.fromisoformat(req["created_at"]),
                    "embedding": []  # 簡略化
                }
            else:
                return {
                    "type": "DecisionNotFoundError",
                    "message": f"Decision not found: {decision_id}",
                    "decision_id": decision_id
                }
                
        except Exception as e:
            error("rgl.repo.v2", "Find failed", error=str(e))
            return {
                "type": "DecisionNotFoundError",
                "message": f"Error finding decision: {str(e)}",
                "decision_id": decision_id
            }
    
    def find_all() -> List[Decision]:
        """すべての要件を取得"""
        try:
            result = conn.execute("""
                MATCH (r:RequirementEntity)
                RETURN r
                ORDER BY r.created_at DESC
            """)
            
            decisions = []
            while result.has_next():
                row = result.get_next()
                req = row[0]
                
                decisions.append({
                    "id": req["id"],
                    "title": req["title"],
                    "description": req["description"],
                    "status": req["status"],
                    "created_at": datetime.fromisoformat(req["created_at"]),
                    "embedding": []
                })
            
            return decisions
            
        except Exception as e:
            error("rgl.repo.v2", "Find all failed", error=str(e))
            return []
    
    # 共有DB用の追加メソッド
    def get_shared_requirements() -> List[Dict]:
        """共有DBから全ペルソナの要件を取得（/org用）"""
        if env_config.get("rgl_org_mode") != "true":
            warn("rgl.repo.v2", "get_shared_requirements called without org mode")
            return []
        
        try:
            result = conn.execute("""
                MATCH (r:RequirementEntity)
                RETURN r.id as id,
                       r.title as title,
                       r.description as description,
                       r.priority as priority,
                       r.CreatedBy as created_by,
                       r.Metadata as metadata
                ORDER BY r.created_at DESC
            """)
            
            requirements = []
            while result.has_next():
                row = result.get_next()
                requirements.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "priority": row[3],
                    "created_by": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {}
                })
            
            info("rgl.repo.v2", "Shared requirements retrieved", count=len(requirements))
            return requirements
            
        except Exception as e:
            error("rgl.repo.v2", "Get shared requirements failed", error=str(e))
            return []
    
    return {
        "save": save,
        "find_by_id": find_by_id,
        "find_all": find_all,
        "find_similar": lambda text, threshold=0.7: [],  # 簡略化
        "get_shared_requirements": get_shared_requirements,
        "connection": conn,  # 直接アクセス用
        "db_path": db_path  # デバッグ用
    }


# In-source tests
def test_create_kuzu_repository_with_env():
    """環境設定を注入してリポジトリ作成"""
    test_config = {
        "ld_library_path": "/test/lib",
        "rgl_db_path": "/tmp/test.db",
        "rgl_org_mode": "false",
        "rgl_skip_schema_check": "true"
    }
    
    repo = create_kuzu_repository(test_config)
    
    assert repo["db_path"] == "/tmp/test.db"
    assert "save" in repo
    assert "find_by_id" in repo


def test_create_kuzu_repository_org_mode():
    """/orgモードでの共有DB使用"""
    test_config = {
        "ld_library_path": "/test/lib",
        "rgl_db_path": "/tmp/local.db",
        "rgl_shared_db_path": "/tmp/shared.db",
        "rgl_org_mode": "true",
        "rgl_skip_schema_check": "true"
    }
    
    repo = create_kuzu_repository(test_config)
    
    assert repo["db_path"] == "/tmp/shared.db"
    assert "get_shared_requirements" in repo