"""KuzuDB Advanced UDF Tests - TDD Red Phase
グラフデータベース特有のUDF機能のテスト（失敗するテスト）
"""

import kuzu
import pytest
from typing import List, Dict, Any


class TestPathAnalysisUDF:
    """パス分析UDFのテスト"""
    
    @pytest.fixture
    def db_conn(self):
        """テスト用のインメモリDB接続"""
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        yield conn
    
    def test_calculate_path_cost_udf(self, db_conn):
        """パスの総コストを計算するUDF"""
        # テストデータの準備
        db_conn.execute("CREATE NODE TABLE Location (id STRING, cost DOUBLE, PRIMARY KEY(id))")
        db_conn.execute("CREATE REL TABLE CONNECTS (FROM Location TO Location, distance DOUBLE)")
        
        # ノードの作成
        db_conn.execute("CREATE (:Location {id: 'A', cost: 10.0})")
        db_conn.execute("CREATE (:Location {id: 'B', cost: 20.0})")
        db_conn.execute("CREATE (:Location {id: 'C', cost: 15.0})")
        
        # エッジの作成
        db_conn.execute("""
            MATCH (a:Location {id: 'A'}), (b:Location {id: 'B'})
            CREATE (a)-[:CONNECTS {distance: 5.0}]->(b)
        """)
        db_conn.execute("""
            MATCH (b:Location {id: 'B'}), (c:Location {id: 'C'})
            CREATE (b)-[:CONNECTS {distance: 3.0}]->(c)
        """)
        
        # UDFの登録（未実装なので失敗する）
        def calculate_path_cost(node_costs: list, edge_costs: list) -> float:
            """パス内のノードコストとエッジコストの合計"""
            pass  # 実装されていない
        
        db_conn.create_function("calculate_path_cost", calculate_path_cost)
        
        # パスのコストを計算
        result = db_conn.execute("""
            MATCH path = (a:Location {id: 'A'})-[:CONNECTS*]->(c:Location {id: 'C'})
            UNWIND nodes(path) as n
            WITH path, collect(n.cost) as node_costs
            UNWIND relationships(path) as r
            WITH path, node_costs, collect(r.distance) as edge_costs
            RETURN calculate_path_cost(node_costs, edge_costs) as total_cost
        """)
        
        # 期待値: ノードコスト(10+20+15) + エッジコスト(5+3) = 53
        row = result.get_next()
        assert row[0] == 53.0
    
    def test_validate_path_hierarchy_udf(self, db_conn):
        """階層的なパスの妥当性を検証するUDF"""
        db_conn.execute("CREATE NODE TABLE URI (path STRING, PRIMARY KEY(path))")
        db_conn.execute("CREATE REL TABLE CHILD_OF (FROM URI TO URI)")
        
        # 階層的なURIの作成
        uris = [
            "req://system",
            "req://system/auth",
            "req://system/auth/login",
            "req://system/db",
            "req://invalid/path"
        ]
        
        for uri in uris:
            db_conn.execute(f"CREATE (:URI {{path: '{uri}'}})")
        
        # 関係の作成
        db_conn.execute("""
            MATCH (p:URI {path: 'req://system'}), (c:URI {path: 'req://system/auth'})
            CREATE (c)-[:CHILD_OF]->(p)
        """)
        db_conn.execute("""
            MATCH (p:URI {path: 'req://system/auth'}), (c:URI {path: 'req://system/auth/login'})
            CREATE (c)-[:CHILD_OF]->(p)
        """)
        
        # UDFの登録（未実装）
        def validate_path_hierarchy(path_list: list) -> bool:
            """パスが階層的に正しいかを検証"""
            pass  # 未実装
        
        db_conn.create_function("validate_path_hierarchy", validate_path_hierarchy)
        
        # パスの検証
        result = db_conn.execute("""
            MATCH path = (c:URI {path: 'req://system/auth/login'})-[:CHILD_OF*]->(r:URI {path: 'req://system'})
            WITH [n IN nodes(path) | n.path] as path_list
            RETURN validate_path_hierarchy(path_list) as is_valid
        """)
        
        row = result.get_next()
        assert row[0] == True


class TestGraphStructureValidationUDF:
    """グラフ構造検証UDFのテスト"""
    
    @pytest.fixture
    def db_conn(self):
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        yield conn
    
    def test_detect_cycles_udf(self, db_conn):
        """循環参照を検出するUDF"""
        db_conn.execute("CREATE NODE TABLE Module (name STRING, PRIMARY KEY(name))")
        db_conn.execute("CREATE REL TABLE DEPENDS_ON (FROM Module TO Module)")
        
        # モジュールの作成
        modules = ["A", "B", "C", "D"]
        for mod in modules:
            db_conn.execute(f"CREATE (:Module {{name: '{mod}'}})")
        
        # 依存関係の作成（Cで循環）
        deps = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "B")]  # D->Bで循環
        for src, dst in deps:
            db_conn.execute(f"""
                MATCH (s:Module {{name: '{src}'}}), (d:Module {{name: '{dst}'}})
                CREATE (s)-[:DEPENDS_ON]->(d)
            """)
        
        # UDFの登録（未実装）
        def detect_cycle_in_path(node_ids: list) -> bool:
            """パス内に循環があるかを検出"""
            pass
        
        db_conn.create_function("detect_cycle_in_path", detect_cycle_in_path)
        
        # 循環の検出
        result = db_conn.execute("""
            MATCH path = (start:Module)-[:DEPENDS_ON*1..10]->(end:Module)
            WITH path, [n IN nodes(path) | n.name] as node_names
            WHERE detect_cycle_in_path(node_names)
            RETURN distinct node_names
            LIMIT 1
        """)
        
        row = result.get_next()
        assert "B" in row[0] and "C" in row[0] and "D" in row[0]
    
    def test_validate_graph_constraints_udf(self, db_conn):
        """グラフの制約を検証するUDF"""
        db_conn.execute("CREATE NODE TABLE Person (id STRING, age INT64, PRIMARY KEY(id))")
        db_conn.execute("CREATE REL TABLE PARENT_OF (FROM Person TO Person)")
        
        # 人物の作成
        people = [
            ("alice", 30),
            ("bob", 25),  # aliceより若いのに親になる（不正）
            ("charlie", 5)
        ]
        
        for person_id, age in people:
            db_conn.execute(f"CREATE (:Person {{id: '{person_id}', age: {age}}})")
        
        # 関係の作成
        db_conn.execute("""
            MATCH (p:Person {id: 'bob'}), (c:Person {id: 'alice'})
            CREATE (p)-[:PARENT_OF]->(c)
        """)
        
        # UDFの登録（未実装）
        def validate_parent_child_ages(parent_age: int, child_age: int) -> bool:
            """親が子より年上かを検証"""
            pass
        
        db_conn.create_function("validate_parent_child_ages", validate_parent_child_ages)
        
        # 制約違反の検出
        result = db_conn.execute("""
            MATCH (parent:Person)-[:PARENT_OF]->(child:Person)
            WHERE NOT validate_parent_child_ages(parent.age, child.age)
            RETURN parent.id, child.id
        """)
        
        row = result.get_next()
        assert row[0] == "bob" and row[1] == "alice"


class TestEdgePropertyCalculationUDF:
    """エッジプロパティ計算UDFのテスト"""
    
    @pytest.fixture
    def db_conn(self):
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        yield conn
    
    def test_calculate_similarity_score_udf(self, db_conn):
        """ノード間の類似度を計算するUDF"""
        db_conn.execute("CREATE NODE TABLE Document (id STRING, tags STRING[], PRIMARY KEY(id))")
        db_conn.execute("CREATE REL TABLE SIMILAR_TO (FROM Document TO Document, score DOUBLE)")
        
        # ドキュメントの作成
        docs = [
            ("doc1", ["python", "ml", "data"]),
            ("doc2", ["python", "ml", "ai"]),
            ("doc3", ["java", "web", "api"])
        ]
        
        for doc_id, tags in docs:
            tags_str = "['" + "','".join(tags) + "']"
            db_conn.execute(f"CREATE (:Document {{id: '{doc_id}', tags: {tags_str}}})")
        
        # UDFの登録（未実装）
        def calculate_jaccard_similarity(tags1: list, tags2: list) -> float:
            """Jaccard類似度を計算"""
            pass
        
        db_conn.create_function("calculate_jaccard_similarity", calculate_jaccard_similarity)
        
        # 類似度の計算と関係の作成
        result = db_conn.execute("""
            MATCH (d1:Document), (d2:Document)
            WHERE d1.id < d2.id
            WITH d1, d2, calculate_jaccard_similarity(d1.tags, d2.tags) as similarity
            WHERE similarity > 0.3
            RETURN d1.id, d2.id, similarity
            ORDER BY similarity DESC
        """)
        
        row = result.get_next()
        # doc1とdoc2が最も類似（2/4 = 0.5）
        assert row[0] == "doc1" and row[1] == "doc2"
        assert abs(row[2] - 0.5) < 0.01
    
    def test_calculate_weighted_distance_udf(self, db_conn):
        """重み付き距離を計算するUDF"""
        db_conn.execute("CREATE NODE TABLE City (name STRING, lat DOUBLE, lon DOUBLE, importance INT64, PRIMARY KEY(name))")
        
        cities = [
            ("Tokyo", 35.6762, 139.6503, 10),
            ("Osaka", 34.6937, 135.5023, 7),
            ("Kyoto", 35.0116, 135.7681, 8)
        ]
        
        for name, lat, lon, imp in cities:
            db_conn.execute(f"CREATE (:City {{name: '{name}', lat: {lat}, lon: {lon}, importance: {imp}}})")
        
        # UDFの登録（未実装）
        def calculate_weighted_distance(lat1: float, lon1: float, lat2: float, lon2: float, 
                                       imp1: int, imp2: int) -> float:
            """重要度を考慮した距離計算"""
            pass
        
        db_conn.create_function("calculate_weighted_distance", calculate_weighted_distance)
        
        result = db_conn.execute("""
            MATCH (c1:City {name: 'Tokyo'}), (c2:City)
            WHERE c1 <> c2
            RETURN c2.name, 
                   calculate_weighted_distance(c1.lat, c1.lon, c2.lat, c2.lon, 
                                             c1.importance, c2.importance) as weighted_dist
            ORDER BY weighted_dist
        """)
        
        row = result.get_next()
        # 京都の方が大阪より重要度が高いので、重み付き距離は短くなるはず
        assert row[0] == "Kyoto"


class TestCustomAggregationUDF:
    """カスタム集約UDFのテスト"""
    
    @pytest.fixture
    def db_conn(self):
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        yield conn
    
    def test_percentile_aggregation_udf(self, db_conn):
        """パーセンタイル集約UDF"""
        db_conn.execute("CREATE NODE TABLE Sensor (id STRING, readings DOUBLE[], PRIMARY KEY(id))")
        
        # センサーデータの作成
        sensors = [
            ("sensor1", [10.5, 12.3, 11.8, 13.2, 10.9]),
            ("sensor2", [20.1, 22.5, 21.3, 23.8, 20.7]),
            ("sensor3", [15.2, 16.8, 15.9, 17.5, 15.5])
        ]
        
        for sensor_id, readings in sensors:
            readings_str = "[" + ",".join(map(str, readings)) + "]"
            db_conn.execute(f"CREATE (:Sensor {{id: '{sensor_id}', readings: {readings_str}}})")
        
        # UDFの登録（未実装）
        def calculate_percentile(values: list, percentile: float) -> float:
            """指定されたパーセンタイルを計算"""
            pass
        
        db_conn.create_function("calculate_percentile", calculate_percentile)
        
        # 各センサーの90パーセンタイルを計算
        result = db_conn.execute("""
            MATCH (s:Sensor)
            RETURN s.id, calculate_percentile(s.readings, 0.9) as p90
            ORDER BY s.id
        """)
        
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        
        # sensor1のP90は約13.0のはず
        assert abs(rows[0][1] - 13.0) < 0.5
    
    def test_recursive_sum_udf(self, db_conn):
        """再帰的な合計を計算するUDF"""
        db_conn.execute("CREATE NODE TABLE Category (name STRING, value INT64, PRIMARY KEY(name))")
        db_conn.execute("CREATE REL TABLE SUBCATEGORY_OF (FROM Category TO Category)")
        
        # カテゴリツリーの作成
        categories = [
            ("root", 10),
            ("branch1", 20),
            ("branch2", 30),
            ("leaf1", 5),
            ("leaf2", 8),
            ("leaf3", 12)
        ]
        
        for name, value in categories:
            db_conn.execute(f"CREATE (:Category {{name: '{name}', value: {value}}})")
        
        # 階層関係の作成
        relations = [
            ("branch1", "root"),
            ("branch2", "root"),
            ("leaf1", "branch1"),
            ("leaf2", "branch1"),
            ("leaf3", "branch2")
        ]
        
        for child, parent in relations:
            db_conn.execute(f"""
                MATCH (c:Category {{name: '{child}'}}), (p:Category {{name: '{parent}'}})
                CREATE (c)-[:SUBCATEGORY_OF]->(p)
            """)
        
        # UDFの登録（未実装）
        def calculate_subtree_sum(node_values: list, tree_structure: list) -> int:
            """サブツリーの合計を計算"""
            pass
        
        db_conn.create_function("calculate_subtree_sum", calculate_subtree_sum)
        
        # rootからのサブツリー合計を計算
        result = db_conn.execute("""
            MATCH (root:Category {name: 'root'})
            MATCH path = (leaf:Category)-[:SUBCATEGORY_OF*0..]->(root)
            WITH root, collect(distinct leaf.value) as all_values
            RETURN calculate_subtree_sum(all_values, []) as total
        """)
        
        row = result.get_next()
        # 全ノードの合計: 10+20+30+5+8+12 = 85
        assert row[0] == 85


class TestComplexTypeHandlingUDF:
    """複雑な型処理UDFのテスト"""
    
    @pytest.fixture
    def db_conn(self):
        db = kuzu.Database(":memory:")
        conn = kuzu.Connection(db)
        yield conn
    
    def test_list_operations_udf(self, db_conn):
        """LIST型の高度な操作UDF"""
        db_conn.execute("CREATE NODE TABLE Product (id STRING, features STRING[], ratings INT64[], PRIMARY KEY(id))")
        
        products = [
            ("prod1", ["waterproof", "lightweight", "durable"], [4, 5, 3, 5, 4]),
            ("prod2", ["lightweight", "affordable"], [3, 3, 4, 2]),
            ("prod3", ["durable", "premium", "waterproof"], [5, 5, 4, 5])
        ]
        
        for prod_id, features, ratings in products:
            features_str = "['" + "','".join(features) + "']"
            ratings_str = "[" + ",".join(map(str, ratings)) + "]"
            db_conn.execute(f"CREATE (:Product {{id: '{prod_id}', features: {features_str}, ratings: {ratings_str}}})")
        
        # UDFの登録（未実装）
        def filter_by_feature_and_rating(features: list, ratings: list, 
                                        required_features: list, min_avg_rating: float) -> bool:
            """特徴と評価でフィルタリング"""
            pass
        
        db_conn.create_function("filter_by_feature_and_rating", filter_by_feature_and_rating)
        
        # 防水で平均評価4以上の製品を検索
        result = db_conn.execute("""
            MATCH (p:Product)
            WHERE filter_by_feature_and_rating(p.features, p.ratings, ['waterproof'], 4.0)
            RETURN p.id
            ORDER BY p.id
        """)
        
        rows = []
        while result.has_next():
            rows.append(result.get_next()[0])
        
        assert rows == ["prod1", "prod3"]
    
    def test_map_operations_udf(self, db_conn):
        """MAP型の操作UDF"""
        db_conn.execute("CREATE NODE TABLE Config (name STRING, settings STRING, PRIMARY KEY(name))")
        
        # JSON風の設定を文字列として保存
        configs = [
            ("app1", '{"timeout": 30, "retries": 3, "cache": true}'),
            ("app2", '{"timeout": 60, "retries": 5, "cache": false}'),
            ("app3", '{"timeout": 45, "retries": 3, "cache": true, "debug": true}')
        ]
        
        for name, settings in configs:
            db_conn.execute(f"CREATE (:Config {{name: '{name}', settings: '{settings}'}})")
        
        # UDFの登録（未実装）
        def parse_and_validate_config(config_str: str, required_keys: list) -> bool:
            """設定文字列を解析して必須キーの存在を確認"""
            pass
        
        db_conn.create_function("parse_and_validate_config", parse_and_validate_config)
        
        # debugキーを持つ設定を検索
        result = db_conn.execute("""
            MATCH (c:Config)
            WHERE parse_and_validate_config(c.settings, ['debug'])
            RETURN c.name
        """)
        
        row = result.get_next()
        assert row[0] == "app3"
    
    def test_nested_structure_udf(self, db_conn):
        """ネストした構造の処理UDF"""
        db_conn.execute("CREATE NODE TABLE Event (id STRING, metadata STRING, PRIMARY KEY(id))")
        
        # ネストしたメタデータ
        events = [
            ("evt1", '{"user": {"id": 123, "role": "admin"}, "action": "login", "timestamp": 1234567890}'),
            ("evt2", '{"user": {"id": 456, "role": "user"}, "action": "upload", "data": {"size": 1024}}'),
            ("evt3", '{"user": {"id": 789, "role": "admin"}, "action": "delete", "target": {"type": "file", "id": "abc"}}')
        ]
        
        for evt_id, metadata in events:
            db_conn.execute(f"CREATE (:Event {{id: '{evt_id}', metadata: '{metadata}'}})")
        
        # UDFの登録（未実装）
        def extract_nested_value(json_str: str, path: str) -> str:
            """ネストしたJSONから値を抽出（path: "user.role"のような形式）"""
            pass
        
        db_conn.create_function("extract_nested_value", extract_nested_value)
        
        # adminユーザーのイベントを検索
        result = db_conn.execute("""
            MATCH (e:Event)
            WHERE extract_nested_value(e.metadata, 'user.role') = 'admin'
            RETURN e.id
            ORDER BY e.id
        """)
        
        rows = []
        while result.has_next():
            rows.append(result.get_next()[0])
        
        assert rows == ["evt1", "evt3"]


if __name__ == "__main__":
    # すべてのテストを実行（すべて失敗するはず）
    pytest.main([__file__, "-v", "--tb=short"])