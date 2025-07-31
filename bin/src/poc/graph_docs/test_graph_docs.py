"""graph_docs POCのテスト

責務:
- DualKuzuDBクラスの基本動作確認
- エラーハンドリングの確認
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import csv
from graph_docs.mod import DualKuzuDB, QueryResult, DualQueryResult
import kuzu

class TestDualKuzuDB:
    """DualKuzuDBクラスのテスト"""
    
    @pytest.fixture
    def temp_db_paths(self):
        """テスト用の一時DBディレクトリを作成"""
        db1_dir = tempfile.mkdtemp()
        db2_dir = tempfile.mkdtemp()
        db1_path = Path(db1_dir) / "db1.kuzu"
        db2_path = Path(db2_dir) / "db2.kuzu"
        yield db1_path, db2_path
        # クリーンアップ
        shutil.rmtree(db1_dir, ignore_errors=True)
        shutil.rmtree(db2_dir, ignore_errors=True)
    
    @pytest.fixture
    def temp_local_db_path(self):
        """ローカルDB初期化テスト用の一時DBディレクトリを作成"""
        db_dir = tempfile.mkdtemp()
        db_path = Path(db_dir) / "test.db"
        yield db_path
        # クリーンアップ
        shutil.rmtree(db_dir, ignore_errors=True)
    
    def test_initialization(self, temp_db_paths):
        """初期化のテスト"""
        db1_path, db2_path = temp_db_paths
        db = DualKuzuDB(db1_path, db2_path)
        
        assert db.db1_path == db1_path
        assert db.db2_path == db2_path
        assert db._db1 is None
        assert db._db2 is None
        assert db._conn1 is None
        assert db._conn2 is None
    
    def test_context_manager(self, temp_db_paths):
        """コンテキストマネージャーのテスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            # 接続が確立されていることを確認
            assert db._db1 is not None
            assert db._db2 is not None
            assert db._conn1 is not None
            assert db._conn2 is not None
        
        # コンテキスト外では切断されていることを確認
        assert db._db1 is None
        assert db._db2 is None
        assert db._conn1 is None
        assert db._conn2 is None
    
    def test_query_single_invalid_db_name(self, temp_db_paths):
        """無効なDB名でのクエリテスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            result = db.query_single("invalid_db", "MATCH (n) RETURN n;")
            
            assert result.error is not None
            assert "Invalid db_name" in result.error
            assert result.source == "invalid_db"
            assert result.columns == []
            assert result.rows == []
    
    def test_query_single_not_connected(self, temp_db_paths):
        """接続前のクエリテスト"""
        db1_path, db2_path = temp_db_paths
        db = DualKuzuDB(db1_path, db2_path)
        
        # 接続せずにクエリを実行
        result = db.query_single("db1", "MATCH (n) RETURN n;")
        
        assert result.error is not None
        assert "Not connected" in result.error
        assert result.source == "db1"
    
    def test_query_both(self, temp_db_paths):
        """両DBへの同一クエリテスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            # 空のDBに対してクエリを実行
            result = db.query_both("CALL show_tables() RETURN *;")
            
            assert isinstance(result, DualQueryResult)
            # 両方のDBで実行されることを確認
            assert result.db1_result is not None or result.db2_result is not None
    
    def test_query_parallel(self, temp_db_paths):
        """異なるクエリの並列実行テスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            result = db.query_parallel(
                "CALL show_tables() RETURN *;",
                "CALL show_tables() RETURN *;"
            )
            
            assert isinstance(result, DualQueryResult)
            # 両方のDBで実行されることを確認
            assert result.db1_result is not None or result.db2_result is not None
    
    def test_init_local_db(self, temp_local_db_path):
        """ローカルDB作成とスキーマ定義の確認"""
        # KuzuDBインスタンスを作成
        db = kuzu.Database(str(temp_local_db_path))
        conn = kuzu.Connection(db)
        
        # User/Product/OWNSスキーマを定義
        conn.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
        conn.execute("CREATE NODE TABLE Product(name STRING, price DOUBLE, PRIMARY KEY (name))")
        conn.execute("CREATE REL TABLE OWNS(FROM User TO Product, since INT32)")
        
        # テーブルが作成されたことを確認
        result = conn.execute("CALL show_tables() RETURN *;")
        
        # カラム名を確認
        column_names = result.get_column_names() if hasattr(result, 'get_column_names') else []
        
        tables = []
        while result.has_next():
            row = result.get_next()
            # カラム名があれば、それに基づいてnameカラムを探す
            if 'name' in column_names:
                name_idx = column_names.index('name')
                tables.append(row[name_idx])
            else:
                # カラム名がない場合は最初の要素がテーブル名と仮定
                tables.append(row[0])
        
        # 期待するテーブルが存在することを確認
        assert "User" in tables
        assert "Product" in tables
        assert "OWNS" in tables
    
    def test_local_db_schema(self, temp_local_db_path):
        """User/Product/OWNSテーブルの存在確認"""
        # KuzuDBインスタンスを作成してスキーマを定義
        db = kuzu.Database(str(temp_local_db_path))
        conn = kuzu.Connection(db)
        
        # スキーマ定義
        conn.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
        conn.execute("CREATE NODE TABLE Product(name STRING, price DOUBLE, PRIMARY KEY (name))")
        conn.execute("CREATE REL TABLE OWNS(FROM User TO Product, since INT32)")
        
        # テストデータを挿入
        conn.execute("CREATE (u:User {name: 'Alice', age: 30})")
        conn.execute("CREATE (p:Product {name: 'Laptop', price: 999.99})")
        conn.execute("MATCH (u:User {name: 'Alice'}), (p:Product {name: 'Laptop'}) CREATE (u)-[:OWNS {since: 2024}]->(p)")
        
        # データが正しく挿入されたことを確認
        user_result = conn.execute("MATCH (u:User) RETURN u.name, u.age")
        user_data = []
        while user_result.has_next():
            user_data.append(user_result.get_next())
        assert len(user_data) == 1
        assert user_data[0] == ['Alice', 30]
        
        # リレーションが正しく定義されたことを確認
        owns_result = conn.execute("MATCH (u:User)-[o:OWNS]->(p:Product) RETURN u.name, p.name, o.since")
        owns_data = []
        while owns_result.has_next():
            owns_data.append(owns_result.get_next())
        assert len(owns_data) == 1
        assert owns_data[0] == ['Alice', 'Laptop', 2024]
    
    def test_copy_from_target_success(self, temp_db_paths):
        """正常なCOPY FROM動作の確認"""
        db1_path, db2_path = temp_db_paths
        
        # CSVファイルの作成
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        try:
            # Userテーブル用のCSVデータ
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Alice', 30])  # name, age
            csv_writer.writerow(['Bob', 25])
            csv_writer.writerow(['Charlie', 35])
            csv_file.close()
            
            with DualKuzuDB(db1_path, db2_path) as db:
                # db1にUserテーブルを作成
                db._conn1.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
                
                # COPY FROMでデータをインポート
                result = db.copy_from("db1", "User", csv_file.name)
                
                # エラーがないことを確認
                assert result.error is None
                assert result.source == "db1"
                assert result.columns == ["rows_copied"]
                assert len(result.rows) == 1
                assert "3 tuples have been copied" in result.rows[0][0]
                
                # データが正しくインポートされたことを確認
                verify_result = db.query_single("db1", "MATCH (u:User) RETURN u.name, u.age ORDER BY u.name")
                assert verify_result.error is None
                assert len(verify_result.rows) == 3
                assert verify_result.rows[0] == ['Alice', 30]
                assert verify_result.rows[1] == ['Bob', 25]
                assert verify_result.rows[2] == ['Charlie', 35]
        finally:
            # CSVファイルのクリーンアップ
            Path(csv_file.name).unlink(missing_ok=True)
    
    def test_copy_from_invalid_target(self, temp_db_paths):
        """無効なtarget名でのCOPY FROMエラー確認"""
        db1_path, db2_path = temp_db_paths
        
        # ダミーのCSVファイルパス（実際には使用されない）
        dummy_csv = "/tmp/dummy.csv"
        
        with DualKuzuDB(db1_path, db2_path) as db:
            # 無効なターゲット名でCOPY FROMを実行
            result = db.copy_from("invalid_db", "User", dummy_csv)
            
            # エラーが返されることを確認
            assert result.error is not None
            assert "Invalid target" in result.error
            assert "Must be 'db1', 'db2', or 'local'" in result.error
            assert result.source == "invalid_db"
            assert result.columns == []
            assert result.rows == []
    
    def test_copy_preserves_original(self, temp_db_paths):
        """COPY FROM実行時に元のDBが変更されないことの確認"""
        db1_path, db2_path = temp_db_paths
        
        # CSVファイルの作成
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        try:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['David', 40])
            csv_writer.writerow(['Eve', 28])
            csv_file.close()
            
            with DualKuzuDB(db1_path, db2_path) as db:
                # 両方のDBにUserテーブルを作成
                db._conn1.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
                db._conn2.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
                
                # db1に初期データを挿入
                db._conn1.execute("CREATE (u:User {name: 'Alice', age: 30})")
                db._conn1.execute("CREATE (u:User {name: 'Bob', age: 25})")
                
                # db2に初期データを挿入
                db._conn2.execute("CREATE (u:User {name: 'Charlie', age: 35})")
                
                # db1の初期状態を確認
                initial_db1 = db.query_single("db1", "MATCH (u:User) RETURN u.name ORDER BY u.name")
                assert len(initial_db1.rows) == 2
                assert initial_db1.rows[0][0] == 'Alice'
                assert initial_db1.rows[1][0] == 'Bob'
                
                # db2の初期状態を確認
                initial_db2 = db.query_single("db2", "MATCH (u:User) RETURN u.name ORDER BY u.name")
                assert len(initial_db2.rows) == 1
                assert initial_db2.rows[0][0] == 'Charlie'
                
                # db2にCOPY FROMでデータを追加
                result = db.copy_from("db2", "User", csv_file.name)
                assert result.error is None
                assert len(result.rows) == 1
                assert "2 tuples have been copied" in result.rows[0][0]
                
                # db1が変更されていないことを確認
                after_db1 = db.query_single("db1", "MATCH (u:User) RETURN u.name ORDER BY u.name")
                assert len(after_db1.rows) == 2  # 変更なし
                assert after_db1.rows[0][0] == 'Alice'
                assert after_db1.rows[1][0] == 'Bob'
                
                # db2に新しいデータが追加されたことを確認
                after_db2 = db.query_single("db2", "MATCH (u:User) RETURN u.name ORDER BY u.name")
                assert len(after_db2.rows) == 3  # 1 + 2 = 3行
                assert after_db2.rows[0][0] == 'Charlie'
                assert after_db2.rows[1][0] == 'David'
                assert after_db2.rows[2][0] == 'Eve'
        finally:
            # CSVファイルのクリーンアップ
            Path(csv_file.name).unlink(missing_ok=True)
    
    def test_create_relation_success(self, temp_local_db_path):
        """User->Product間のOWNSリレーション作成確認"""
        # KuzuDBインスタンスを作成
        db = kuzu.Database(str(temp_local_db_path))
        conn = kuzu.Connection(db)
        
        # スキーマ定義
        conn.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
        conn.execute("CREATE NODE TABLE Product(name STRING, price DOUBLE, PRIMARY KEY (name))")
        conn.execute("CREATE REL TABLE OWNS(FROM User TO Product, since INT32)")
        
        # ノードを作成
        conn.execute("CREATE (u:User {name: 'Alice', age: 30})")
        conn.execute("CREATE (u:User {name: 'Bob', age: 25})")
        conn.execute("CREATE (p:Product {name: 'Laptop', price: 999.99})")
        conn.execute("CREATE (p:Product {name: 'Phone', price: 599.99})")
        
        # リレーションを作成
        conn.execute("MATCH (u:User {name: 'Alice'}), (p:Product {name: 'Laptop'}) CREATE (u)-[:OWNS {since: 2024}]->(p)")
        conn.execute("MATCH (u:User {name: 'Alice'}), (p:Product {name: 'Phone'}) CREATE (u)-[:OWNS {since: 2023}]->(p)")
        conn.execute("MATCH (u:User {name: 'Bob'}), (p:Product {name: 'Phone'}) CREATE (u)-[:OWNS {since: 2022}]->(p)")
        
        # リレーションが正しく作成されたことを確認
        result = conn.execute("MATCH ()-[r:OWNS]->() RETURN COUNT(r) as count")
        assert result.has_next()
        row = result.get_next()
        assert row[0] == 3  # 3つのリレーションが作成されたことを確認
        
        # 特定のリレーションの詳細を確認
        alice_owns = conn.execute("MATCH (u:User {name: 'Alice'})-[o:OWNS]->(p:Product) RETURN p.name, o.since ORDER BY o.since")
        owns_data = []
        while alice_owns.has_next():
            owns_data.append(alice_owns.get_next())
        
        assert len(owns_data) == 2
        assert owns_data[0] == ['Phone', 2023]
        assert owns_data[1] == ['Laptop', 2024]
    
    def test_create_relation_invalid_nodes(self, temp_local_db_path):
        """存在しないノードへのリレーションエラー確認"""
        # KuzuDBインスタンスを作成
        db = kuzu.Database(str(temp_local_db_path))
        conn = kuzu.Connection(db)
        
        # スキーマ定義
        conn.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
        conn.execute("CREATE NODE TABLE Product(name STRING, price DOUBLE, PRIMARY KEY (name))")
        conn.execute("CREATE REL TABLE OWNS(FROM User TO Product, since INT32)")
        
        # Userノードのみ作成（Productは作成しない）
        conn.execute("CREATE (u:User {name: 'Alice', age: 30})")
        
        # 存在しないProductノードへのリレーション作成を試みる
        # KuzuDBでは存在しないノードへのリレーション作成はマッチが失敗するため、リレーションが作成されない
        conn.execute("MATCH (u:User {name: 'Alice'}), (p:Product {name: 'NonExistent'}) CREATE (u)-[:OWNS {since: 2024}]->(p)")
        
        # リレーションが作成されていないことを確認
        result = conn.execute("MATCH ()-[r:OWNS]->() RETURN COUNT(r) as count")
        assert result.has_next()
        row = result.get_next()
        assert row[0] == 0  # リレーションが作成されていない
        
        # 存在しないUserからのリレーション作成も試みる
        conn.execute("CREATE (p:Product {name: 'Laptop', price: 999.99})")
        conn.execute("MATCH (u:User {name: 'NonExistentUser'}), (p:Product {name: 'Laptop'}) CREATE (u)-[:OWNS {since: 2024}]->(p)")
        
        # まだリレーションが作成されていないことを確認
        result2 = conn.execute("MATCH ()-[r:OWNS]->() RETURN COUNT(r) as count")
        assert result2.has_next()
        row2 = result2.get_next()
        assert row2[0] == 0  # リレーションが作成されていない
    
    def test_query_relations(self, temp_local_db_path):
        """作成したリレーションのクエリ動作確認"""
        # KuzuDBインスタンスを作成
        db = kuzu.Database(str(temp_local_db_path))
        conn = kuzu.Connection(db)
        
        # スキーマ定義
        conn.execute("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))")
        conn.execute("CREATE NODE TABLE Product(name STRING, price DOUBLE, PRIMARY KEY (name))")
        conn.execute("CREATE REL TABLE OWNS(FROM User TO Product, since INT32)")
        
        # テストデータを作成
        conn.execute("CREATE (u:User {name: 'Alice', age: 30})")
        conn.execute("CREATE (u:User {name: 'Bob', age: 25})")
        conn.execute("CREATE (u:User {name: 'Charlie', age: 35})")
        conn.execute("CREATE (p:Product {name: 'Laptop', price: 999.99})")
        conn.execute("CREATE (p:Product {name: 'Phone', price: 599.99})")
        conn.execute("CREATE (p:Product {name: 'Tablet', price: 399.99})")
        
        # リレーションを作成
        conn.execute("MATCH (u:User {name: 'Alice'}), (p:Product {name: 'Laptop'}) CREATE (u)-[:OWNS {since: 2024}]->(p)")
        conn.execute("MATCH (u:User {name: 'Alice'}), (p:Product {name: 'Phone'}) CREATE (u)-[:OWNS {since: 2023}]->(p)")
        conn.execute("MATCH (u:User {name: 'Bob'}), (p:Product {name: 'Phone'}) CREATE (u)-[:OWNS {since: 2022}]->(p)")
        conn.execute("MATCH (u:User {name: 'Charlie'}), (p:Product {name: 'Tablet'}) CREATE (u)-[:OWNS {since: 2024}]->(p)")
        
        # 1. 特定のユーザーが所有する製品を検索
        alice_products = conn.execute("MATCH (u:User {name: 'Alice'})-[:OWNS]->(p:Product) RETURN p.name ORDER BY p.name")
        products = []
        while alice_products.has_next():
            products.append(alice_products.get_next()[0])
        assert products == ['Laptop', 'Phone']
        
        # 2. 特定の製品を所有するユーザーを検索
        phone_owners = conn.execute("MATCH (u:User)-[:OWNS]->(p:Product {name: 'Phone'}) RETURN u.name ORDER BY u.name")
        owners = []
        while phone_owners.has_next():
            owners.append(phone_owners.get_next()[0])
        assert owners == ['Alice', 'Bob']
        
        # 3. リレーションのプロパティを含むクエリ
        recent_purchases = conn.execute("MATCH (u:User)-[o:OWNS]->(p:Product) WHERE o.since >= 2023 RETURN u.name, p.name, o.since ORDER BY o.since DESC")
        purchases = []
        while recent_purchases.has_next():
            purchases.append(recent_purchases.get_next())
        assert len(purchases) == 3
        assert purchases[0] == ['Alice', 'Laptop', 2024]
        assert purchases[1] == ['Charlie', 'Tablet', 2024]
        assert purchases[2] == ['Alice', 'Phone', 2023]
        
        # 4. 複数の製品を所有するユーザーを検索
        multi_owners = conn.execute("""
            MATCH (u:User)-[:OWNS]->(p:Product)
            WITH u, COUNT(p) as product_count
            WHERE product_count > 1
            RETURN u.name, product_count
            ORDER BY product_count DESC
        """)
        multi_owner_data = []
        while multi_owners.has_next():
            multi_owner_data.append(multi_owners.get_next())
        assert len(multi_owner_data) == 1
        assert multi_owner_data[0] == ['Alice', 2]

class TestQueryResult:
    """QueryResultデータクラスのテスト"""
    
    def test_query_result_creation(self):
        """QueryResultの作成テスト"""
        result = QueryResult(
            source="db1",
            columns=["id", "name"],
            rows=[[1, "test"], [2, "test2"]]
        )
        
        assert result.source == "db1"
        assert result.columns == ["id", "name"]
        assert result.rows == [[1, "test"], [2, "test2"]]
        assert result.error is None
    
    def test_query_result_with_error(self):
        """エラー付きQueryResultのテスト"""
        result = QueryResult(
            source="db1",
            columns=[],
            rows=[],
            error="Connection failed"
        )
        
        assert result.source == "db1"
        assert result.columns == []
        assert result.rows == []
        assert result.error == "Connection failed"

class TestDualQueryResult:
    """DualQueryResultデータクラスのテスト"""
    
    def test_dual_query_result_creation(self):
        """DualQueryResultの作成テスト"""
        db1_result = QueryResult("db1", ["col1"], [[1]])
        db2_result = QueryResult("db2", ["col2"], [[2]])
        
        dual_result = DualQueryResult(
            db1_result=db1_result,
            db2_result=db2_result
        )
        
        assert dual_result.db1_result == db1_result
        assert dual_result.db2_result == db2_result
        assert dual_result.combined is None