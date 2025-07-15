#!/usr/bin/env python3
"""Ruri v3 + KuzuDB Vector Search POC"""

from dataclasses import dataclass
from typing import List
import kuzu
import os
import shutil

from .infrastructure import create_embedding_model
from .application import TextEmbeddingService
from .domain import EmbeddingType


@dataclass
class Document:
    """ドキュメントデータ"""
    id: int
    content: str
    embedding: List[float]


class KuzuVectorDB:
    """KuzuDBを使用したベクトル検索"""
    
    def __init__(self, db_path: str = "./kuzu_db", dimension: int = 256):
        self.db_path = db_path
        self.dimension = dimension
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._install_vector_extension()
        self._setup_schema()
    
    def _install_vector_extension(self):
        """VECTOR拡張機能をインストール"""
        try:
            self.conn.execute("LOAD EXTENSION VECTOR;")
        except:
            # 拡張機能がない場合はインストール
            self.conn.execute("INSTALL VECTOR;")
            self.conn.execute("LOAD EXTENSION VECTOR;")
    
    def _setup_schema(self):
        """データベーススキーマの初期化"""
        self.conn.execute(f"""
            CREATE NODE TABLE Document (
                id INT64,
                content STRING,
                embedding FLOAT[{self.dimension}],
                PRIMARY KEY (id)
            )
        """)
    
    def insert_documents(self, documents: List[Document]):
        """ドキュメントをデータベースに挿入"""
        for doc in documents:
            self.conn.execute("""
                CREATE (d:Document {
                    id: $id,
                    content: $content,
                    embedding: $embedding
                })
            """, {
                "id": doc.id,
                "content": doc.content,
                "embedding": doc.embedding
            })
    
    def create_vector_index(self):
        """ベクトルインデックスを作成"""
        self.conn.execute("""
            CALL CREATE_VECTOR_INDEX(
                'Document',
                'doc_embedding_index',
                'embedding'
            )
        """)
    
    def search_similar(self, query_embedding: List[float], k: int = 5) -> List[tuple[str, float]]:
        """類似ドキュメントを検索"""
        result = self.conn.execute("""
            CALL QUERY_VECTOR_INDEX(
                'Document',
                'doc_embedding_index',
                $embedding,
                $k
            ) RETURN node, distance
        """, {"embedding": query_embedding, "k": k})
        
        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]
            distance = row[1]
            results.append((node["content"], distance))
        return results


def main():
    """メイン処理"""
    print("=== Ruri v3 + KuzuDB Vector Search POC ===\n")
    
    # サンプルドキュメント
    sample_docs = [
        "瑠璃色（るりいろ）は、紫みを帯びた濃い青。名は、半貴石の瑠璃（ラピスラズリ）による。",
        "川べりでサーフボードを持った人たちがいます",
        "機械学習モデルを使用してテキストをベクトルに変換できます。",
        "サーファーたちが川べりに立っています",
        "今日は良い天気で、散歩に最適な日です。",
        "プログラミングは創造的で楽しい活動です。",
    ]
    
    print("1. 埋め込みモデルの初期化中...")
    print("   使用モデル: cl-nagoya/ruri-v3-30m (30M parameters)")
    
    # モデルとサービスの初期化
    model = create_embedding_model("ruri-v3-30m")
    embedding_service = TextEmbeddingService(model)
    
    print(f"   埋め込み次元: {model.dimension}")
    
    print("\n2. ドキュメントの埋め込みベクトル生成中...")
    doc_results = embedding_service.embed_documents(sample_docs)
    
    documents = [
        Document(
            id=i+1, 
            content=doc, 
            embedding=result.embeddings
        )
        for i, (doc, result) in enumerate(zip(sample_docs, doc_results))
    ]
    
    print("3. KuzuDBの初期化とデータ挿入中...")
    vector_db = KuzuVectorDB(dimension=model.dimension)
    vector_db.insert_documents(documents)
    
    print("4. ベクトルインデックスの作成中...")
    vector_db.create_vector_index()
    
    print("\n=== 検索テスト ===")
    queries = [
        "瑠璃色はどんな色？",
        "海でサーフィンをする人",
    ]
    
    for query in queries:
        print(f"\nクエリ: '{query}'")
        
        # 類似度検索（埋め込みサービスを使用）
        results = embedding_service.search_similar_documents(
            query, 
            sample_docs, 
            top_k=3
        )
        
        print("検索結果（埋め込みサービス経由）:")
        for i, (idx, content, similarity) in enumerate(results, 1):
            print(f"{i}. 類似度: {similarity:.4f}")
            print(f"   内容: {content}\n")
        
        # KuzuDB経由の検索
        print("KuzuDB経由の検索:")
        query_result = embedding_service.embed_query(query)
        kuzu_results = vector_db.search_similar(query_result.embeddings, k=3)
        
        for i, (content, distance) in enumerate(kuzu_results, 1):
            print(f"{i}. 距離: {distance:.4f}")
            print(f"   内容: {content}\n")


if __name__ == "__main__":
    main()