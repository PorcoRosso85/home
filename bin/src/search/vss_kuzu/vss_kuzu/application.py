#!/usr/bin/env python3
"""
アプリケーション層 - 高階関数による依存性注入

ユースケースの実装と、ドメイン層・インフラ層の結合
高階関数を使用して、柔軟な依存性注入を実現
"""

import time
from typing import Dict, Any, List, Optional, Callable, Tuple, TypedDict

# Type aliases for clarity
EmbeddingFunction = Callable[[str], List[float]]
DatabaseFunction = Callable[..., Any]
IndexFunction = Callable[[List[Dict[str, str]]], Dict[str, Any]]
SearchFunction = Callable[[str, int], Dict[str, Any]]


class VSSServiceInterface(TypedDict):
    """VSS統一APIインターフェース"""
    index: IndexFunction
    search: SearchFunction


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
        
        # 入力検証
        if not documents:
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
        else:
            # It's a dict
            db_path = config.get('db_path', './kuzu_db')
            in_memory = config.get('in_memory', False)
            embedding_dimension = config.get('embedding_dimension', 256)
            
        db_config = {
            'db_path': db_path,
            'in_memory': in_memory,
            'embedding_dimension': embedding_dimension
        }
        
        db_success, database, db_error = create_db_func(db_config)
        if not db_success:
            return {
                "ok": False,
                "error": db_error["error"],
                "details": db_error["details"]
            }
        
        conn_success, connection, conn_error = create_conn_func(database)
        if not conn_success:
            return {
                "ok": False,
                "error": conn_error["error"],
                "details": conn_error["details"]
            }
        
        try:
            # VECTOR拡張をチェック
            vector_available, vector_error = check_vector_func(connection)
            if not vector_available:
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
                return {
                    "ok": False,
                    "error": insert_error["error"],
                    "details": insert_error["details"]
                }
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return {
                "ok": True,
                "status": "success",
                "indexed_count": inserted_count,
                "index_time_ms": elapsed_ms
            }
            
        finally:
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
        
        # データベース接続を作成
        # DatabaseConfig is now a TypedDict, no need to import
        
        # Handle both dict and VSSConfig objects
        if hasattr(config, '__dict__'):
            # It's a dataclass/object, convert to dict-like access
            db_path = getattr(config, 'db_path', './kuzu_db')
            in_memory = getattr(config, 'in_memory', False)
            embedding_dimension = getattr(config, 'embedding_dimension', 256)
        else:
            # It's a dict
            db_path = config.get('db_path', './kuzu_db')
            in_memory = config.get('in_memory', False)
            embedding_dimension = config.get('embedding_dimension', 256)
            
        db_config = {
            'db_path': db_path,
            'in_memory': in_memory,
            'embedding_dimension': embedding_dimension
        }
        
        db_success, database, db_error = create_db_func(db_config)
        if not db_success:
            return {
                "ok": False,
                "error": db_error["error"],
                "details": db_error["details"]
            }
        
        conn_success, connection, conn_error = create_conn_func(database)
        if not conn_success:
            return {
                "ok": False,
                "error": conn_error["error"],
                "details": conn_error["details"]
            }
        
        try:
            # VECTOR拡張をチェック
            vector_available, vector_error = check_vector_func(connection)
            if not vector_available:
                return {
                    "ok": False,
                    "error": vector_error["error"],
                    "details": vector_error["details"]
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
                        "search_time_ms": (time.time() - start_time) * 1000
                    }
                }
            
            # クエリベクトルを取得または生成
            if "query_vector" in search_input:
                query_vector = search_input["query_vector"]
            else:
                query_vector = generate_embedding_func(query)
            
            # 検索を実行（efsパラメータを含む）
            search_success, db_results, search_error = search_func(
                connection, query_vector, limit, efs
            )
            
            if not search_success:
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
            
            elapsed_ms = (time.time() - start_time) * 1000
            
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


def create_vss_instance(config: Any, service_funcs: Dict[str, Callable]) -> VSSServiceInterface:
    """
    VSS統一APIインターフェースを作成
    
    Args:
        config: アプリケーション設定
        service_funcs: サービス関数の辞書
        
    Returns:
        VSSServiceInterface準拠の辞書
    """
    
    def index(documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        ドキュメントをインデックス
        
        Args:
            documents: {"id": str, "content": str}のリスト
            
        Returns:
            インデックス結果
        """
        return service_funcs["index_documents"](documents, config)
    
    def search(query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        類似ドキュメントを検索
        
        Args:
            query: 検索クエリ
            limit: 返す結果の最大数
            **kwargs: その他のオプション（query_vector, efsなど）
            
        Returns:
            検索結果
        """
        search_input = {"query": query, "limit": limit}
        search_input.update(kwargs)
        return service_funcs["search"](search_input, config)
    
    # TypedDictインターフェースに準拠した辞書を返す
    vss_service: VSSServiceInterface = {
        "index": index,
        "search": search
    }
    return vss_service


def create_vss(
    db_path: str = "./kuzu_db",
    in_memory: bool = False,
    model_name: str = "cl-nagoya/ruri-v3-30m",
    **kwargs
) -> VSSServiceInterface:
    """
    VSS統一APIインスタンスを作成
    
    Args:
        db_path: データベースパス
        in_memory: インメモリデータベースを使用するか
        model_name: 使用する埋め込みモデル名
        **kwargs: その他の設定パラメータ
            - embedding_dimension: 埋め込み次元数
            - default_limit: デフォルトの検索結果数
            - index_mu: HNSWインデックスのmuパラメータ
            - index_ml: HNSWインデックスのmlパラメータ
            - index_metric: 距離メトリック ('cosine', 'l2')
            - index_efc: HNSWインデックスのefCパラメータ
    
    Returns:
        VSSServiceInterface準拠の辞書
    
    Example:
        vss = create_vss(in_memory=True)
        vss["index"]([{"id": "1", "content": "テキスト"}])
        results = vss["search"]("検索語")
    """
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
        'index_efc': kwargs.get('index_efc', 200)
    }
    
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
    db_config = {
        'db_path': config['db_path'],
        'in_memory': config['in_memory'],
        'embedding_dimension': config['embedding_dimension']
    }
    
    db_success, database, db_error = create_kuzu_database(db_config)
    if not db_success:
        raise RuntimeError(f"Failed to create database: {db_error.get('error', 'Unknown error')}")
    
    conn_success, connection, conn_error = create_kuzu_connection(database)
    if not conn_success:
        raise RuntimeError(f"Failed to create connection: {conn_error.get('error', 'Unknown error')}")
    
    try:
        vector_available, vector_error = check_vector_extension(connection)
        if not vector_available:
            # VECTOR拡張が利用できない場合は即座に失敗
            error_msg = vector_error.get('error', 'VECTOR extension not available')
            details = vector_error.get('details', {})
            raise RuntimeError(
                f"Failed to initialize VSS: {error_msg}. "
                f"Details: {details}"
            )
        
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
            raise RuntimeError(
                f"Failed to initialize VSS schema: {error_msg}. "
                f"Details: {details}"
            )
    finally:
        close_connection(connection)
    
    return create_vss_instance(config, service_funcs)


# SimpleNamespaceについて
# ====================
#
# SimpleNamespaceは、Pythonの標準ライブラリ(types)に含まれるクラスで、
# 属性へのドットアクセスを提供するシンプルなオブジェクトです。
#
# 特徴:
# 1. 辞書のような柔軟性を持ちながら、obj.attributeの形式でアクセス可能
# 2. 動的に属性を追加・変更可能
# 3. クラス定義なしで構造化されたデータを表現できる
#
# 使用例:
#   vss = create_vss()  # SimpleNamespaceを返す
#   vss.index(documents)  # メソッドのようにアクセス
#   vss.search(query)     # 同様にドット記法でアクセス
#
# なぜSimpleNamespaceを使うのか:
# - 統一APIのインターフェースとして、クラスを定義せずに
#   複数の関数をグループ化できる
# - ユーザーにとって直感的なドット記法でのアクセスを提供
# - 内部実装の詳細を隠蔽しながら、シンプルなAPIを提供
# - 将来的に機能を追加する際も、後方互換性を保ちやすい