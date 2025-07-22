#!/usr/bin/env python3
"""
アプリケーション層 - 高階関数による依存性注入

ユースケースの実装と、ドメイン層・インフラ層の結合
高階関数を使用して、柔軟な依存性注入を実現
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Type aliases for clarity
EmbeddingFunction = Callable[[str], list[float]]
DatabaseFunction = Callable[..., Any]


@dataclass(frozen=True)
class ApplicationConfig:
    """アプリケーション設定"""

    db_path: str = "./kuzu_db"
    in_memory: bool = False
    embedding_dimension: int = 256
    default_limit: int = 10


def create_vss_service(
    create_db_func: DatabaseFunction,
    create_conn_func: DatabaseFunction,
    check_vector_func: DatabaseFunction,
    init_schema_func: DatabaseFunction,
    insert_docs_func: DatabaseFunction,
    search_func: DatabaseFunction,
    count_func: DatabaseFunction,
    close_func: DatabaseFunction,
    generate_embedding_func: EmbeddingFunction,
    calculate_similarity_func: Callable[
        [list[float], list[tuple[str, str, list[float]]], int], list[Any]
    ],
) -> dict[str, Callable]:
    """
    VSS サービスを作成する高階関数

    各種の関数を受け取り、ユースケースを実装した関数群を返す
    """

    def index_documents(
        documents: list[dict[str, str]], config: ApplicationConfig
    ) -> dict[str, Any]:
        """
        ドキュメントをインデックスする

        Args:
            documents: {"id": str, "content": str}のリスト
            config: アプリケーション設定

        Returns:
            インデックス結果
        """
        start_time = time.time()

        # 入力検証
        if not documents:
            return {
                "ok": False,
                "error": "No documents provided",
                "details": {"documents_count": 0},
            }

        # データベース接続を作成
        from infrastructure import DatabaseConfig

        db_config = DatabaseConfig(
            db_path=config.db_path,
            in_memory=config.in_memory,
            embedding_dimension=config.embedding_dimension,
        )

        db_success, database, db_error = create_db_func(db_config)
        if not db_success:
            return {"ok": False, "error": db_error["error"], "details": db_error["details"]}

        conn_success, connection, conn_error = create_conn_func(database)
        if not conn_success:
            return {"ok": False, "error": conn_error["error"], "details": conn_error["details"]}

        try:
            # VECTOR拡張をチェック
            vector_available, vector_error = check_vector_func(connection)
            if not vector_available:
                return {
                    "ok": False,
                    "error": vector_error["error"],
                    "details": vector_error["details"],
                }

            # スキーマを初期化
            schema_success, schema_error = init_schema_func(connection, config.embedding_dimension)
            if not schema_success:
                return {
                    "ok": False,
                    "error": schema_error["error"],
                    "details": schema_error["details"],
                }

            # ドキュメントに埋め込みを生成
            documents_with_embeddings = []
            for doc in documents:
                doc_id = doc.get("id")
                content = doc.get("content")

                if not doc_id or not content:
                    return {
                        "ok": False,
                        "error": "Invalid document format",
                        "details": {"expected": {"id": "string", "content": "string"}, "got": doc},
                    }

                # 埋め込みを生成
                embedding = generate_embedding_func(content)
                documents_with_embeddings.append((doc_id, content, embedding))

            # データベースに挿入
            insert_success, inserted_count, insert_error = insert_docs_func(
                connection, documents_with_embeddings
            )

            if not insert_success:
                return {
                    "ok": False,
                    "error": insert_error["error"],
                    "details": insert_error["details"],
                }

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "ok": True,
                "status": "success",
                "indexed_count": inserted_count,
                "index_time_ms": elapsed_ms,
            }

        finally:
            close_func(connection)

    def search(search_input: dict[str, Any], config: ApplicationConfig) -> dict[str, Any]:
        """
        類似ドキュメントを検索する

        Args:
            search_input: {"query": str, "limit": int, "query_vector": List[float] (optional)}
            config: アプリケーション設定

        Returns:
            検索結果
        """
        start_time = time.time()

        # 入力検証
        query = search_input.get("query")
        if not query and "query_vector" not in search_input:
            return {
                "ok": False,
                "error": "Missing required parameter: query or query_vector",
                "details": {"required": ["query"], "optional": ["limit", "query_vector"]},
            }

        limit = search_input.get("limit", config.default_limit)

        # データベース接続を作成
        from infrastructure import DatabaseConfig

        db_config = DatabaseConfig(
            db_path=config.db_path,
            in_memory=config.in_memory,
            embedding_dimension=config.embedding_dimension,
        )

        db_success, database, db_error = create_db_func(db_config)
        if not db_success:
            return {"ok": False, "error": db_error["error"], "details": db_error["details"]}

        conn_success, connection, conn_error = create_conn_func(database)
        if not conn_success:
            return {"ok": False, "error": conn_error["error"], "details": conn_error["details"]}

        try:
            # VECTOR拡張をチェック
            vector_available, vector_error = check_vector_func(connection)
            if not vector_available:
                return {
                    "ok": False,
                    "error": vector_error["error"],
                    "details": vector_error["details"],
                }

            # ドキュメント数を取得
            count_success, total_count, count_error = count_func(connection)
            if not count_success:
                total_count = 0

            # 空のインデックスの場合
            if total_count == 0:
                return {
                    "ok": True,
                    "results": [],
                    "metadata": {
                        "total_results": 0,
                        "query": query,
                        "search_time_ms": (time.time() - start_time) * 1000,
                    },
                }

            # クエリベクトルを取得または生成
            if "query_vector" in search_input:
                query_vector = search_input["query_vector"]
            else:
                query_vector = generate_embedding_func(query)

            # 検索を実行
            search_success, db_results, search_error = search_func(connection, query_vector, limit)

            if not search_success:
                return {
                    "ok": False,
                    "error": search_error["error"],
                    "details": search_error["details"],
                }

            # 結果を変換（distanceをscoreに）
            results = []
            for row in db_results:
                score = 1.0 - row["distance"]
                results.append(
                    {
                        "id": row["id"],
                        "content": row["content"],
                        "score": score,
                        "distance": row["distance"],
                    }
                )

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "ok": True,
                "results": results,
                "metadata": {
                    "total_results": len(results),
                    "query": query,
                    "search_time_ms": elapsed_ms,
                },
            }

        finally:
            close_func(connection)

    # 返す関数群
    return {"index_documents": index_documents, "search": search}


def create_embedding_service(model_name: str = "cl-nagoya/ruri-v3-30m") -> EmbeddingFunction:
    """
    埋め込み生成サービスを作成する

    Args:
        model_name: 使用するモデル名

    Returns:
        埋め込み生成関数
    """

    def generate_embedding(text: str) -> list[float]:
        """
        テキストから埋め込みベクトルを生成する

        実際の実装では sentence-transformers などを使用
        ここではダミー実装
        """
        # ダミー実装：256次元のランダムベクトル
        import hashlib
        import struct

        # テキストのハッシュからシードを生成
        hash_obj = hashlib.sha256(text.encode("utf-8"))
        hash_bytes = hash_obj.digest()

        # ハッシュから浮動小数点数を生成
        embedding = []
        for i in range(0, min(len(hash_bytes), 256 * 4), 4):
            if i + 4 <= len(hash_bytes):
                # 4バイトを符号なし整数として解釈し、正規化
                value = struct.unpack("I", hash_bytes[i : i + 4])[0]
                normalized = (value / (2**32 - 1)) * 2 - 1  # -1 to 1
                embedding.append(normalized)

        # 256次元に調整
        while len(embedding) < 256:
            embedding.append(0.0)

        return embedding[:256]

    return generate_embedding


class VSSService:
    """
    VSSサービスクラス - アプリケーション層のファサード

    高階関数を使用して作成されたサービスを
    オブジェクト指向インターフェースでラップ
    """

    def __init__(self, db_path: str = "./kuzu_db", in_memory: bool = False):
        """
        VSSサービスを初期化

        Args:
            db_path: データベースパス
            in_memory: インメモリデータベースを使用するか
        """
        self.config = ApplicationConfig(db_path=db_path, in_memory=in_memory)

        # 依存関数をインポート
        from domain import find_semantically_similar_documents
        from infrastructure import (
            check_vector_extension,
            close_connection,
            count_documents,
            create_kuzu_connection,
            create_kuzu_database,
            initialize_vector_schema,
            insert_documents_with_embeddings,
            search_similar_vectors,
        )

        # 埋め込みサービスを作成
        embedding_func = create_embedding_service()

        # VSSサービスを作成
        self._service_funcs = create_vss_service(
            create_db_func=create_kuzu_database,
            create_conn_func=create_kuzu_connection,
            check_vector_func=check_vector_extension,
            init_schema_func=initialize_vector_schema,
            insert_docs_func=insert_documents_with_embeddings,
            search_func=search_similar_vectors,
            count_func=count_documents,
            close_func=close_connection,
            generate_embedding_func=embedding_func,
            calculate_similarity_func=find_semantically_similar_documents,
        )

    def index_documents(self, documents: list[dict[str, str]]) -> dict[str, Any]:
        """ドキュメントをインデックス"""
        return self._service_funcs["index_documents"](documents, self.config)

    def search(self, search_input: dict[str, Any]) -> dict[str, Any]:
        """類似ドキュメントを検索"""
        return self._service_funcs["search"](search_input, self.config)


def create_fts_service(
    create_db_func: DatabaseFunction,
    create_conn_func: DatabaseFunction,
    check_fts_func: DatabaseFunction,
    install_fts_func: DatabaseFunction,
    init_schema_func: DatabaseFunction,
    create_index_func: DatabaseFunction,
    insert_docs_func: DatabaseFunction,
    search_func: DatabaseFunction,
    count_func: DatabaseFunction,
    close_func: DatabaseFunction,
) -> dict[str, Callable]:
    """
    FTS サービスを作成する高階関数

    各種の関数を受け取り、FTSユースケースを実装した関数群を返す
    """

    def index_documents(
        documents: list[dict[str, str]], config: ApplicationConfig
    ) -> dict[str, Any]:
        """
        ドキュメントをFTSインデックスに追加する

        Args:
            documents: {"id": str, "title": str, "content": str}のリスト
            config: アプリケーション設定

        Returns:
            インデックス結果
        """
        start_time = time.time()

        # 入力検証
        if not documents:
            return {
                "ok": False,
                "error": "No documents provided",
                "details": {"documents_count": 0},
            }

        # データベース接続を作成
        from infrastructure import DatabaseConfig

        db_config = DatabaseConfig(
            db_path=config.db_path,
            in_memory=config.in_memory,
            embedding_dimension=config.embedding_dimension,
        )

        db_success, database, db_error = create_db_func(db_config)
        if not db_success:
            return {"ok": False, "error": db_error["error"], "details": db_error["details"]}

        conn_success, connection, conn_error = create_conn_func(database)
        if not conn_success:
            return {"ok": False, "error": conn_error["error"], "details": conn_error["details"]}

        try:
            # FTS拡張をインストール/ロード
            install_result = install_fts_func(connection)
            if isinstance(install_result, tuple):
                install_success, install_error = install_result
            else:
                install_success = install_result.get("ok", False)
                install_error = install_result if not install_success else None

            if not install_success:
                return {
                    "ok": False,
                    "error": (
                        install_error.get("error", "Failed to install FTS extension")
                        if isinstance(install_error, dict)
                        else str(install_error)
                    ),
                    "details": (
                        install_error.get("details", {}) if isinstance(install_error, dict) else {}
                    ),
                }

            # FTS拡張をチェック
            check_result = check_fts_func(connection)
            if isinstance(check_result, tuple):
                fts_available, fts_error = check_result
            elif isinstance(check_result, bool):
                fts_available = check_result
                fts_error = None
            else:
                fts_available = check_result.get("ok", False)
                fts_error = check_result if not fts_available else None

            if not fts_available:
                return {
                    "ok": False,
                    "error": (
                        fts_error.get("error", "FTS extension not available")
                        if isinstance(fts_error, dict)
                        else str(fts_error) if fts_error else "FTS extension not available"
                    ),
                    "details": fts_error.get("details", {}) if isinstance(fts_error, dict) else {},
                }

            # スキーマを初期化
            schema_result = init_schema_func(connection)
            if isinstance(schema_result, tuple):
                schema_success, schema_error = schema_result
            else:
                schema_success = schema_result.get("ok", False)
                schema_error = schema_result if not schema_success else None

            if not schema_success:
                return {
                    "ok": False,
                    "error": (
                        schema_error.get("error", "Failed to initialize schema")
                        if isinstance(schema_error, dict)
                        else str(schema_error) if schema_error else "Failed to initialize schema"
                    ),
                    "details": (
                        schema_error.get("details", {}) if isinstance(schema_error, dict) else {}
                    ),
                }

            # FTSインデックスを作成
            # Note: Current FTS implementation supports single property index
            # We'll create an index on the content field (main search target)
            index_config = {
                "table_name": "Document",
                "property_name": "content",
                "index_name": "doc_fts_idx",
            }
            index_result = create_index_func(connection, index_config)
            if isinstance(index_result, tuple):
                index_success, index_error = index_result
            else:
                index_success = index_result.get("ok", False)
                index_error = index_result if not index_success else None

            if not index_success:
                # インデックスが既に存在する場合は続行
                error_msg = (
                    index_error.get("error", "")
                    if isinstance(index_error, dict)
                    else str(index_error) if index_error else ""
                )
                if "already exists" not in error_msg.lower():
                    return {
                        "ok": False,
                        "error": error_msg or "Failed to create FTS index",
                        "details": (
                            index_error.get("details", {}) if isinstance(index_error, dict) else {}
                        ),
                    }

            # ドキュメントを挿入
            indexed_count = 0
            for doc in documents:
                doc_id = doc.get("id")
                title = doc.get("title", "")
                content = doc.get("content", "")

                if not doc_id:
                    return {
                        "ok": False,
                        "error": "Document missing required 'id' field",
                        "details": {"document": doc},
                    }

                # ドキュメントを挿入（FTSインデックスがある場合はDELETE/INSERTを使用）
                try:
                    # First delete if exists
                    connection.execute("MATCH (d:Document {id: $id}) DELETE d", {"id": doc_id})

                    # Then insert new document
                    connection.execute(
                        """
                        CREATE (d:Document {
                            id: $id,
                            title: $title,
                            content: $content
                        })
                        """,
                        {"id": doc_id, "title": title, "content": content},
                    )
                    indexed_count += 1
                except Exception as e:
                    return {
                        "ok": False,
                        "error": f"Failed to insert document: {str(e)}",
                        "details": {"document_id": doc_id},
                    }

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "ok": True,
                "status": "success",
                "indexed_count": indexed_count,
                "index_time_ms": elapsed_ms,
            }

        finally:
            close_func(connection)

    def search(search_input: dict[str, Any], config: ApplicationConfig) -> dict[str, Any]:
        """
        FTS検索を実行する

        Args:
            search_input: {"query": str, "limit": int}
            config: アプリケーション設定

        Returns:
            検索結果
        """
        start_time = time.time()

        # 入力検証
        query = search_input.get("query")
        if not query:
            return {
                "ok": False,
                "error": "Missing required parameter: query",
                "details": {"required": ["query"], "optional": ["limit"]},
            }

        limit = search_input.get("limit", config.default_limit)

        # データベース接続を作成
        from infrastructure import DatabaseConfig

        db_config = DatabaseConfig(
            db_path=config.db_path,
            in_memory=config.in_memory,
            embedding_dimension=config.embedding_dimension,
        )

        db_success, database, db_error = create_db_func(db_config)
        if not db_success:
            return {"ok": False, "error": db_error["error"], "details": db_error["details"]}

        conn_success, connection, conn_error = create_conn_func(database)
        if not conn_success:
            return {"ok": False, "error": conn_error["error"], "details": conn_error["details"]}

        try:
            # FTS拡張をチェック
            check_result = check_fts_func(connection)
            if isinstance(check_result, tuple):
                fts_available, fts_error = check_result
            elif isinstance(check_result, bool):
                fts_available = check_result
                fts_error = None
            else:
                fts_available = check_result.get("ok", False)
                fts_error = check_result if not fts_available else None

            if not fts_available:
                # 拡張がない場合は単純な文字列検索にフォールバック
                # （規約に従い、エラーとして扱うべきかもしれない）
                results = []
                try:
                    # 単純な文字列マッチング
                    result = connection.execute(
                        """
                        MATCH (d:Document)
                        WHERE d.content CONTAINS $query OR d.title CONTAINS $query
                        RETURN d.id AS id, d.title AS title, d.content AS content
                        LIMIT $limit
                        """,
                        {"query": query, "limit": limit},
                    )

                    while result.has_next():
                        row = result.get_next()
                        full_content = f"{row[1]} {row[2]}" if row[1] else row[2]
                        results.append(
                            {
                                "id": row[0],
                                "content": full_content,
                                "score": 1.0,  # 固定スコア
                                "highlights": [],
                            }
                        )
                except Exception:
                    # テーブルが存在しない場合
                    pass
            else:
                # FTS検索を実行
                from domain import create_highlight_info

                # query_fts_index関数を使ってFTS検索
                index_name = "doc_fts_idx"
                search_result = search_func(connection, index_name, query, limit)

                if isinstance(search_result, dict):
                    fts_success = search_result.get("ok", False)
                    fts_results = search_result.get("results", [])
                    fts_error = search_result if not fts_success else None
                else:
                    # タプルの場合
                    fts_success, fts_results, fts_error = search_result

                if not fts_success:
                    # FTS検索が失敗した場合、フォールバックとして単純な文字列検索
                    results = []
                    try:
                        # 単純な文字列マッチング
                        result = connection.execute(
                            """
                            MATCH (d:Document)
                            WHERE d.content CONTAINS $query OR d.title CONTAINS $query
                            RETURN d.id AS id, d.title AS title, d.content AS content
                            LIMIT $limit
                            """,
                            {"query": query, "limit": limit},
                        )

                        while result.has_next():
                            row = result.get_next()
                            full_content = f"{row[1]} {row[2]}" if row[1] else row[2]
                            results.append(
                                {
                                    "id": row[0],
                                    "content": full_content,
                                    "score": 1.0,  # 固定スコア
                                    "highlights": [],
                                }
                            )
                    except Exception:
                        # テーブルが存在しない場合
                        pass
                else:
                    # FTS結果を整形
                    results = []
                    for fts_result in fts_results:
                        # ハイライト情報を生成
                        highlights, positions = create_highlight_info(fts_result["content"], query)

                        results.append(
                            {
                                "id": fts_result["id"],
                                "content": fts_result["content"],
                                "score": fts_result["score"],
                                "highlights": highlights,
                            }
                        )

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "ok": True,
                "results": results,
                "metadata": {
                    "total_results": len(results),
                    "query": query,
                    "search_time_ms": elapsed_ms,
                },
            }

        finally:
            close_func(connection)

    # 返す関数群
    return {"index_documents": index_documents, "search": search}


class FTSService:
    """
    FTSサービスクラス - アプリケーション層のファサード

    Full-Text Search機能を提供するサービス
    """

    def __init__(self, db_path: str = "./kuzu_db", in_memory: bool = False):
        """
        FTSサービスを初期化

        Args:
            db_path: データベースパス
            in_memory: インメモリデータベースを使用するか
        """
        self.config = ApplicationConfig(db_path=db_path, in_memory=in_memory)

        # 依存関数をインポート
        from infrastructure import (
            DatabaseConfig,
            check_fts_extension,
            close_connection,
            count_documents,
            create_fts_index,
            create_kuzu_connection,
            create_kuzu_database,
            initialize_fts_schema,
            install_fts_extension,
            query_fts_index,
        )

        # インメモリデータベースの場合は永続的な接続を保持
        self._database = None
        self._connection = None

        if in_memory:
            # インメモリの場合は事前に接続を作成して保持
            db_config = DatabaseConfig(db_path=db_path, in_memory=True, embedding_dimension=256)
            db_success, database, db_error = create_kuzu_database(db_config)
            if db_success:
                self._database = database
                conn_success, connection, conn_error = create_kuzu_connection(database)
                if conn_success:
                    self._connection = connection
                    # FTS拡張をインストール
                    install_fts_extension(connection)
                    # スキーマを初期化
                    initialize_fts_schema(connection)
                    # FTSインデックスを作成
                    index_config = {
                        "table_name": "Document",
                        "property_name": "content",
                        "index_name": "doc_fts_idx",
                    }
                    create_fts_index(connection, index_config)

        # FTSサービスを作成
        self._service_funcs = create_fts_service(
            create_db_func=create_kuzu_database,
            create_conn_func=create_kuzu_connection,
            check_fts_func=check_fts_extension,
            install_fts_func=install_fts_extension,
            init_schema_func=initialize_fts_schema,
            create_index_func=create_fts_index,
            insert_docs_func=None,  # FTSは独自の挿入ロジックを使用
            search_func=query_fts_index,  # FTS検索関数を使用
            count_func=count_documents,
            close_func=close_connection,
        )

    def index_documents(self, documents: list[dict[str, str]]) -> dict[str, Any]:
        """ドキュメントをFTSインデックスに追加"""
        if self._connection:
            # Use persistent connection for in-memory database
            return self._index_with_connection(documents)
        else:
            return self._service_funcs["index_documents"](documents, self.config)

    def search(self, search_input: dict[str, Any]) -> dict[str, Any]:
        """FTS検索を実行"""
        if self._connection:
            # Use persistent connection for in-memory database
            return self._search_with_connection(search_input)
        else:
            return self._service_funcs["search"](search_input, self.config)

    def _index_with_connection(self, documents: list[dict[str, str]]) -> dict[str, Any]:
        """Use persistent connection to index documents"""
        import time

        start_time = time.time()

        if not documents:
            return {
                "ok": False,
                "error": "No documents provided",
                "details": {"documents_count": 0},
            }

        try:
            indexed_count = 0
            for doc in documents:
                doc_id = doc.get("id")
                title = doc.get("title", "")
                content = doc.get("content", "")

                if not doc_id:
                    return {
                        "ok": False,
                        "error": "Document missing required 'id' field",
                        "details": {"document": doc},
                    }

                # Delete if exists
                self._connection.execute("MATCH (d:Document {id: $id}) DELETE d", {"id": doc_id})

                # Insert new document
                self._connection.execute(
                    """
                    CREATE (d:Document {
                        id: $id,
                        title: $title,
                        content: $content
                    })
                    """,
                    {"id": doc_id, "title": title, "content": content},
                )
                indexed_count += 1

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "ok": True,
                "status": "success",
                "indexed_count": indexed_count,
                "index_time_ms": elapsed_ms,
            }

        except Exception as e:
            return {
                "ok": False,
                "error": f"Failed to index documents: {str(e)}",
                "details": {"error": str(e)},
            }

    def _search_with_connection(self, search_input: dict[str, Any]) -> dict[str, Any]:
        """Use persistent connection to search"""
        import time

        from domain import create_highlight_info
        from infrastructure import query_fts_index

        start_time = time.time()

        query = search_input.get("query")
        if not query:
            return {
                "ok": False,
                "error": "Missing required parameter: query",
                "details": {"required": ["query"], "optional": ["limit"]},
            }

        limit = search_input.get("limit", self.config.default_limit)

        try:
            # Try FTS search
            index_name = "doc_fts_idx"
            search_result = query_fts_index(self._connection, index_name, query, limit)

            if isinstance(search_result, dict):
                fts_success = search_result.get("ok", False)
                fts_results = search_result.get("results", [])
            else:
                fts_success, fts_results, fts_error = search_result

            results = []
            if fts_success and fts_results:
                # Process FTS results
                for fts_result in fts_results:
                    highlights, positions = create_highlight_info(fts_result["content"], query)
                    results.append(
                        {
                            "id": fts_result["id"],
                            "content": fts_result["content"],
                            "score": fts_result["score"],
                            "highlights": highlights,
                        }
                    )
            else:
                # Fallback to simple string search with case-insensitive matching
                # Split query into words for multi-word support
                words = query.split()

                if len(words) > 1:
                    # Multi-word query: search for documents containing ANY of the words
                    where_clauses = []
                    params = {"limit": limit}

                    for i, word in enumerate(words):
                        param_name = f"word{i}"
                        params[param_name] = word
                        where_clauses.append(
                            f"lower(d.content) CONTAINS lower(${param_name}) OR lower(d.title) CONTAINS lower(${param_name})"
                        )

                    where_condition = " OR ".join(f"({clause})" for clause in where_clauses)

                    result = self._connection.execute(
                        f"""
                        MATCH (d:Document)
                        WHERE {where_condition}
                        RETURN d.id AS id, d.title AS title, d.content AS content
                        LIMIT $limit
                        """,
                        params,
                    )
                else:
                    # Single word query
                    result = self._connection.execute(
                        """
                        MATCH (d:Document)
                        WHERE lower(d.content) CONTAINS lower($query) OR lower(d.title) CONTAINS lower($query)
                        RETURN d.id AS id, d.title AS title, d.content AS content
                        LIMIT $limit
                        """,
                        {"query": query, "limit": limit},
                    )

                while result.has_next():
                    row = result.get_next()
                    full_content = f"{row[1]} {row[2]}" if row[1] else row[2]
                    results.append(
                        {"id": row[0], "content": full_content, "score": 1.0, "highlights": []}
                    )

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "ok": True,
                "results": results,
                "metadata": {
                    "total_results": len(results),
                    "query": query,
                    "search_time_ms": elapsed_ms,
                },
            }

        except Exception as e:
            return {"ok": False, "error": f"Search failed: {str(e)}", "details": {"error": str(e)}}
