#!/usr/bin/env python3
"""
インフラストラクチャ層 - KuzuDB関連の関数

データベース接続、VECTOR拡張の操作、永続化など
外部システム（KuzuDB）との接続を担当
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import time
from pathlib import Path
from dataclasses import dataclass

# KuzuDB imports
try:
    from kuzu_py import create_database, create_connection
except ImportError:
    # For testing without actual kuzu_py
    create_database = None
    create_connection = None


# Constants
VECTOR_EXTENSION_NAME = 'VECTOR'
DOCUMENT_TABLE_NAME = 'Document'
DOCUMENT_EMBEDDING_INDEX_NAME = 'doc_embedding_index'
IN_MEMORY_DB_PATH = ':memory:'
EMBEDDING_DIMENSION = 256


@dataclass(frozen=True)
class DatabaseConfig:
    """データベース設定の不変データクラス"""
    db_path: str
    in_memory: bool
    embedding_dimension: int = EMBEDDING_DIMENSION


def create_kuzu_database(config: DatabaseConfig) -> Tuple[bool, Optional[Any], Optional[Dict[str, Any]]]:
    """
    KuzuDBデータベースを作成する
    
    Args:
        config: データベース設定
        
    Returns:
        (success, database_object, error_info)
    """
    if create_database is None:
        return False, None, {
            "error": "KuzuDB not available",
            "details": {
                "message": "kuzu_py module is not installed",
                "install_command": "pip install kuzu"
            }
        }
    
    try:
        db_path = IN_MEMORY_DB_PATH if config.in_memory else config.db_path
        db = create_database(db_path)
        
        # Check if it's an error response
        if hasattr(db, 'get') and db.get("ok") is False:
            return False, None, {
                "error": db.get("error", "Unknown error"),
                "details": db.get("details", {})
            }
        
        return True, db, None
        
    except Exception as e:
        return False, None, {
            "error": f"Failed to create database: {str(e)}",
            "details": {
                "exception_type": type(e).__name__,
                "db_path": config.db_path
            }
        }


def create_kuzu_connection(database: Any) -> Tuple[bool, Optional[Any], Optional[Dict[str, Any]]]:
    """
    KuzuDBへの接続を作成する
    
    Args:
        database: KuzuDBデータベースオブジェクト
        
    Returns:
        (success, connection_object, error_info)
    """
    if create_connection is None:
        return False, None, {
            "error": "KuzuDB not available",
            "details": {
                "message": "kuzu_py module is not installed",
                "install_command": "pip install kuzu"
            }
        }
    
    try:
        conn = create_connection(database)
        
        # Check if it's an error response
        if hasattr(conn, 'get') and conn.get("ok") is False:
            return False, None, {
                "error": conn.get("error", "Unknown error"),
                "details": conn.get("details", {})
            }
        
        return True, conn, None
        
    except Exception as e:
        return False, None, {
            "error": f"Failed to create connection: {str(e)}",
            "details": {
                "exception_type": type(e).__name__
            }
        }


def install_vector_extension(connection: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    VECTOR拡張をインストールしてロードする
    
    Args:
        connection: KuzuDB接続オブジェクト
        
    Returns:
        (success, error_info)
    """
    try:
        # Install VECTOR extension
        connection.execute(f"INSTALL {VECTOR_EXTENSION_NAME}")
        # Load VECTOR extension
        connection.execute(f"LOAD EXTENSION {VECTOR_EXTENSION_NAME}")
        return True, None
        
    except Exception as e:
        error_msg = str(e)
        return False, {
            "error": f"Failed to install/load VECTOR extension: {str(e)}",
            "details": {
                "extension": VECTOR_EXTENSION_NAME,
                "raw_error": error_msg
            }
        }


def check_vector_extension(connection: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    VECTOR拡張が利用可能かチェックし、必要ならインストールする
    
    Args:
        connection: KuzuDB接続オブジェクト
        
    Returns:
        (is_available, error_info)
    """
    try:
        # First try to check if extension is already loaded
        # by attempting to create a temporary vector index
        test_table = "_vector_test_" + str(int(time.time() * 1000))
        try:
            # Create a temporary table with vector
            connection.execute(f"""
                CREATE NODE TABLE IF NOT EXISTS {test_table} (
                    id INT64,
                    embedding DOUBLE[3],
                    PRIMARY KEY (id)
                )
            """)
            
            # Try to create a vector index
            connection.execute(f"""
                CREATE VECTOR INDEX IF NOT EXISTS {test_table}_idx 
                ON {test_table}(embedding)
            """)
            
            # Clean up
            connection.execute(f"DROP TABLE {test_table}")
            
            # If we get here, VECTOR extension is available
            return True, None
            
        except Exception:
            # Try to clean up if table was created
            try:
                connection.execute(f"DROP TABLE IF EXISTS {test_table}")
            except:
                pass
            raise
        
    except Exception as e:
        error_msg = str(e)
        # Check for various error patterns that indicate missing VECTOR extension
        if any(pattern in error_msg for pattern in ["Extension", "vector_dims", "does not exist", "unknown function"]):
            # Try to install the extension
            install_success, install_error = install_vector_extension(connection)
            
            if install_success:
                # Try the test query again
                try:
                    connection.execute(test_query)
                    return True, None
                except Exception as e2:
                    return False, {
                        "error": "VECTOR extension installed but still not working",
                        "details": {
                            "extension": VECTOR_EXTENSION_NAME,
                            "install_error": str(e2),
                            "original_error": error_msg
                        }
                    }
            else:
                return False, {
                    "error": "VECTOR extension not available and failed to install",
                    "details": {
                        "extension": VECTOR_EXTENSION_NAME,
                        "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                        "install_error": install_error,
                        "original_error": error_msg
                    }
                }
        else:
            # For other errors, assume VECTOR extension is not available
            return False, {
                "error": "VECTOR extension check failed",
                "details": {
                    "extension": VECTOR_EXTENSION_NAME,
                    "raw_error": error_msg
                }
            }


def initialize_vector_schema(connection: Any, dimension: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    ベクトル検索用のスキーマを初期化する
    
    Args:
        connection: KuzuDB接続オブジェクト
        dimension: 埋め込みベクトルの次元数
        
    Returns:
        (success, error_info)
    """
    try:
        # Create Document node table with VECTOR type
        create_table_query = f"""
            CREATE NODE TABLE IF NOT EXISTS {DOCUMENT_TABLE_NAME} (
                id STRING,
                content STRING,
                embedding DOUBLE[{dimension}],
                PRIMARY KEY (id)
            )
        """
        connection.execute(create_table_query)
        
        # Create vector index
        create_index_query = f"""
            CREATE VECTOR INDEX IF NOT EXISTS {DOCUMENT_EMBEDDING_INDEX_NAME} 
            ON {DOCUMENT_TABLE_NAME}(embedding)
        """
        connection.execute(create_index_query)
        
        return True, None
        
    except Exception as e:
        error_msg = str(e)
        if "Extension" in error_msg and VECTOR_EXTENSION_NAME in error_msg:
            return False, {
                "error": "VECTOR extension not available",
                "details": {
                    "extension": VECTOR_EXTENSION_NAME,
                    "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                    "raw_error": error_msg
                }
            }
        else:
            return False, {
                "error": f"Failed to initialize schema: {error_msg}",
                "details": {
                    "exception_type": type(e).__name__,
                    "dimension": dimension
                }
            }


def insert_documents_with_embeddings(
    connection: Any,
    documents: List[Tuple[str, str, List[float]]]
) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
    """
    ドキュメントと埋め込みをデータベースに挿入する
    
    Args:
        connection: KuzuDB接続オブジェクト
        documents: (id, content, embedding)のタプルリスト
        
    Returns:
        (success, inserted_count, error_info)
    """
    if not documents:
        return False, 0, {
            "error": "No documents provided",
            "details": {"documents_count": 0}
        }
    
    inserted_count = 0
    
    try:
        for doc_id, content, embedding in documents:
            # Validate embedding dimension
            if len(embedding) != EMBEDDING_DIMENSION:
                return False, inserted_count, {
                    "error": f"Invalid embedding dimension",
                    "details": {
                        "expected": EMBEDDING_DIMENSION,
                        "got": len(embedding),
                        "document_id": doc_id
                    }
                }
            
            # Insert or update document
            query = f"""
                MERGE (d:{DOCUMENT_TABLE_NAME} {{id: $id}})
                SET d.content = $content, d.embedding = $embedding
            """
            
            connection.execute(query, {
                "id": doc_id,
                "content": content,
                "embedding": embedding
            })
            
            inserted_count += 1
        
        return True, inserted_count, None
        
    except Exception as e:
        error_msg = str(e)
        if "Extension" in error_msg and VECTOR_EXTENSION_NAME in error_msg:
            return False, inserted_count, {
                "error": "VECTOR extension not available",
                "details": {
                    "extension": VECTOR_EXTENSION_NAME,
                    "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                    "inserted_before_error": inserted_count
                }
            }
        else:
            return False, inserted_count, {
                "error": f"Failed to insert documents: {error_msg}",
                "details": {
                    "exception_type": type(e).__name__,
                    "inserted_before_error": inserted_count
                }
            }


def search_similar_vectors(
    connection: Any,
    query_vector: List[float],
    limit: int = 10
) -> Tuple[bool, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    類似ベクトルを検索する
    
    Args:
        connection: KuzuDB接続オブジェクト
        query_vector: クエリベクトル
        limit: 返す結果の最大数
        
    Returns:
        (success, results, error_info)
    """
    try:
        # Validate query vector dimension
        if len(query_vector) != EMBEDDING_DIMENSION:
            return False, [], {
                "error": "Invalid query vector dimension",
                "details": {
                    "expected": EMBEDDING_DIMENSION,
                    "got": len(query_vector)
                }
            }
        
        # Search using VECTOR extension's QUERY_VECTOR_INDEX
        # Use QUERY_VECTOR_INDEX function
        result = connection.execute(f"""
            CALL QUERY_VECTOR_INDEX(
                '{DOCUMENT_TABLE_NAME}',
                '{DOCUMENT_EMBEDDING_INDEX_NAME}',
                $query_vector,
                $limit
            )
            RETURN node, distance
        """, {
            "query_vector": query_vector,
            "limit": limit
        })
        
        # Process results
        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]  # node object
            distance = row[1]  # distance value
            
            # Extract node properties
            results.append({
                "id": node.get("id"),
                "content": node.get("content"),
                "distance": float(distance),
                "embedding": node.get("embedding")
            })
        
        return True, results, None
        
    except Exception as e:
        error_msg = str(e)
        if "Extension" in error_msg and VECTOR_EXTENSION_NAME in error_msg:
            return False, [], {
                "error": "VECTOR extension not available",
                "details": {
                    "extension": VECTOR_EXTENSION_NAME,
                    "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                    "raw_error": error_msg
                }
            }
        elif "dimension" in error_msg.lower():
            return False, [], {
                "error": "Vector dimension mismatch",
                "details": {
                    "expected": EMBEDDING_DIMENSION,
                    "got": len(query_vector),
                    "raw_error": error_msg
                }
            }
        elif "QUERY_VECTOR_INDEX" in error_msg or "does not exist" in error_msg:
            return False, [], {
                "error": "VECTOR extension not available or index not created",
                "details": {
                    "extension": VECTOR_EXTENSION_NAME,
                    "function": "QUERY_VECTOR_INDEX",
                    "index_name": DOCUMENT_EMBEDDING_INDEX_NAME,
                    "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                    "raw_error": error_msg
                }
            }
        else:
            return False, [], {
                "error": f"Search failed: {error_msg}",
                "details": {
                    "exception_type": type(e).__name__,
                    "raw_error": error_msg
                }
            }


def count_documents(connection: Any) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
    """
    ドキュメントの総数を取得する
    
    Args:
        connection: KuzuDB接続オブジェクト
        
    Returns:
        (success, count, error_info)
    """
    try:
        query = f"MATCH (d:{DOCUMENT_TABLE_NAME}) RETURN COUNT(d) AS count"
        result = connection.execute(query)
        
        if result.has_next():
            count = result.get_next()[0]
            return True, int(count), None
        else:
            return True, 0, None
            
    except Exception as e:
        return False, 0, {
            "error": f"Failed to count documents: {str(e)}",
            "details": {
                "exception_type": type(e).__name__
            }
        }


def close_connection(connection: Any) -> None:
    """
    データベース接続を閉じる
    
    Args:
        connection: KuzuDB接続オブジェクト
    """
    if connection is not None:
        try:
            connection.close()
        except Exception:
            # Ignore errors when closing
            pass