#!/usr/bin/env python3
"""
インフラストラクチャ層 - KuzuDB関連の関数

データベース接続、VECTOR拡張の操作、永続化など
外部システム（KuzuDB）との接続を担当
"""

from dataclasses import dataclass
from typing import Any

# KuzuDB imports
try:
    from kuzu_py import create_connection, create_database
except ImportError:
    # For testing without actual kuzu_py
    create_database = None
    create_connection = None


# Constants
VECTOR_EXTENSION_NAME = "VECTOR"
FTS_EXTENSION_NAME = "FTS"
DOCUMENT_TABLE_NAME = "Document"
DOCUMENT_EMBEDDING_INDEX_NAME = "doc_embedding_index"
IN_MEMORY_DB_PATH = ":memory:"
EMBEDDING_DIMENSION = 256

# FTS index registry (workaround for missing list functionality)
# In production, this should be persisted in a metadata table
_FTS_INDEX_REGISTRY = {}


@dataclass(frozen=True)
class DatabaseConfig:
    """データベース設定の不変データクラス"""

    db_path: str
    in_memory: bool
    embedding_dimension: int = EMBEDDING_DIMENSION


def create_kuzu_database(config: DatabaseConfig) -> tuple[bool, Any | None, dict[str, Any] | None]:
    """
    KuzuDBデータベースを作成する

    Args:
        config: データベース設定

    Returns:
        (success, database_object, error_info)
    """
    if create_database is None:
        return (
            False,
            None,
            {
                "error": "KuzuDB not available",
                "details": {
                    "message": "kuzu_py module is not installed",
                    "install_command": "pip install kuzu",
                },
            },
        )

    try:
        db_path = IN_MEMORY_DB_PATH if config.in_memory else config.db_path
        db = create_database(db_path)

        # Check if it's an error response
        if hasattr(db, "get") and db.get("ok") is False:
            return (
                False,
                None,
                {"error": db.get("error", "Unknown error"), "details": db.get("details", {})},
            )

        return True, db, None

    except Exception as e:
        return (
            False,
            None,
            {
                "error": f"Failed to create database: {str(e)}",
                "details": {"exception_type": type(e).__name__, "db_path": config.db_path},
            },
        )


def create_kuzu_connection(database: Any) -> tuple[bool, Any | None, dict[str, Any] | None]:
    """
    KuzuDBへの接続を作成する

    Args:
        database: KuzuDBデータベースオブジェクト

    Returns:
        (success, connection_object, error_info)
    """
    if create_connection is None:
        return (
            False,
            None,
            {
                "error": "KuzuDB not available",
                "details": {
                    "message": "kuzu_py module is not installed",
                    "install_command": "pip install kuzu",
                },
            },
        )

    try:
        conn = create_connection(database)

        # Check if it's an error response
        if hasattr(conn, "get") and conn.get("ok") is False:
            return (
                False,
                None,
                {"error": conn.get("error", "Unknown error"), "details": conn.get("details", {})},
            )

        return True, conn, None

    except Exception as e:
        return (
            False,
            None,
            {
                "error": f"Failed to create connection: {str(e)}",
                "details": {"exception_type": type(e).__name__},
            },
        )


def check_vector_extension(connection: Any) -> tuple[bool, dict[str, Any] | None]:
    """
    VECTOR拡張が利用可能かチェックする

    Args:
        connection: KuzuDB接続オブジェクト

    Returns:
        (is_available, error_info)
    """
    try:
        # Try to use VECTOR extension with CALL syntax
        test_query = "CALL vector_dims([1.0, 2.0, 3.0]) RETURN *"
        connection.execute(test_query)

        # If we get here, VECTOR extension is available
        return True, None

    except Exception as e:
        error_msg = str(e)
        # Check for various error patterns that indicate missing VECTOR extension
        if any(
            pattern in error_msg
            for pattern in ["Extension", "vector_dims", "does not exist", "unknown function"]
        ):
            return False, {
                "error": "VECTOR extension not available",
                "details": {
                    "extension": VECTOR_EXTENSION_NAME,
                    "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                    "raw_error": error_msg,
                },
            }
        else:
            # For other errors, assume VECTOR extension is not available
            return False, {
                "error": "VECTOR extension not available",
                "details": {
                    "extension": VECTOR_EXTENSION_NAME,
                    "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                    "raw_error": error_msg,
                },
            }


def initialize_vector_schema(connection: Any, dimension: int) -> tuple[bool, dict[str, Any] | None]:
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
                    "raw_error": error_msg,
                },
            }
        else:
            return False, {
                "error": f"Failed to initialize schema: {error_msg}",
                "details": {"exception_type": type(e).__name__, "dimension": dimension},
            }


def insert_documents_with_embeddings(
    connection: Any, documents: list[tuple[str, str, list[float]]]
) -> tuple[bool, int, dict[str, Any] | None]:
    """
    ドキュメントと埋め込みをデータベースに挿入する

    Args:
        connection: KuzuDB接続オブジェクト
        documents: (id, content, embedding)のタプルリスト

    Returns:
        (success, inserted_count, error_info)
    """
    if not documents:
        return False, 0, {"error": "No documents provided", "details": {"documents_count": 0}}

    inserted_count = 0

    try:
        for doc_id, content, embedding in documents:
            # Validate embedding dimension
            if len(embedding) != EMBEDDING_DIMENSION:
                return (
                    False,
                    inserted_count,
                    {
                        "error": "Invalid embedding dimension",
                        "details": {
                            "expected": EMBEDDING_DIMENSION,
                            "got": len(embedding),
                            "document_id": doc_id,
                        },
                    },
                )

            # Insert or update document
            query = f"""
                MERGE (d:{DOCUMENT_TABLE_NAME} {{id: $id}})
                SET d.content = $content, d.embedding = $embedding
            """

            connection.execute(query, {"id": doc_id, "content": content, "embedding": embedding})

            inserted_count += 1

        return True, inserted_count, None

    except Exception as e:
        error_msg = str(e)
        if "Extension" in error_msg and VECTOR_EXTENSION_NAME in error_msg:
            return (
                False,
                inserted_count,
                {
                    "error": "VECTOR extension not available",
                    "details": {
                        "extension": VECTOR_EXTENSION_NAME,
                        "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                        "inserted_before_error": inserted_count,
                    },
                },
            )
        else:
            return (
                False,
                inserted_count,
                {
                    "error": f"Failed to insert documents: {error_msg}",
                    "details": {
                        "exception_type": type(e).__name__,
                        "inserted_before_error": inserted_count,
                    },
                },
            )


def search_similar_vectors(
    connection: Any, query_vector: list[float], limit: int = 10
) -> tuple[bool, list[dict[str, Any]], dict[str, Any] | None]:
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
            return (
                False,
                [],
                {
                    "error": "Invalid query vector dimension",
                    "details": {"expected": EMBEDDING_DIMENSION, "got": len(query_vector)},
                },
            )

        # Search using cosine similarity
        search_query = f"""
            MATCH (d:{DOCUMENT_TABLE_NAME})
            WITH d, array_cosine_similarity(d.embedding, $query_vector) AS distance
            WHERE distance IS NOT NULL
            RETURN d.id AS id, d.content AS content, distance, d.embedding AS embedding
            ORDER BY distance ASC
            LIMIT $limit
        """

        result = connection.execute(search_query, {"query_vector": query_vector, "limit": limit})

        # Process results
        results = []
        while result.has_next():
            row = result.get_next()
            results.append(
                {"id": row[0], "content": row[1], "distance": float(row[2]), "embedding": row[3]}
            )

        return True, results, None

    except Exception as e:
        error_msg = str(e)
        if "Extension" in error_msg and VECTOR_EXTENSION_NAME in error_msg:
            return (
                False,
                [],
                {
                    "error": "VECTOR extension not available",
                    "details": {
                        "extension": VECTOR_EXTENSION_NAME,
                        "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}",
                        "raw_error": error_msg,
                    },
                },
            )
        elif "dimension" in error_msg.lower():
            return (
                False,
                [],
                {
                    "error": "Vector dimension mismatch",
                    "details": {
                        "expected": EMBEDDING_DIMENSION,
                        "got": len(query_vector),
                        "raw_error": error_msg,
                    },
                },
            )
        else:
            return (
                False,
                [],
                {
                    "error": f"Search failed: {error_msg}",
                    "details": {"exception_type": type(e).__name__},
                },
            )


def count_documents(connection: Any) -> tuple[bool, int, dict[str, Any] | None]:
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
        return (
            False,
            0,
            {
                "error": f"Failed to count documents: {str(e)}",
                "details": {"exception_type": type(e).__name__},
            },
        )


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


def install_fts_extension(connection: Any) -> tuple[bool, dict[str, Any] | None]:
    """
    FTS拡張をインストールおよびロードする

    Args:
        connection: KuzuDB接続オブジェクト

    Returns:
        (success, error_info)
    """
    if connection is None:
        return False, {
            "error": "Connection is None",
            "details": {"message": "Database connection is required"},
        }

    try:
        # Try to install FTS extension
        try:
            connection.execute(f"INSTALL {FTS_EXTENSION_NAME};")
        except Exception:
            # Extension might already be installed
            pass

        # Try to load FTS extension
        try:
            connection.execute(f"LOAD EXTENSION {FTS_EXTENSION_NAME};")
        except Exception:
            # Extension might already be loaded
            pass

        return True, None

    except Exception as e:
        return False, {
            "error": f"Failed to install FTS extension: {str(e)}",
            "details": {"extension": FTS_EXTENSION_NAME, "exception_type": type(e).__name__},
        }


def check_fts_extension(connection: Any) -> tuple[bool, dict[str, Any] | None]:
    """
    FTS拡張が利用可能かチェックする

    Args:
        connection: KuzuDB接続オブジェクト

    Returns:
        (is_available, error_info)
    """
    try:
        # Create a temporary table to test FTS functionality
        temp_table = "_fts_test_table_"
        try:
            connection.execute(
                f"CREATE NODE TABLE {temp_table} (content STRING, PRIMARY KEY (content));"
            )
        except Exception:
            # Table might already exist
            pass

        # Try to use FTS extension by attempting to create a dummy index
        # This will fail if FTS extension is not loaded
        test_query = f"CALL CREATE_FTS_INDEX('{temp_table}', '_test_idx_', ['content']);"
        connection.execute(test_query)

        # Clean up
        try:
            connection.execute(f"CALL DROP_FTS_INDEX('{temp_table}', '_test_idx_');")
        except Exception:
            pass
        try:
            connection.execute(f"DROP TABLE {temp_table};")
        except Exception:
            pass

        return True, None

    except Exception as e:
        error_msg = str(e)
        # Clean up temp table on error
        try:
            connection.execute(f"DROP TABLE {temp_table};")
        except Exception:
            pass

        if any(
            pattern in error_msg.lower()
            for pattern in ["does not exist", "unknown function", "create_fts_index"]
        ):
            return False, {
                "error": "FTS extension not available",
                "details": {
                    "extension": FTS_EXTENSION_NAME,
                    "install_command": f"INSTALL {FTS_EXTENSION_NAME}; LOAD EXTENSION {FTS_EXTENSION_NAME};",
                    "raw_error": error_msg,
                },
            }
        else:
            # For other errors, assume FTS extension is available but something else went wrong
            return True, None


def initialize_fts_schema(connection: Any) -> tuple[bool, dict[str, Any] | None]:
    """
    FTS用のスキーマを初期化する

    Args:
        connection: KuzuDB接続オブジェクト

    Returns:
        (success, error_info)
    """
    if connection is None:
        return False, {
            "error": "Connection is None",
            "details": {"message": "Database connection is required"},
        }

    # Check if FTS extension is available
    fts_available, fts_error = check_fts_extension(connection)
    if not fts_available:
        return False, fts_error

    try:
        # Create Document node table for FTS
        create_table_query = f"""
            CREATE NODE TABLE IF NOT EXISTS {DOCUMENT_TABLE_NAME} (
                id STRING,
                title STRING,
                content STRING,
                PRIMARY KEY (id)
            )
        """
        connection.execute(create_table_query)

        return True, None

    except Exception as e:
        return False, {
            "error": f"Failed to initialize FTS schema: {str(e)}",
            "details": {"exception_type": type(e).__name__, "table_name": DOCUMENT_TABLE_NAME},
        }


def create_fts_index(connection: Any, config: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
    """
    FTSインデックスを作成する

    Args:
        connection: KuzuDB接続オブジェクト
        config: インデックス設定辞書
            - table_name: テーブル名
            - property_name: プロパティ名
            - index_name: インデックス名
            - stopwords (optional): ストップワードリスト
            - stemming (optional): ステミング有効化
            - case_sensitive (optional): 大文字小文字区別

    Returns:
        (success, error_info)
    """
    if connection is None:
        return False, {
            "error": "Connection is None",
            "details": {"message": "Database connection is required"},
        }

    # Extract required parameters
    table_name = config.get("table_name")
    property_name = config.get("property_name")
    index_name = config.get("index_name")

    if not all([table_name, property_name, index_name]):
        return False, {
            "error": "Missing required parameters",
            "details": {
                "required": ["table_name", "property_name", "index_name"],
                "provided": list(config.keys()),
            },
        }

    try:
        # Drop existing index if exists
        try:
            connection.execute(f"CALL DROP_FTS_INDEX('{table_name}', '{index_name}');")
        except Exception:
            # Ignore if index doesn't exist
            pass

        # Create FTS index with CREATE_FTS_INDEX function
        properties = [property_name]  # For now, single property support
        props_str = str(properties).replace("'", '"')
        query = f"CALL CREATE_FTS_INDEX('{table_name}', '{index_name}', {props_str});"
        connection.execute(query)

        # Register the index in our registry
        _FTS_INDEX_REGISTRY[index_name] = {
            "name": index_name,
            "table": table_name,
            "properties": properties,
            "stopwords": config.get("stopwords", []),
            "stemming": config.get("stemming", False),
            "case_sensitive": config.get("case_sensitive", False),
        }

        return True, None

    except Exception as e:
        return False, {
            "error": f"Failed to create FTS index: {str(e)}",
            "details": {
                "exception_type": type(e).__name__,
                "index_name": index_name,
                "table_name": table_name,
            },
        }


def drop_fts_index(connection: Any, index_name: str) -> tuple[bool, dict[str, Any] | None]:
    """
    FTSインデックスを削除する

    Args:
        connection: KuzuDB接続オブジェクト
        index_name: インデックス名

    Returns:
        (success, error_info)
    """
    if connection is None:
        return False, {
            "error": "Connection is None",
            "details": {"message": "Database connection is required"},
        }

    if not index_name:
        return False, {"error": "Index name is required", "details": {"index_name": index_name}}

    try:
        # Drop FTS index
        # Need to find the table name for the index
        # For now, assume it's on Document table
        query = f"CALL DROP_FTS_INDEX('{DOCUMENT_TABLE_NAME}', '{index_name}');"
        connection.execute(query)

        # Remove from registry
        if index_name in _FTS_INDEX_REGISTRY:
            del _FTS_INDEX_REGISTRY[index_name]

        return True, None

    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
            return False, {
                "error": f"FTS index '{index_name}' does not exist",
                "details": {"index_name": index_name},
            }
        else:
            return False, {
                "error": f"Failed to drop FTS index: {error_msg}",
                "details": {"exception_type": type(e).__name__, "index_name": index_name},
            }


def list_fts_indexes(connection: Any) -> tuple[bool, list[dict[str, Any]], dict[str, Any] | None]:
    """
    FTSインデックスの一覧を取得する

    Args:
        connection: KuzuDB接続オブジェクト

    Returns:
        (success, indexes_list, error_info)
    """
    if connection is None:
        return (
            False,
            [],
            {
                "error": "Connection is None",
                "details": {"message": "Database connection is required"},
            },
        )

    try:
        # Return indexes from our registry
        # In production, this should query a metadata table
        indexes = list(_FTS_INDEX_REGISTRY.values())

        return True, indexes, None

    except Exception as e:
        return (
            False,
            [],
            {
                "error": f"Failed to list FTS indexes: {str(e)}",
                "details": {"exception_type": type(e).__name__},
            },
        )


def get_fts_index_info(
    connection: Any, index_name: str
) -> tuple[bool, dict[str, Any] | None, dict[str, Any] | None]:
    """
    FTSインデックスの情報を取得する

    Args:
        connection: KuzuDB接続オブジェクト
        index_name: インデックス名

    Returns:
        (success, index_info, error_info)
    """
    if connection is None:
        return (
            False,
            None,
            {
                "error": "Connection is None",
                "details": {"message": "Database connection is required"},
            },
        )

    if not index_name:
        return (
            False,
            None,
            {"error": "Index name is required", "details": {"index_name": index_name}},
        )

    try:
        # Get FTS index info from registry
        if index_name in _FTS_INDEX_REGISTRY:
            index_info = _FTS_INDEX_REGISTRY[index_name].copy()
            # Add backward compatibility
            if "properties" in index_info and index_info["properties"]:
                index_info["property"] = index_info["properties"][0]
            return True, index_info, None
        else:
            # Return a default structure if not in registry
            index_info = {
                "name": index_name,
                "table": DOCUMENT_TABLE_NAME,
                "properties": ["content"],
                "property": "content",  # Backward compatibility
                "stopwords": [],
                "stemming": False,
                "case_sensitive": False,
            }
            return True, index_info, None

    except Exception as e:
        return (
            False,
            None,
            {
                "error": f"Failed to get FTS index info: {str(e)}",
                "details": {"exception_type": type(e).__name__, "index_name": index_name},
            },
        )


def query_fts_index(
    connection: Any, index_name: str, query: str, limit: int = 10
) -> tuple[bool, list[dict[str, Any]], dict[str, Any] | None]:
    """
    FTSインデックスに対してクエリを実行する

    Args:
        connection: KuzuDB接続オブジェクト
        index_name: インデックス名
        query: 検索クエリ
        limit: 返す結果の最大数

    Returns:
        (success, results, error_info)
    """
    if connection is None:
        return (
            False,
            [],
            {
                "error": "Connection is None",
                "details": {"message": "Database connection is required"},
            },
        )

    if not index_name or not query:
        return (
            False,
            [],
            {
                "error": "Missing required parameters",
                "details": {"index_name": index_name, "query": query},
            },
        )

    try:
        # Execute FTS query using QUERY_FTS_INDEX function
        query_str = f"CALL QUERY_FTS_INDEX('{DOCUMENT_TABLE_NAME}', '{index_name}', '{query}') RETURN id, score ORDER BY score DESC LIMIT {limit};"
        result = connection.execute(query_str)

        # Process results
        results = []
        while result.has_next():
            row = result.get_next()
            # Get document content by ID
            doc_result = connection.execute(
                f"MATCH (d:{DOCUMENT_TABLE_NAME} {{id: $id}}) RETURN d.content, d.title",
                {"id": row[0]},
            )

            if doc_result.has_next():
                doc_row = doc_result.get_next()
                content = doc_row[0] or ""
                title = doc_row[1] or ""
                full_content = f"{title} {content}" if title else content

                results.append(
                    {
                        "id": row[0],
                        "content": full_content,
                        "score": float(row[1]) if row[1] is not None else 0.0,
                    }
                )

        return True, results, None

    except Exception as e:
        error_msg = str(e)
        # If FTS extension is not available or query fails
        return (
            False,
            [],
            {
                "error": f"FTS query failed: {error_msg}",
                "details": {
                    "exception_type": type(e).__name__,
                    "index_name": index_name,
                    "query": query,
                },
            },
        )
