"""
Meta Node POC - Cypherクエリをノードに格納して動的実行するテスト

このテストは、グラフノード自体にクエリロジックを持たせ、
メタプログラミング的なアプローチでグラフ操作を実現する仕様を定義します。
"""

import pytest
from pathlib import Path
import tempfile
import os
import kuzu

from meta_node import MetaNode, QueryNode, QueryExecutor


class TestMetaNodeBasics:
    """メタノードの基本的な振る舞いを検証"""
    
    def test_メタノードを作成できる(self):
        """メタノードインスタンスが作成できることを確認"""
        # Given: 一時的なデータベースファイル
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = kuzu.Database(db_path)
            
            # When: メタノードを作成
            meta_node = MetaNode(db)
            
            # Then: インスタンスが正しく作成される
            assert meta_node is not None
            assert meta_node.db == db


class TestQueryNode:
    """クエリノードの振る舞いを検証"""
    
    def test_クエリノードを作成して保存できる(self):
        """Cypherクエリをプロパティとして持つノードを作成できる"""
        # Given: メタノードシステム
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = kuzu.Database(db_path)
            meta_node = MetaNode(db)
            
            # When: クエリノードを作成
            query_node = QueryNode(
                name="find_all_persons",
                description="すべてのPersonノードを検索",
                cypher_query="MATCH (p:Person) RETURN p"
            )
            node_id = meta_node.create_query_node(query_node)
            
            # Then: ノードが作成され、IDが返される
            assert node_id is not None
            
    def test_クエリノードを名前で取得できる(self):
        """保存したクエリノードを名前で取得できる"""
        # Given: 保存されたクエリノード
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = kuzu.Database(db_path)
            meta_node = MetaNode(db)
            query_node = QueryNode(
                name="find_by_age",
                description="年齢でPersonを検索",
                cypher_query="MATCH (p:Person) WHERE p.age > $age RETURN p"
            )
            meta_node.create_query_node(query_node)
            
            # When: 名前でクエリノードを取得
            retrieved = meta_node.get_query_node("find_by_age")
            
            # Then: 正しいクエリノードが取得される
            assert retrieved is not None
            assert retrieved.name == "find_by_age"
            assert retrieved.cypher_query == "MATCH (p:Person) WHERE p.age > $age RETURN p"


class TestQueryExecutor:
    """動的クエリ実行エンジンの振る舞いを検証"""
    
    def test_クエリノードからクエリを実行できる(self):
        """保存されたクエリを動的に実行できる"""
        # Given: テストデータとクエリノード
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = kuzu.Database(db_path)
            meta_node = MetaNode(db)
            
            # テストデータを準備
            conn = kuzu.Connection(db)
            conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))")
            conn.execute("CREATE (:Person {name: 'Alice', age: 30})")
            conn.execute("CREATE (:Person {name: 'Bob', age: 25})")
            
            # クエリノードを作成
            query_node = QueryNode(
                name="find_adults",
                description="成人を検索",
                cypher_query="MATCH (p:Person) WHERE p.age >= 20 RETURN p.name as name, p.age as age ORDER BY p.name"
            )
            meta_node.create_query_node(query_node)
            
            # When: クエリエグゼキュータで実行
            executor = QueryExecutor(meta_node)
            results = executor.execute_query("find_adults")
            
            # Then: 正しい結果が返される
            assert len(results) == 2
            assert results[0]["name"] == "Alice"
            assert results[0]["age"] == 30
            assert results[1]["name"] == "Bob"
            assert results[1]["age"] == 25
    
    def test_パラメータ付きクエリを実行できる(self):
        """パラメータをバインドしてクエリを実行できる"""
        # Given: パラメータ付きクエリノード
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = kuzu.Database(db_path)
            meta_node = MetaNode(db)
            
            # テストデータを準備
            conn = kuzu.Connection(db)
            conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))")
            conn.execute("CREATE (:Person {name: 'Alice', age: 30})")
            conn.execute("CREATE (:Person {name: 'Bob', age: 25})")
            conn.execute("CREATE (:Person {name: 'Charlie', age: 20})")
            
            # パラメータ付きクエリノードを作成
            query_node = QueryNode(
                name="find_by_min_age",
                description="指定年齢以上の人を検索",
                cypher_query="MATCH (p:Person) WHERE p.age >= $min_age RETURN p.name as name ORDER BY p.name"
            )
            meta_node.create_query_node(query_node)
            
            # When: パラメータを指定して実行
            executor = QueryExecutor(meta_node)
            results = executor.execute_query("find_by_min_age", parameters={"min_age": 25})
            
            # Then: フィルタされた結果が返される
            assert len(results) == 2
            assert results[0]["name"] == "Alice"
            assert results[1]["name"] == "Bob"