"""
LocationURI Dataset Management Module

責務:
- LocationURIの有効なデータセットを管理
- データセットからのみノード作成を制限
- requirement/graphのスキーマに準拠
"""
from typing import List, Dict, Optional, Union, Set
from pathlib import Path


def create_locationuri_dataset() -> Dict[str, Union[Dict, List[str]]]:
    """
    LocationURIの有効なデータセットを作成
    
    Returns:
        成功時: {"uris": List[str], "metadata": Dict}
        エラー時: {"type": "Error", "message": str}
    """
    # 標準的な要件URIパターン
    base_uris = [
        # ルートレベル要件
        "req://system",
        "req://architecture", 
        "req://security",
        "req://performance",
        "req://usability",
        
        # アーキテクチャサブ要件
        "req://architecture/infrastructure",
        "req://architecture/domain",
        "req://architecture/application",
        "req://architecture/presentation",
        
        # セキュリティサブ要件
        "req://security/authentication",
        "req://security/authorization",
        "req://security/encryption",
        "req://security/audit",
        
        # パフォーマンスサブ要件
        "req://performance/response_time",
        "req://performance/throughput",
        "req://performance/scalability",
        "req://performance/resource_usage",
        
        # プロジェクト固有要件
        "req://project/trd",
        "req://project/kuzu_integration",
        "req://project/search_service",
    ]
    
    return {
        "uris": base_uris,
        "metadata": {
            "total": len(base_uris),
            "categories": {
                "root": 5,
                "architecture": 4,
                "security": 4,
                "performance": 4,
                "project": 3
            }
        }
    }


def validate_locationuri(uri: str, allowed_dataset: Optional[Set[str]] = None) -> Dict[str, Union[bool, str]]:
    """
    LocationURIの妥当性を検証
    
    Args:
        uri: 検証するURI
        allowed_dataset: 許可されたURIのセット（Noneの場合はフォーマットのみ検証）
    
    Returns:
        {"valid": bool, "reason": str}
    """
    # 基本フォーマット検証
    if not uri.startswith("req://"):
        return {
            "valid": False,
            "reason": "URI must start with 'req://'"
        }
    
    # パス部分の取得
    path = uri[6:]  # "req://"を除去
    
    # 空パスチェック
    if not path:
        return {
            "valid": False,
            "reason": "URI path cannot be empty"
        }
    
    # 不正な文字チェック
    invalid_chars = ["\\", " ", "\n", "\t", "..", "//"]
    for char in invalid_chars:
        if char in path:
            return {
                "valid": False,
                "reason": f"URI contains invalid character or sequence: '{char}'"
            }
    
    # データセット制限チェック
    if allowed_dataset is not None:
        if uri not in allowed_dataset:
            return {
                "valid": False,
                "reason": f"URI '{uri}' is not in the allowed dataset"
            }
    
    return {
        "valid": True,
        "reason": "Valid LocationURI"
    }


def create_restricted_repository(db_path: str = ":memory:") -> Dict[str, any]:
    """
    データセット制限付きリポジトリを作成
    
    Args:
        db_path: データベースパス（デフォルト: インメモリ）
    
    Returns:
        リポジトリ関数の辞書またはエラー
    """
    # kuzu_pyを使用
    import sys
    from pathlib import Path
    
    # persistence/kuzu_pyへのパスを追加
    persistence_path = Path(__file__).parent.parent.parent / "persistence" / "kuzu_py"
    if str(persistence_path) not in sys.path:
        sys.path.insert(0, str(persistence_path))
    
    from database import create_database, create_connection
    
    # データベース作成
    db_result = create_database(db_path)
    if hasattr(db_result, "get") and db_result.get("ok") is False:
        return {
            "type": "DatabaseError",
            "message": "Failed to create database",
            "details": db_result
        }
    
    # コネクション作成
    conn_result = create_connection(db_result)
    if hasattr(conn_result, "get") and conn_result.get("ok") is False:
        return {
            "type": "ConnectionError", 
            "message": "Failed to create connection",
            "details": conn_result
        }
    
    db = db_result
    conn = conn_result
    
    # 許可されたURIデータセットを作成
    dataset_result = create_locationuri_dataset()
    if "type" in dataset_result and dataset_result["type"] == "Error":
        return dataset_result
    
    allowed_uris = set(dataset_result["uris"])
    
    # スキーマ初期化
    try:
        # LocationURIテーブルの作成
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS LocationURI (
                id STRING PRIMARY KEY
            )
        """)
        
        # 初期データセットをロード
        for uri in allowed_uris:
            conn.execute("""
                CREATE (l:LocationURI {id: $uri})
            """, {"uri": uri})
            
    except Exception as e:
        return {
            "type": "SchemaError",
            "message": f"Failed to initialize schema: {str(e)}"
        }
    
    def create_locationuri_node(uri: str) -> Dict[str, any]:
        """制限付きLocationURIノード作成"""
        # 検証
        validation = validate_locationuri(uri, allowed_uris)
        if not validation["valid"]:
            return {
                "type": "ValidationError",
                "message": validation["reason"],
                "uri": uri
            }
        
        try:
            # 既存チェック
            result = conn.execute("""
                MATCH (l:LocationURI {id: $uri})
                RETURN l
            """, {"uri": uri})
            
            if result.has_next():
                return {
                    "type": "AlreadyExists",
                    "message": f"LocationURI '{uri}' already exists",
                    "uri": uri
                }
            
            # 作成（データセットに含まれているので必ず成功するはず）
            conn.execute("""
                CREATE (l:LocationURI {id: $uri})
            """, {"uri": uri})
            
            return {
                "type": "Success",
                "uri": uri,
                "message": "LocationURI node created"
            }
            
        except Exception as e:
            return {
                "type": "DatabaseError",
                "message": f"Failed to create node: {str(e)}",
                "uri": uri
            }
    
    def list_locationuris() -> Dict[str, any]:
        """登録済みLocationURI一覧取得"""
        try:
            result = conn.execute("""
                MATCH (l:LocationURI)
                RETURN l.id as uri
                ORDER BY l.id
            """)
            
            uris = []
            while result.has_next():
                row = result.get_next()
                uris.append(row[0])
            
            return {
                "type": "Success",
                "uris": uris,
                "count": len(uris)
            }
            
        except Exception as e:
            return {
                "type": "DatabaseError",
                "message": f"Failed to list URIs: {str(e)}"
            }
    
    def get_allowed_dataset() -> Dict[str, any]:
        """許可されたデータセットを返す"""
        return {
            "type": "Success",
            "uris": list(allowed_uris),
            "count": len(allowed_uris)
        }
    
    # リポジトリインターフェース
    return {
        "create_locationuri_node": create_locationuri_node,
        "list_locationuris": list_locationuris,
        "get_allowed_dataset": get_allowed_dataset,
        "validate_locationuri": lambda uri: validate_locationuri(uri, allowed_uris),
        "connection": conn,
        "database": db
    }