#!/usr/bin/env python3
"""PLaMo-Embedding-1B + KuzuDB Vector Search POC"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from transformers import AutoModel, AutoTokenizer
import kuzu
import os
import shutil


@dataclass
class Document:
    """ドキュメントデータ"""
    id: int
    content: str
    embedding: List[float]


class PlamoEmbedder:
    """PLaMo-Embedding-1Bを使用したテキスト埋め込み生成"""
    
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            "pfnet/plamo-embedding-1b", 
            trust_remote_code=True
        )
        self.model = AutoModel.from_pretrained(
            "pfnet/plamo-embedding-1b", 
            trust_remote_code=True
        )
    
    def encode_query(self, query: str) -> List[float]:
        """クエリテキストを埋め込みベクトルに変換"""
        embedding = self.model.encode_query(query, self.tokenizer)
        return embedding.tolist()
    
    def encode_documents(self, documents: List[str]) -> List[List[float]]:
        """ドキュメントリストを埋め込みベクトルに変換"""
        embeddings = self.model.encode_document(documents, self.tokenizer)
        return embeddings.tolist()


class KuzuVectorDB:
    """KuzuDBを使用したベクトル検索"""
    
    def __init__(self, db_path: str = "./kuzu_db"):
        self.db_path = db_path
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._setup_schema()
    
    def _setup_schema(self):
        """データベーススキーマの初期化"""
        self.conn.execute("""
            CREATE NODE TABLE Document (
                id INT64,
                content STRING,
                embedding FLOAT[1536],
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
    
    def search_similar(self, query_embedding: List[float], k: int = 5) -> List[Tuple[str, float]]:
        """類似ドキュメントを検索"""
        result = self.conn.execute("""
            CALL QUERY_VECTOR_INDEX(
                'Document',
                'doc_embedding_index',
                $1,
                $2
            ) RETURN node, distance
        """, [query_embedding, k])
        
        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]
            distance = row[1]
            results.append((node["content"], distance))
        return results


def main():
    """メイン処理"""
    print("=== PLaMo-Embedding-1B + KuzuDB Vector Search POC ===\n")
    
    # サンプルドキュメント
    sample_docs = [
        "PLaMo-Embedding-1Bは日本語に特化した埋め込みモデルです。",
        "KuzuDBはグラフデータベースでベクター検索機能も提供しています。",
        "機械学習モデルを使用してテキストをベクトルに変換できます。",
        "今日は良い天気で、散歩に最適な日です。",
        "プログラミングは創造的で楽しい活動です。",
    ]
    
    print("1. PLaMo-Embedding-1Bの初期化中...")
    embedder = PlamoEmbedder()
    
    print("2. ドキュメントの埋め込みベクトル生成中...")
    embeddings = embedder.encode_documents(sample_docs)
    
    documents = [
        Document(id=i+1, content=doc, embedding=emb)
        for i, (doc, emb) in enumerate(zip(sample_docs, embeddings))
    ]
    
    print("3. KuzuDBの初期化とデータ挿入中...")
    vector_db = KuzuVectorDB()
    vector_db.insert_documents(documents)
    
    print("4. ベクトルインデックスの作成中...")
    vector_db.create_vector_index()
    
    print("\n=== 検索テスト ===")
    query = "日本語の自然言語処理について"
    print(f"クエリ: '{query}'")
    
    print("5. クエリの埋め込みベクトル生成中...")
    query_embedding = embedder.encode_query(query)
    
    print("6. 類似ドキュメント検索中...\n")
    results = vector_db.search_similar(query_embedding, k=3)
    
    print("検索結果:")
    for i, (content, distance) in enumerate(results, 1):
        print(f"{i}. 距離: {distance:.4f}")
        print(f"   内容: {content}\n")


if __name__ == "__main__":
    main()