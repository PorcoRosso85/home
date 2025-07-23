#!/usr/bin/env python3
"""
アプリケーション層 - 高階関数による依存性注入

ユースケースの実装と、ドメイン層・インフラ層の結合
高階関数を使用して、柔軟な依存性注入を実現
"""

import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass

# Type aliases for clarity
EmbeddingFunction = Callable[[str], List[float]]
DatabaseFunction = Callable[..., Any]


@dataclass(frozen=True)
class ApplicationConfig:
    """アプリケーション設定"""
    db_path: str = "./kuzu_db"
    in_memory: bool = False
    embedding_dimension: int = 256
    default_limit: int = 10
    index_mu: int = 30
    index_ml: int = 60
    index_metric: str = 'cosine'
    index_efc: int = 200


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
    
    def index_documents(documents: List[Dict[str, str]], config: ApplicationConfig) -> Dict[str, Any]:
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
        from .infrastructure import DatabaseConfig
        db_config = DatabaseConfig(
            db_path=config.db_path,
            in_memory=config.in_memory,
            embedding_dimension=config.embedding_dimension
        )
        
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
            schema_success, schema_error = init_schema_func(
                connection, 
                config.embedding_dimension,
                config.index_mu,
                config.index_ml,
                config.index_metric,
                config.index_efc
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
    
    def search(search_input: Dict[str, Any], config: ApplicationConfig) -> Dict[str, Any]:
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
        
        limit = search_input.get("limit", config.default_limit)
        efs = search_input.get("efs", 200)  # Default efs value
        
        # データベース接続を作成
        from .infrastructure import DatabaseConfig
        db_config = DatabaseConfig(
            db_path=config.db_path,
            in_memory=config.in_memory,
            embedding_dimension=config.embedding_dimension
        )
        
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


class VSSService:
    """
    VSSサービスクラス - アプリケーション層のファサード
    
    高階関数を使用して作成されたサービスを
    オブジェクト指向インターフェースでラップ
    """
    
    def __init__(self, db_path: str = "./kuzu_db", in_memory: bool = False, model_name: str = "cl-nagoya/ruri-v3-30m"):
        """
        VSSサービスを初期化
        
        Args:
            db_path: データベースパス
            in_memory: インメモリデータベースを使用するか
            model_name: 使用する埋め込みモデル名
        """
        embedding_func = create_embedding_service(model_name)
        embedding_dimension = getattr(embedding_func, 'dimension', 256)
        
        self.config = ApplicationConfig(
            db_path=db_path,
            in_memory=in_memory,
            embedding_dimension=embedding_dimension
        )
        
        self._init_error: Optional[Dict[str, Any]] = None
        self._is_initialized = False
        
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
            calculate_similarity_func=find_semantically_similar_documents
        )
        
        self._test_initialization(
            create_kuzu_database,
            create_kuzu_connection,
            check_vector_extension,
            initialize_vector_schema,
            close_connection,
            DatabaseConfig
        )
    
    def _test_initialization(
        self,
        create_db_func,
        create_conn_func,
        check_vector_func,
        init_schema_func,
        close_func,
        DatabaseConfig
    ):
        """初期化時にデータベース接続とスキーマを確認"""
        db_config = DatabaseConfig(
            db_path=self.config.db_path,
            in_memory=self.config.in_memory,
            embedding_dimension=self.config.embedding_dimension
        )
        
        db_success, database, db_error = create_db_func(db_config)
        if not db_success:
            self._init_error = {
                "ok": False,
                "error": db_error.get("error", "Database creation failed"),
                "details": db_error.get("details", {})
            }
            return
        
        conn_success, connection, conn_error = create_conn_func(database)
        if not conn_success:
            self._init_error = {
                "ok": False,
                "error": conn_error.get("error", "Connection creation failed"),
                "details": conn_error.get("details", {})
            }
            return
        
        try:
            vector_available, vector_error = check_vector_func(connection)
            if not vector_available:
                error_msg = f"CRITICAL: {vector_error.get('error', 'VECTOR extension not available')}"
                self._init_error = {
                    "ok": False,
                    "error": error_msg,
                    "details": vector_error.get("details", {})
                }
                raise RuntimeError(error_msg)
            
            # スキーマを初期化（HNSWパラメータを含む）
            schema_success, schema_error = init_schema_func(
                connection, 
                self.config.embedding_dimension,
                self.config.index_mu,
                self.config.index_ml,
                self.config.index_metric,
                self.config.index_efc
            )
            if not schema_success:
                self._init_error = {
                    "ok": False,
                    "error": schema_error.get("error", "Schema initialization failed"),
                    "details": schema_error.get("details", {})
                }
                return
            
            self._is_initialized = True
            
        finally:
            close_func(connection)
    
    def _check_initialized(self) -> Optional[Dict[str, Any]]:
        """初期化状態を確認し、エラーがあれば返す"""
        if self._init_error:
            return self._init_error
        if not self._is_initialized:
            return {
                "ok": False,
                "error": "Service not properly initialized",
                "details": {
                    "reason": "Initialization was not completed",
                    "db_path": self.config.db_path
                }
            }
        return None
    
    def index_documents(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """ドキュメントをインデックス"""
        init_error = self._check_initialized()
        if init_error:
            return init_error
        
        return self._service_funcs["index_documents"](documents, self.config)
    
    def search(self, search_input: Dict[str, Any]) -> Dict[str, Any]:
        """類似ドキュメントを検索"""
        init_error = self._check_initialized()
        if init_error:
            return init_error
        
        return self._service_funcs["search"](search_input, self.config)
    
    # Legacy API compatibility methods
    def add_document(self, document_id: str, content: str) -> Dict[str, Any]:
        """
        旧API互換メソッド: 単一ドキュメントを追加
        
        Args:
            document_id: ドキュメントID
            content: ドキュメント内容
            
        Returns:
            インデックス結果
        """
        documents = [{"id": document_id, "content": content}]
        return self.index_documents(documents)
    
    def search_similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        旧API互換メソッド: 類似検索
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            
        Returns:
            検索結果のリスト
        """
        search_result = self.search({"query": query, "limit": k})
        
        # エラーの場合は空リストを返す
        if not search_result.get("ok", False):
            return []
        
        # 結果を旧フォーマットに変換
        results = []
        for result in search_result.get("results", []):
            results.append({
                "document_id": result.get("id", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0)
            })
        
        return results