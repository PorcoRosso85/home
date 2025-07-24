#!/usr/bin/env python3
"""
VECTOR拡張管理モジュール

KuzuDBのVECTOR拡張の管理とベクトル検索機能を提供
"""

from typing import Dict, Any, List, Optional, Tuple
import time
from log_py import log


VECTOR_EXTENSION_NAME = 'VECTOR'
DOCUMENT_TABLE_NAME = 'Document'
DOCUMENT_EMBEDDING_INDEX_NAME = 'doc_embedding_index'
EMBEDDING_DIMENSION = 256


def install_vector_extension(connection: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    VECTOR拡張をインストールしてロードする
    
    Args:
        connection: KuzuDB接続オブジェクト
        
    Returns:
        (success, error_info)
    """
    try:
        log("info", {
            "message": "Installing VECTOR extension",
            "component": "vss.infrastructure.vector",
            "operation": "install_vector_extension",
            "extension": VECTOR_EXTENSION_NAME
        })
        
        # Install VECTOR extension
        connection.execute(f"INSTALL {VECTOR_EXTENSION_NAME}")
        
        log("info", {
            "message": "Loading VECTOR extension",
            "component": "vss.infrastructure.vector",
            "operation": "install_vector_extension",
            "extension": VECTOR_EXTENSION_NAME
        })
        
        # Load VECTOR extension
        connection.execute(f"LOAD EXTENSION {VECTOR_EXTENSION_NAME}")
        
        log("info", {
            "message": "VECTOR extension installed and loaded successfully",
            "component": "vss.infrastructure.vector",
            "operation": "install_vector_extension",
            "extension": VECTOR_EXTENSION_NAME
        })
        
        return True, None
        
    except Exception as e:
        error_msg = str(e)
        error_info = {
            "error": f"Failed to install/load VECTOR extension: {str(e)}",
            "details": {
                "extension": VECTOR_EXTENSION_NAME,
                "raw_error": error_msg
            }
        }
        log("error", {
            "message": "VECTOR extension installation failed",
            "component": "vss.infrastructure.vector",
            "operation": "install_vector_extension",
            "exception_type": type(e).__name__,
            "exception": str(e),
            "extension": VECTOR_EXTENSION_NAME
        })
        return False, error_info


def check_vector_extension(connection: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    VECTOR拡張が利用可能かチェックし、必要ならインストールする
    
    Args:
        connection: KuzuDB接続オブジェクト
        
    Returns:
        (is_available, error_info)
    """
    try:
        # Simple check - try to call VECTOR extension function
        # This will fail immediately if VECTOR is not available
        test_table = "_vector_test_" + str(int(time.time() * 1000))
        try:
            # Just check if CREATE_VECTOR_INDEX function exists
            # Use a table that doesn't exist - it will fail but in a different way
            connection.execute(f"""
                CALL CREATE_VECTOR_INDEX(
                    'nonexistent_table_{test_table}',
                    'test_idx',
                    'embedding'
                )
            """)
        except Exception as e:
            error_msg = str(e)
            # If error is about the table not existing, VECTOR is available
            if "does not exist" in error_msg and "nonexistent_table" in error_msg:
                return True, None
            # If error is about CREATE_VECTOR_INDEX not being defined, VECTOR is missing
            if "CREATE_VECTOR_INDEX" in error_msg and ("not defined" in error_msg or "unknown" in error_msg):
                raise
            # For other errors, assume VECTOR is available
            return True, None
        
    except Exception as e:
        error_msg = str(e)
        if any(pattern in error_msg for pattern in ["Extension", "CREATE_VECTOR_INDEX", "does not exist", "unknown function", "not defined"]):
            install_success, install_error = install_vector_extension(connection)
            
            if install_success:
                return check_vector_extension(connection)
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


def initialize_vector_schema(
    connection: Any, 
    dimension: int,
    mu: int = 30,
    ml: int = 60,
    metric: str = 'cosine',
    efc: int = 200
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    ベクトル検索用のスキーマを初期化する
    
    Args:
        connection: KuzuDB接続オブジェクト
        dimension: 埋め込みベクトルの次元数
        mu: 上位グラフのノード最大次数 (default: 30)
        ml: 下位グラフのノード最大次数 (default: 60)
        metric: 距離計算関数 ('cosine', 'l2', 'l2sq', 'dotproduct') (default: 'cosine')
        efc: インデックス構築時の候補頂点数 (default: 200)
        
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
        
        # Try to create the index
        try:
            create_index_query = f"""
                CALL CREATE_VECTOR_INDEX(
                    '{DOCUMENT_TABLE_NAME}',
                    '{DOCUMENT_EMBEDDING_INDEX_NAME}',
                    'embedding',
                    mu := {mu},
                    ml := {ml},
                    metric := '{metric}',
                    efc := {efc}
                )
            """
            connection.execute(create_index_query)
        except Exception as e:
            error_msg = str(e)
            # If index already exists, that's OK - schema is already initialized
            if "already exists" in error_msg:
                return True, None
            # Otherwise, re-raise the exception
            raise
        
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
            if len(embedding) != EMBEDDING_DIMENSION:
                return False, inserted_count, {
                    "error": f"Invalid embedding dimension",
                    "details": {
                        "expected": EMBEDDING_DIMENSION,
                        "got": len(embedding),
                        "document_id": doc_id
                    }
                }
            
            # Check if document exists first
            check_query = f"""
                MATCH (d:{DOCUMENT_TABLE_NAME} {{id: $id}})
                RETURN d.id
            """
            check_result = connection.execute(check_query, {"id": doc_id})
            
            if check_result.has_next():
                # Document exists - delete and re-insert due to index constraints
                delete_query = f"""
                    MATCH (d:{DOCUMENT_TABLE_NAME} {{id: $id}})
                    DELETE d
                """
                connection.execute(delete_query, {"id": doc_id})
            
            # Insert new document
            query = f"""
                CREATE (d:{DOCUMENT_TABLE_NAME} {{id: $id, content: $content, embedding: $embedding}})
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
    limit: int = 10,
    efs: int = 200
) -> Tuple[bool, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    類似ベクトルを検索する
    
    Args:
        connection: KuzuDB接続オブジェクト
        query_vector: クエリベクトル
        limit: 返す結果の最大数
        efs: 検索時の候補頂点数 (default: 200)
        
    Returns:
        (success, results, error_info)
    """
    try:
        if len(query_vector) != EMBEDDING_DIMENSION:
            log("warning", {
                "message": "Invalid query vector dimension",
                "component": "vss.infrastructure.vector",
                "operation": "search_similar_vectors",
                "expected_dimension": EMBEDDING_DIMENSION,
                "actual_dimension": len(query_vector)
            })
            return False, [], {
                "error": "Invalid query vector dimension",
                "details": {
                    "expected": EMBEDDING_DIMENSION,
                    "got": len(query_vector)
                }
            }
        
        log("info", {
            "message": "Executing vector similarity search",
            "component": "vss.infrastructure.vector",
            "operation": "search_similar_vectors",
            "limit": limit,
            "efs": efs,
            "table": DOCUMENT_TABLE_NAME,
            "index": DOCUMENT_EMBEDDING_INDEX_NAME
        })
        
        result = connection.execute(f"""
            CALL QUERY_VECTOR_INDEX(
                '{DOCUMENT_TABLE_NAME}',
                '{DOCUMENT_EMBEDDING_INDEX_NAME}',
                $query_vector,
                $limit,
                efs := {efs}
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
            
            results.append({
                "id": node.get("id"),
                "content": node.get("content"),
                "distance": float(distance),
                "embedding": node.get("embedding")
            })
        
        log("info", {
            "message": "Vector search completed successfully",
            "component": "vss.infrastructure.vector",
            "operation": "search_similar_vectors",
            "results_count": len(results),
            "limit": limit
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