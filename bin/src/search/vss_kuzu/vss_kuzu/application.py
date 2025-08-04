#!/usr/bin/env python3
"""
アプリケーション層 - 高階関数による依存性注入

ユースケースの実装と、ドメイン層・インフラ層の結合
高階関数を使用して、柔軟な依存性注入を実現
"""

import time
from typing import Dict, Any, List, Optional, Callable, Tuple, TypedDict
from log_py import log

from .protocols import VSSAlgebra

# Type aliases for clarity
EmbeddingFunction = Callable[[str], List[float]]
DatabaseFunction = Callable[..., Any]


class ApplicationConfig(TypedDict, total=False):
    """アプリケーション設定"""
    db_path: str
    in_memory: bool
    embedding_dimension: int
    default_limit: int
    index_mu: int
    index_ml: int
    index_metric: str
    index_efc: int
    existing_connection: Optional[Any]


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
    calculate_similarity_func: Callable[[List[float], List[Tuple[str, str, List[float]]], int], List[Any]]
) -> Dict[str, Callable]:
    """
    VSS サービスを作成する高階関数
    
    各種の関数を受け取り、ユースケースを実装した関数群を返す
    """
    
    def index_documents(documents: List[Dict[str, str]], config: Any) -> Dict[str, Any]:
        """
        ドキュメントをインデックスする
        
        Args:
            documents: {"id": str, "content": str}のリスト
            config: アプリケーション設定
            
        Returns:
            インデックス結果
        """
        start_time = time.time()
        
        log("info", {
            "message": "Starting document indexing",
            "component": "vss.application",
            "operation": "index_documents",
            "document_count": len(documents)
        })
        
        # 入力検証
        if not documents:
            log("warning", {
                "message": "No documents provided for indexing",
                "component": "vss.application",
                "operation": "index_documents",
                "document_count": 0
            })
            return {
                "ok": False,
                "error": "No documents provided",
                "details": {"documents_count": 0}
            }
        
        # データベース接続を作成
        # DatabaseConfig is now a TypedDict, no need to import
        
        # Handle both dict and VSSConfig objects
        if hasattr(config, '__dict__'):
            # It's a dataclass/object, convert to dict-like access
            db_path = getattr(config, 'db_path', './kuzu_db')
            in_memory = getattr(config, 'in_memory', False)
            embedding_dimension = getattr(config, 'embedding_dimension', 256)
            existing_conn = getattr(config, 'existing_connection', None)
        else:
            # It's a dict
            db_path = config.get('db_path', './kuzu_db')
            in_memory = config.get('in_memory', False)
            embedding_dimension = config.get('embedding_dimension', 256)
            existing_conn = config.get('existing_connection')
        
        # 既存接続があれば使用、なければ新規作成
        if existing_conn:
            connection = existing_conn
            should_close = False
        else:
            db_config = {
                'db_path': db_path,
                'in_memory': in_memory,
                'embedding_dimension': embedding_dimension
            }
            
            db_success, database, db_error = create_db_func(db_config)
            if not db_success:
                log("error", {
                    "message": "Failed to create database",
                    "component": "vss.application",
                    "operation": "index_documents",
                    "error": db_error["error"],
                    "details": db_error["details"]
                })
                return {
                    "ok": False,
                    "error": db_error["error"],
                    "details": db_error["details"]
                }
            
            conn_success, connection, conn_error = create_conn_func(database)
            if not conn_success:
                log("error", {
                    "message": "Failed to create connection",
                    "component": "vss.application",
                    "operation": "index_documents",
                    "error": conn_error["error"],
                    "details": conn_error["details"]
                })
                return {
                    "ok": False,
                    "error": conn_error["error"],
                    "details": conn_error["details"]
                }
            should_close = True
        
        try:
            # VECTOR拡張をチェック
            vector_available, vector_error = check_vector_func(connection)
            if not vector_available:
                log("error", {
                    "message": "VECTOR extension not available",
                    "component": "vss.application",
                    "operation": "index_documents",
                    "error": vector_error["error"],
                    "details": vector_error["details"]
                })
                return {
                    "ok": False,
                    "error": vector_error["error"],
                    "details": vector_error["details"]
                }
            
            # スキーマを初期化（HNSWパラメータを含む）
            if hasattr(config, '__dict__'):
                # It's a dataclass/object
                schema_success, schema_error = init_schema_func(
                    connection, 
                    getattr(config, 'embedding_dimension', 256),
                    getattr(config, 'index_mu', 30),
                    getattr(config, 'index_ml', 60),
                    getattr(config, 'index_metric', 'cosine'),
                    getattr(config, 'index_efc', 200)
                )
            else:
                # It's a dict
                schema_success, schema_error = init_schema_func(
                    connection, 
                    config.get('embedding_dimension', 256),
                    config.get('index_mu', 30),
                    config.get('index_ml', 60),
                    config.get('index_metric', 'cosine'),
                    config.get('index_efc', 200)
                )
            if not schema_success:
                log("error", {
                    "message": "Failed to initialize schema",
                    "component": "vss.application",
                    "operation": "index_documents",
                    "error": schema_error["error"],
                    "details": schema_error["details"]
                })
                return {
                    "ok": False,
                    "error": schema_error["error"],
                    "details": schema_error["details"]
                }
            
            # ドキュメントに埋め込みを生成
            documents_with_embeddings = []
            for doc in documents:
                doc_id = doc.get("id")
                content = doc.get("content")
                
                if not doc_id or not content:
                    log("error", {
                        "message": "Invalid document format",
                        "component": "vss.application",
                        "operation": "index_documents",
                        "document": doc
                    })
                    return {
                        "ok": False,
                        "error": "Invalid document format",
                        "details": {
                            "expected": {"id": "string", "content": "string"},
                            "got": doc
                        }
                    }
                
                # 埋め込みを生成
                embedding = generate_embedding_func(content)
                documents_with_embeddings.append((doc_id, content, embedding))
            
            # データベースに挿入
            insert_success, inserted_count, insert_error = insert_docs_func(
                connection, documents_with_embeddings
            )
            
            if not insert_success:
                log("error", {
                    "message": "Failed to insert documents",
                    "component": "vss.application",
                    "operation": "index_documents",
                    "error": insert_error["error"],
                    "details": insert_error["details"]
                })
                return {
                    "ok": False,
                    "error": insert_error["error"],
                    "details": insert_error["details"]
                }
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            log("info", {
                "message": "Successfully indexed documents",
                "component": "vss.application",
                "operation": "index_documents",
                "indexed_count": inserted_count,
                "index_time_ms": elapsed_ms
            })
            
            return {
                "ok": True,
                "status": "success",
                "indexed_count": inserted_count,
                "index_time_ms": elapsed_ms
            }
            
        finally:
            # 自分で作成した接続のみクローズ
            if should_close:
                close_func(connection)
    
    def search(search_input: Dict[str, Any], config: Any) -> Dict[str, Any]:
        """
        類似ドキュメントを検索する
        
        Args:
            search_input: {"query": str, "limit": int, "query_vector": List[float] (optional), "efs": int (optional)}
            config: アプリケーション設定
            
        Returns:
            検索結果
        """
        start_time = time.time()
        
        # 入力検証
        query = search_input.get("query")
        if not query and "query_vector" not in search_input:
            log("error", {
                "message": "Missing required search parameter",
                "component": "vss.application",
                "operation": "search",
                "error": "Missing required parameter: query or query_vector",
                "search_input_keys": list(search_input.keys())
            })
            return {
                "ok": False,
                "error": "Missing required parameter: query or query_vector",
                "details": {
                    "required": ["query"],
                    "optional": ["limit", "query_vector", "efs"]
                }
            }
        
        # Handle both dict and VSSConfig objects for default_limit
        if hasattr(config, '__dict__'):
            default_limit = getattr(config, 'default_limit', 10)
        else:
            default_limit = config.get('default_limit', 10)
        limit = search_input.get("limit", default_limit)
        efs = search_input.get("efs", 200)  # Default efs value
        
        # Log search query received (without exposing sensitive data)
        log("info", {
            "message": "Search query received",
            "component": "vss.application",
            "operation": "search",
            "has_query": bool(query),
            "has_query_vector": "query_vector" in search_input,
            "limit": limit,
            "efs": efs
        })
        
        # データベース接続を作成
        # DatabaseConfig is now a TypedDict, no need to import
        
        # Handle both dict and VSSConfig objects
        if hasattr(config, '__dict__'):
            # It's a dataclass/object, convert to dict-like access
            db_path = getattr(config, 'db_path', './kuzu_db')
            in_memory = getattr(config, 'in_memory', False)
            embedding_dimension = getattr(config, 'embedding_dimension', 256)
            existing_conn = getattr(config, 'existing_connection', None)
        else:
            # It's a dict
            db_path = config.get('db_path', './kuzu_db')
            in_memory = config.get('in_memory', False)
            embedding_dimension = config.get('embedding_dimension', 256)
            existing_conn = config.get('existing_connection')
        
        # 既存接続があれば使用、なければ新規作成
        if existing_conn:
            connection = existing_conn
            should_close = False
        else:
            db_config = {
                'db_path': db_path,
                'in_memory': in_memory,
                'embedding_dimension': embedding_dimension
            }
            
            db_success, database, db_error = create_db_func(db_config)
            if not db_success:
                log("error", {
                    "message": "Failed to create database for search",
                    "component": "vss.application",
                    "operation": "search",
                    "error": db_error.get("error", "Unknown error"),
                    "details": db_error.get("details", {})
                })
                return {
                    "ok": False,
                    "error": db_error["error"],
                    "details": db_error["details"]
                }
            
            conn_success, connection, conn_error = create_conn_func(database)
            if not conn_success:
                log("error", {
                    "message": "Failed to create connection for search",
                    "component": "vss.application",
                    "operation": "search",
                    "error": conn_error.get("error", "Unknown error"),
                    "details": conn_error.get("details", {})
                })
                return {
                    "ok": False,
                    "error": conn_error["error"],
                    "details": conn_error["details"]
                }
            should_close = True
        
        try:
            # VECTOR拡張をチェック
            vector_available, vector_error = check_vector_func(connection)
            if not vector_available:
                log("error", {
                    "message": "VECTOR extension not available for search",
                    "component": "vss.application",
                    "operation": "search",
                    "error": vector_error.get("error", "Unknown error"),
                    "details": vector_error.get("details", {})
                })
                return {
                    "ok": False,
                    "error": vector_error["error"],
                    "details": vector_error["details"]
                }
            
            # ドキュメント数を取得
            from .infrastructure import DOCUMENT_TABLE_NAME
            count_success, total_count, count_error = count_func(connection, DOCUMENT_TABLE_NAME)
            if not count_success:
                total_count = 0
            
            # 空のインデックスの場合
            if total_count == 0:
                log("info", {
                    "message": "Search on empty index",
                    "component": "vss.application",
                    "operation": "search",
                    "total_documents": 0
                })
                return {
                    "ok": True,
                    "results": [],
                    "metadata": {
                        "total_results": 0,
                        "query": query,
                        "search_time_ms": (time.time() - start_time) * 1000
                    }
                }
            
            # クエリベクトルを取得または生成
            if "query_vector" in search_input:
                query_vector = search_input["query_vector"]
            else:
                query_vector = generate_embedding_func(query)
            
            # 検索を実行（efsパラメータを含む）
            log("info", {
                "message": "Executing vector search",
                "component": "vss.application",
                "operation": "search",
                "limit": limit,
                "efs": efs,
                "vector_dimension": len(query_vector) if query_vector else 0
            })
            
            search_success, db_results, search_error = search_func(
                connection, query_vector, limit, efs
            )
            
            if not search_success:
                log("error", {
                    "message": "Search execution failed",
                    "component": "vss.application",
                    "operation": "search",
                    "error": search_error.get("error", "Unknown error"),
                    "details": search_error.get("details", {})
                })
                return {
                    "ok": False,
                    "error": search_error["error"],
                    "details": search_error["details"]
                }
            
            results = []
            for row in db_results:
                score = 1.0 - row["distance"]
                results.append({
                    "id": row["id"],
                    "content": row["content"],
                    "score": score,
                    "distance": row["distance"]
                })
            
            # スコアの降順でソート
            results.sort(key=lambda r: r["score"], reverse=True)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Log successful search completion
            log("info", {
                "message": "Search completed successfully",
                "component": "vss.application",
                "operation": "search",
                "results_count": len(results),
                "search_time_ms": elapsed_ms,
                "has_query": bool(query),
                "limit_requested": limit,
                "efs": efs
            })
            
            return {
                "ok": True,
                "results": results,
                "metadata": {
                    "total_results": len(results),
                    "query": query,
                    "search_time_ms": elapsed_ms
                }
            }
            
        finally:
            # 自分で作成した接続のみクローズ
            if should_close:
                close_func(connection)
    
    return {
        "index_documents": index_documents,
        "search": search
    }


def create_embedding_service(model_name: str = "cl-nagoya/ruri-v3-30m") -> EmbeddingFunction:
    """
    埋め込み生成サービスを作成する
    
    Args:
        model_name: 使用するモデル名
        
    Returns:
        埋め込み生成関数
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        
        embedding_dim = model.get_sentence_embedding_dimension()
        
        def generate_embedding_with_model(text: str) -> List[float]:
            """
            sentence-transformersを使用して埋め込みを生成
            """
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        
        generate_embedding_with_model.dimension = embedding_dim
        
        return generate_embedding_with_model
        
    except ImportError:
        def generate_embedding(text: str) -> List[float]:
            """
            テキストから埋め込みベクトルを生成する（フォールバック実装）
            
            sentence-transformersが利用できない場合のダミー実装
            """
            import hashlib
            import struct
            
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            
            embedding = []
            for i in range(0, min(len(hash_bytes), 256 * 4), 4):
                if i + 4 <= len(hash_bytes):
                    value = struct.unpack('I', hash_bytes[i:i+4])[0]
                    normalized = (value / (2**32 - 1)) * 2 - 1
                    embedding.append(normalized)
            
            while len(embedding) < 256:
                embedding.append(0.0)
            
            return embedding[:256]
        
        generate_embedding.dimension = 256
        
        return generate_embedding


def create_vss_interpreter(config: Any, service_funcs: Dict[str, Callable]) -> VSSAlgebra:
    """
    VSSインタープリターをクロージャとして作成
    
    Args:
        config: アプリケーション設定
        service_funcs: サービス関数の辞書
        
    Returns:
        VSSAlgebra protocol を実装するオブジェクト（クロージャ）
    """
    # クロージャが参照する設定とサービス関数
    _config = config
    _service_funcs = service_funcs
    
    class VSSInterpreterClosure:
        """VSS代数のインタープリター実装（クロージャベース）"""
        
        def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
            """ドキュメントをインデックス"""
            return _service_funcs["index_documents"](documents, _config)
        
        def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
            """類似ドキュメントを検索"""
            search_input = {"query": query, "limit": limit}
            search_input.update(kwargs)
            return _service_funcs["search"](search_input, _config)
    
    return VSSInterpreterClosure()



def create_vss(
    db_path: str = "./kuzu_db",
    in_memory: bool = False,
    model_name: str = "cl-nagoya/ruri-v3-30m",
    existing_connection: Optional[Any] = None,
    **kwargs
) -> Optional[VSSAlgebra]:
    """
    VSS統一APIインスタンスを作成
    
    Args:
        db_path: データベースパス
        in_memory: インメモリデータベースを使用するか
        model_name: 使用する埋め込みモデル名
        existing_connection: 既存のKuzuDB接続（オプション）
        **kwargs: その他の設定パラメータ
            - embedding_dimension: 埋め込み次元数
            - default_limit: デフォルトの検索結果数
            - index_mu: HNSWインデックスのmuパラメータ
            - index_ml: HNSWインデックスのmlパラメータ
            - index_metric: 距離メトリック ('cosine', 'l2')
            - index_efc: HNSWインデックスのefCパラメータ
    
    Returns:
        VSSAlgebra protocol実装 (成功時) または None (失敗時)
    
    Example:
        vss = create_vss(in_memory=True)
        if isinstance(vss, dict) and vss.get('type'):
            print(f"Failed to initialize VSS: {vss.get('message')}")
            return
        vss.index([{"id": "1", "content": "テキスト"}])
        results = vss.search("検索語")
    """
    # VSS initialization start
    log("info", {
        "message": "Starting VSS initialization",
        "component": "vss.application",
        "operation": "create_vss",
        "db_path": db_path,
        "in_memory": in_memory,
        "model_name": model_name,
        "has_existing_connection": existing_connection is not None
    })
    
    # 埋め込みサービスを作成
    embedding_func = create_embedding_service(model_name)
    embedding_dimension = kwargs.get(
        'embedding_dimension', 
        getattr(embedding_func, 'dimension', 256)
    )
    
    # ApplicationConfigを作成
    config: ApplicationConfig = {
        'db_path': db_path,
        'in_memory': in_memory,
        'embedding_dimension': embedding_dimension,
        'default_limit': kwargs.get('default_limit', 10),
        'index_mu': kwargs.get('index_mu', 30),
        'index_ml': kwargs.get('index_ml', 60),
        'index_metric': kwargs.get('index_metric', 'cosine'),
        'index_efc': kwargs.get('index_efc', 200),
        'existing_connection': existing_connection  # 既存接続を設定に追加
    }
    
    # Log configuration parameters (non-sensitive)
    log("info", {
        "message": "VSS configuration parameters",
        "component": "vss.application",
        "operation": "create_vss",
        "embedding_dimension": config['embedding_dimension'],
        "default_limit": config['default_limit'],
        "index_mu": config['index_mu'],
        "index_ml": config['index_ml'],
        "index_metric": config['index_metric'],
        "index_efc": config['index_efc']
    })
    
    # インフラストラクチャ関数をインポート
    from .infrastructure import (
        create_kuzu_database,
        create_kuzu_connection,
        check_vector_extension,
        initialize_vector_schema,
        insert_documents_with_embeddings,
        search_similar_vectors,
        count_documents,
        close_connection,
        DatabaseConfig
    )
    
    from .domain import find_semantically_similar_documents
    
    # サービス関数を作成
    service_funcs = create_vss_service(
        create_db_func=create_kuzu_database,
        create_conn_func=create_kuzu_connection,
        check_vector_func=check_vector_extension,
        init_schema_func=initialize_vector_schema,
        insert_docs_func=insert_documents_with_embeddings,
        search_func=search_similar_vectors,
        count_func=count_documents,
        close_func=close_connection,
        generate_embedding_func=embedding_func,
        calculate_similarity_func=find_semantically_similar_documents
    )
    
    # 初期化テスト（データベース接続とVECTOR拡張の確認）
    if existing_connection:
        # 既存の接続を使用
        connection = existing_connection
        should_close_connection = False
    else:
        # 新しい接続を作成
        db_config = {
            'db_path': config['db_path'],
            'in_memory': config['in_memory'],
            'embedding_dimension': config['embedding_dimension']
        }
        
        db_success, database, db_error = create_kuzu_database(db_config)
        if not db_success:
            error_msg = db_error.get('error', 'Unknown error')
            log("error", {
                "message": "Failed to create database during VSS initialization",
                "component": "vss.application",
                "operation": "create_vss",
                "error": error_msg,
                "details": db_error.get('details', {})
            })
            return {
                "type": "database_creation_error",
                "message": error_msg,
                "details": db_error.get('details', {})
            }
        
        conn_success, connection, conn_error = create_kuzu_connection(database)
        if not conn_success:
            error_msg = conn_error.get('error', 'Unknown error')
            log("error", {
                "message": "Failed to create connection during VSS initialization",
                "component": "vss.application",
                "operation": "create_vss",
                "error": error_msg,
                "details": conn_error.get('details', {})
            })
            return {
                "type": "connection_error",
                "message": error_msg,
                "details": conn_error.get('details', {})
            }
        
        should_close_connection = True
    
    try:
        vector_available, vector_error = check_vector_extension(connection)
        if not vector_available:
            # VECTOR拡張が利用できない場合は即座に失敗
            error_msg = vector_error.get('error', 'VECTOR extension not available')
            details = vector_error.get('details', {})
            log("error", {
                "message": "VECTOR extension not available",
                "component": "vss.application",
                "operation": "create_vss",
                "error": error_msg,
                "details": details
            })
            return {
                "type": "vector_extension_error",
                "message": error_msg,
                "details": details
            }
        
        # スキーマを初期化
        schema_success, schema_error = initialize_vector_schema(
            connection,
            config['embedding_dimension'],
            config['index_mu'],
            config['index_ml'],
            config['index_metric'],
            config['index_efc']
        )
        if not schema_success:
            error_msg = schema_error.get('error', 'Failed to initialize schema')
            details = schema_error.get('details', {})
            log("error", {
                "message": "Failed to initialize VSS schema",
                "component": "vss.application",
                "operation": "create_vss",
                "error": error_msg,
                "details": details
            })
            return {
                "type": "schema_initialization_error",
                "message": error_msg,
                "details": details
            }
    finally:
        # 自分で作成した接続のみクローズ
        if should_close_connection:
            close_connection(connection)
    
    # Log successful initialization
    log("info", {
        "message": "VSS initialization completed successfully",
        "component": "vss.application",
        "operation": "create_vss",
        "db_path": config['db_path'],
        "in_memory": config['in_memory'],
        "embedding_dimension": config['embedding_dimension']
    })
    
    return create_vss_interpreter(config, service_funcs)


def create_vss_optional(
    db_path: str = "./kuzu_db",
    in_memory: bool = False,
    model_name: str = "cl-nagoya/ruri-v3-30m",
    existing_connection: Optional[Any] = None,
    **kwargs
) -> Optional[VSSAlgebra]:
    """
    VSS統一APIインスタンスを作成 (Optional版 - 後方互換性のため)
    
    Args:
        db_path: データベースパス
        in_memory: インメモリデータベースを使用するか
        model_name: 使用する埋め込みモデル名
        existing_connection: 既存のKuzuDB接続（オプション）
        **kwargs: その他の設定パラメータ
    
    Returns:
        VSSAlgebra protocol実装 (成功時) または None (失敗時)
    
    Example:
        vss = create_vss_optional(in_memory=True)
        if vss is None:
            print("Failed to initialize VSS")
            return
        vss.index([{"id": "1", "content": "テキスト"}])
        results = vss.search("検索語")
    """
    # Deprecation warning
    log("warning", {
        "message": "create_vss_optional is deprecated and will be removed in a future version",
        "component": "vss_kuzu",
        "operation": "create_vss_optional",
        "deprecation": True,
        "recommendation": "Use create_vss directly and check for VSSError dict"
    })
    
    result = create_vss(db_path, in_memory, model_name, existing_connection, **kwargs)
    
    # VSSErrorの場合はNoneを返す（後方互換性のため）
    if isinstance(result, dict) and result.get('type'):
        return None
    
    return result
