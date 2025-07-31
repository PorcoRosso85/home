#!/usr/bin/env python3
"""E2Eリレーションクエリの検証

2つのDB間を跨いだ端から端までのクエリパスを検証
"""

import tempfile
import shutil
from pathlib import Path
import kuzu

def log(level: str, component: str, message: str, **kwargs):
    """Local logging function for testing"""
    context = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    print(f"[{level}] {component}: {message} {context}".strip())

def setup_user_db(db_path: Path):
    """UserデータベースのセットアップとUser間リレーション"""
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    
    # Userスキーマ
    conn.execute("CREATE NODE TABLE User(id INT64, name STRING, PRIMARY KEY(id))")
    conn.execute("CREATE REL TABLE FOLLOWS(FROM User TO User, since INT32)")
    
    # Userデータ
    conn.execute("CREATE (:User {id: 1, name: 'Alice'})")
    conn.execute("CREATE (:User {id: 2, name: 'Bob'})")
    conn.execute("CREATE (:User {id: 3, name: 'Charlie'})")
    conn.execute("CREATE (:User {id: 4, name: 'David'})")
    
    # User間のリレーション（ソーシャルネットワーク）
    conn.execute("MATCH (a:User {id: 1}), (b:User {id: 2}) CREATE (a)-[:FOLLOWS {since: 2022}]->(b)")
    conn.execute("MATCH (a:User {id: 2}), (b:User {id: 3}) CREATE (a)-[:FOLLOWS {since: 2023}]->(b)")
    conn.execute("MATCH (a:User {id: 3}), (b:User {id: 4}) CREATE (a)-[:FOLLOWS {since: 2024}]->(b)")
    
    # チェックポイントを実行
    conn.execute("CHECKPOINT")
    
    return db, conn

def setup_product_db(db_path: Path):
    """ProductデータベースのセットアップとProduct間リレーション"""
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    
    # Productスキーマ
    conn.execute("CREATE NODE TABLE Product(id INT64, name STRING, category STRING, PRIMARY KEY(id))")
    conn.execute("CREATE REL TABLE SIMILAR_TO(FROM Product TO Product, score DOUBLE)")
    
    # Productデータ
    conn.execute("CREATE (:Product {id: 101, name: 'Laptop A', category: 'Electronics'})")
    conn.execute("CREATE (:Product {id: 102, name: 'Laptop B', category: 'Electronics'})")
    conn.execute("CREATE (:Product {id: 103, name: 'Phone X', category: 'Electronics'})")
    conn.execute("CREATE (:Product {id: 104, name: 'Tablet Y', category: 'Electronics'})")
    
    # Product間のリレーション（類似性）
    conn.execute("MATCH (a:Product {id: 101}), (b:Product {id: 102}) CREATE (a)-[:SIMILAR_TO {score: 0.9}]->(b)")
    conn.execute("MATCH (a:Product {id: 102}), (b:Product {id: 103}) CREATE (a)-[:SIMILAR_TO {score: 0.7}]->(b)")
    conn.execute("MATCH (a:Product {id: 103}), (b:Product {id: 104}) CREATE (a)-[:SIMILAR_TO {score: 0.8}]->(b)")
    
    # チェックポイントを実行
    conn.execute("CHECKPOINT")
    
    return db, conn

def setup_integrated_db(db_path: Path, user_db_path: Path, product_db_path: Path):
    """統合データベースのセットアップ（COPY FROM + クロスDBリレーション）"""
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    
    # スキーマ定義
    conn.execute("CREATE NODE TABLE User(id INT64, name STRING, PRIMARY KEY(id))")
    conn.execute("CREATE NODE TABLE Product(id INT64, name STRING, category STRING, PRIMARY KEY(id))")
    conn.execute("CREATE REL TABLE FOLLOWS(FROM User TO User, since INT32)")
    conn.execute("CREATE REL TABLE SIMILAR_TO(FROM Product TO Product, score DOUBLE)")
    conn.execute("CREATE REL TABLE OWNS(FROM User TO Product, quantity INT32)")
    
    # 手動でデータをコピー（ATTACHは読み取り専用のため）
    # User DBから読み取り
    user_db = kuzu.Database(str(user_db_path))
    user_conn = kuzu.Connection(user_db)
    
    users = user_conn.execute("MATCH (u:User) RETURN u.id, u.name")
    while users.has_next():
        id, name = users.get_next()
        conn.execute(f"CREATE (:User {{id: {id}, name: '{name}'}})")
    
    follows = user_conn.execute("MATCH (a:User)-[f:FOLLOWS]->(b:User) RETURN a.id, b.id, f.since")
    while follows.has_next():
        from_id, to_id, since = follows.get_next()
        conn.execute(f"MATCH (a:User {{id: {from_id}}}), (b:User {{id: {to_id}}}) CREATE (a)-[:FOLLOWS {{since: {since}}}]->(b)")
    
    # Product DBから読み取り
    product_db = kuzu.Database(str(product_db_path))
    product_conn = kuzu.Connection(product_db)
    
    products = product_conn.execute("MATCH (p:Product) RETURN p.id, p.name, p.category")
    while products.has_next():
        id, name, category = products.get_next()
        conn.execute(f"CREATE (:Product {{id: {id}, name: '{name}', category: '{category}'}})")
    
    similar = product_conn.execute("MATCH (a:Product)-[s:SIMILAR_TO]->(b:Product) RETURN a.id, b.id, s.score")
    while similar.has_next():
        from_id, to_id, score = similar.get_next()
        conn.execute(f"MATCH (a:Product {{id: {from_id}}}), (b:Product {{id: {to_id}}}) CREATE (a)-[:SIMILAR_TO {{score: {score}}}]->(b)")
    
    # クロスDBリレーション（User-Product間）
    conn.execute("MATCH (u:User {id: 2}), (p:Product {id: 101}) CREATE (u)-[:OWNS {quantity: 1}]->(p)")  # Bob owns Laptop A
    conn.execute("MATCH (u:User {id: 3}), (p:Product {id: 103}) CREATE (u)-[:OWNS {quantity: 2}]->(p)")  # Charlie owns Phone X
    conn.execute("MATCH (u:User {id: 4}), (p:Product {id: 102}) CREATE (u)-[:OWNS {quantity: 1}]->(p)")  # David owns Laptop B
    
    return db, conn

def test_follow_chain_to_product_when_users_connected_then_finds_owned_products():
    """テスト: ユーザー間のフォローチェーンを辿って所有製品を発見できる
    
    シナリオ: Alice → Bob → Charlie とフォローチェーンがあり、
    CharileがPhone Xを所有している場合、
    Aliceから2ホップ以内のフォローチェーンを辿って所有製品を見つける
    """
    # 一時ディレクトリ作成
    temp_dir = tempfile.mkdtemp()
    user_db_path = Path(temp_dir) / "user.db"
    product_db_path = Path(temp_dir) / "product.db"
    integrated_db_path = Path(temp_dir) / "integrated.db"
    
    try:
        # 各DBのセットアップ
        user_db, user_conn = setup_user_db(user_db_path)
        product_db, product_conn = setup_product_db(product_db_path)
        integrated_db, conn = setup_integrated_db(integrated_db_path, user_db_path, product_db_path)
        
        log('DEBUG', 'graph_docs.test_e2e', 'Starting E2E Query 1', query_type='follow_chain_to_product', start_user='Alice')
        # Alice(1) → Bob(2) → Charlie(3) → Phone X(103)
        result = conn.execute("""
            MATCH path = (alice:User {name: 'Alice'})-[:FOLLOWS*1..2]->(owner:User)-[:OWNS]->(product:Product)
            RETURN alice.name as start_user, owner.name as product_owner, product.name as owned_product
        """)
        
        # 結果検証
        found = False
        while result.has_next():
            row = result.get_next()
            log('DEBUG', 'graph_docs.test_e2e', 'Query result', start_user=row[0], product_owner=row[1], owned_product=row[2], path_type='follows_chain_owns')
            if row[1] == 'Charlie' and row[2] == 'Phone X':
                found = True
        
        assert found, "Alice should be able to find Charlie's Phone X through follow chain"
        
    finally:
        # クリーンアップ
        shutil.rmtree(temp_dir)


def test_product_similarity_recommendation_when_user_owns_product_then_recommends_similar():
    """テスト: ユーザーが所有する製品に基づいて類似製品をレコメンドできる
    
    シナリオ: BobがLaptop Aを所有しており、
    Laptop A → Laptop B → Phone X という類似性チェーンがある場合、
    Bobに対して類似製品をレコメンドする
    """
    # 一時ディレクトリ作成
    temp_dir = tempfile.mkdtemp()
    user_db_path = Path(temp_dir) / "user.db"
    product_db_path = Path(temp_dir) / "product.db"
    integrated_db_path = Path(temp_dir) / "integrated.db"
    
    try:
        # 各DBのセットアップ
        user_db, user_conn = setup_user_db(user_db_path)
        product_db, product_conn = setup_product_db(product_db_path)
        integrated_db, conn = setup_integrated_db(integrated_db_path, user_db_path, product_db_path)
        
        log('DEBUG', 'graph_docs.test_e2e', 'Starting E2E Query 2', query_type='product_similarity_recommendation')
        # Bob(2) → Laptop A(101) → Laptop B(102) → Phone X(103)
        result = conn.execute("""
            MATCH (user:User {name: 'Bob'})-[:OWNS]->(owned:Product),
                  (owned)-[:SIMILAR_TO*1..2]->(recommended:Product)
            WHERE owned.id <> recommended.id
            RETURN user.name, owned.name, recommended.name, recommended.category
        """)
        
        # 結果検証
        recommendations = []
        while result.has_next():
            row = result.get_next()
            log('DEBUG', 'graph_docs.test_e2e', 'Query result', user=row[0], owned_product=row[1], recommended_product=row[2], category=row[3], path_type='owns_similar_to')
            recommendations.append(row[2])
        
        assert 'Laptop B' in recommendations, "Bob should get Laptop B as recommendation"
        assert 'Phone X' in recommendations, "Bob should get Phone X as recommendation through similarity chain"
        
    finally:
        # クリーンアップ
        shutil.rmtree(temp_dir)


def test_social_product_full_path_when_following_and_owning_then_traces_complete_path():
    """テスト: ソーシャルグラフと製品グラフを跨いだ完全なパスを追跡できる
    
    シナリオ: Alice → Bob → Charlie → Phone X → Tablet Y という
    フォローチェーンと製品所有、製品類似性を含む完全なパスを追跡する
    """
    # 一時ディレクトリ作成
    temp_dir = tempfile.mkdtemp()
    user_db_path = Path(temp_dir) / "user.db"
    product_db_path = Path(temp_dir) / "product.db"
    integrated_db_path = Path(temp_dir) / "integrated.db"
    
    try:
        # 各DBのセットアップ
        user_db, user_conn = setup_user_db(user_db_path)
        product_db, product_conn = setup_product_db(product_db_path)
        integrated_db, conn = setup_integrated_db(integrated_db_path, user_db_path, product_db_path)
        
        log('DEBUG', 'graph_docs.test_e2e', 'Starting E2E Query 3', query_type='social_product_full_path')
        # Alice → Bob → Charlie → Phone X → Tablet Y
        # KuzuDBの制約により、クエリを分割して実行
        result = conn.execute("""
            MATCH (start:User {name: 'Alice'})-[:FOLLOWS*1..3]->(owner:User)-[:OWNS]->(prod:Product)
            RETURN start.name, owner.name, prod.name, prod.id
        """)
        paths = []
        while result.has_next():
            row = result.get_next()
            paths.append(row)
        
        # パスが見つかったことを確認
        assert len(paths) > 0, "Should find at least one path from Alice to owned products"
        
        # 各製品から類似製品へのパスを探索
        similar_products_found = False
        for start_name, owner_name, prod_name, prod_id in paths:
            # 直接の類似製品を探索
            similar_result = conn.execute(f"""
                MATCH (p:Product {{id: {prod_id}}})-[:SIMILAR_TO]->(target:Product)
                RETURN target.name
            """)
            while similar_result.has_next():
                target_name = similar_result.get_next()[0]
                log('DEBUG', 'graph_docs.test_e2e', 'Query result', start_user=start_name, product_owner=owner_name, owned_product=prod_name, similar_product=target_name, path_type='follows_owns_similar')
                if prod_name == 'Phone X' and target_name == 'Tablet Y':
                    similar_products_found = True
        
        assert similar_products_found, "Should find path from Phone X to Tablet Y through similarity"
        
    finally:
        # クリーンアップ
        shutil.rmtree(temp_dir)


def test_common_interest_users_when_similar_products_owned_then_finds_connections():
    """テスト: 類似製品を所有するユーザー同士の関係を発見できる
    
    シナリオ: 異なるユーザーが類似製品を所有している場合、
    その関係を発見して共通の興味を持つユーザーを特定する
    """
    # 一時ディレクトリ作成
    temp_dir = tempfile.mkdtemp()
    user_db_path = Path(temp_dir) / "user.db"
    product_db_path = Path(temp_dir) / "product.db"
    integrated_db_path = Path(temp_dir) / "integrated.db"
    
    try:
        # 各DBのセットアップ
        user_db, user_conn = setup_user_db(user_db_path)
        product_db, product_conn = setup_product_db(product_db_path)
        integrated_db, conn = setup_integrated_db(integrated_db_path, user_db_path, product_db_path)
        
        log('DEBUG', 'graph_docs.test_e2e', 'Starting E2E Query 4', query_type='common_interest_users')
        # 類似製品を所有するユーザー同士の関係
        result = conn.execute("""
            MATCH (u1:User)-[:OWNS]->(p1:Product)-[:SIMILAR_TO]->(p2:Product)<-[:OWNS]-(u2:User)
            WHERE u1.id < u2.id
            RETURN u1.name, p1.name, p2.name, u2.name
        """)
        
        # 結果検証
        connections = []
        while result.has_next():
            row = result.get_next()
            log('DEBUG', 'graph_docs.test_e2e', 'Query result', user1=row[0], user1_product=row[1], user2_product=row[2], user2=row[3], relationship='similar_products')
            connections.append((row[0], row[3]))
        
        # Bob (Laptop A) と Charlie (Phone X) は類似製品チェーンで繋がっている
        # Laptop A → Laptop B → Phone X
        assert len(connections) > 0, "Should find users with similar product interests"
        
    finally:
        # クリーンアップ
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # 各テストを順番に実行
    test_follow_chain_to_product_when_users_connected_then_finds_owned_products()
    print("✓ Test 1 passed: Follow chain to product")
    
    test_product_similarity_recommendation_when_user_owns_product_then_recommends_similar()
    print("✓ Test 2 passed: Product similarity recommendation")
    
    test_social_product_full_path_when_following_and_owning_then_traces_complete_path()
    print("✓ Test 3 passed: Social product full path")
    
    test_common_interest_users_when_similar_products_owned_then_finds_connections()
    print("✓ Test 4 passed: Common interest users")
    
    print("\nAll tests passed!")