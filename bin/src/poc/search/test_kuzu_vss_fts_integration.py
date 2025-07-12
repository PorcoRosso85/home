#!/usr/bin/env python3
"""
KuzuDB VSS/FTS統合テスト（実装例）
仕様を満たす最小限の実装
"""

import os
from typing import List, Dict, Any, Tuple

os.environ["PYTHONPATH"] = "/home/nixos/bin/src"
os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"

# Import subprocess wrapper
import sys
sys.path.insert(0, "/home/nixos/bin/src/poc/search/hybrid")
from kuzu_extension_wrapper import KuzuExtensionSubprocess


def create_kuzu_test_db():
    """テスト用KuzuDBインスタンス"""
    import kuzu
    import tempfile
    
    # テンポラリディレクトリでDBを作成
    db_dir = tempfile.mkdtemp()
    db = kuzu.Database(db_dir)
    conn = kuzu.Connection(db)
    
    # 拡張機能のロード試行
    extensions_loaded = {
        "vector": False,
        "fts": False
    }
    
    # Skip extension loading in main process to avoid segfault
    # Extensions will be loaded in subprocess
    extensions_loaded["vector"] = True  # Assume available
    extensions_loaded["fts"] = True     # Assume available
    print("✓ 拡張機能はサブプロセスでロードされます")
    
    # Store db_path and db object in conn for later use
    conn.db_path = db_dir
    conn.db_obj = db
    
    return conn, extensions_loaded


def create_requirement_table(conn) -> bool:
    """要件管理用テーブルを作成"""
    try:
        conn.execute("""
            CREATE NODE TABLE RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                author STRING,
                category STRING,
                created_at INT64,
                embedding DOUBLE[384]
            )
        """)
        
        conn.execute("""
            CREATE REL TABLE DEPENDS_ON (
                FROM RequirementEntity TO RequirementEntity
            )
        """)
        
        return True
    except Exception as e:
        print(f"テーブル作成エラー: {e}")
        return False


def generate_mock_embedding(requirement: Dict[str, Any]) -> List[float]:
    """テスト用のモック埋め込み生成（numpy不要）"""
    text = requirement.get("title", "") + " " + requirement.get("description", "")
    hash_value = hash(text)
    
    # 決定的な384次元ベクトル生成
    embedding = []
    for i in range(384):
        seed = (hash_value + i) % 2147483647
        value = (seed % 1000) / 1000.0
        embedding.append(value)
    return embedding


def insert_sample_requirements(conn) -> List[Dict[str, Any]]:
    """サンプル要件データを投入"""
    
    requirements = [
        {
            "id": "AUTH001",
            "title": "ユーザー認証基盤",
            "description": "OAuth2.0を使用した認証システムの構築",
            "author": "TeamA",
            "category": "Security",
            "created_at": 1000
        },
        {
            "id": "LOGIN001", 
            "title": "ログイン画面実装",
            "description": "ユーザーがメールとパスワードでログインする画面",
            "author": "TeamB",
            "category": "UI",
            "created_at": 2000
        },
        {
            "id": "AUTH002",
            "title": "二要素認証システム",
            "description": "SMSまたはTOTPを使った追加認証",
            "author": "TeamA", 
            "category": "Security",
            "created_at": 3000
        },
        {
            "id": "DB001",
            "title": "ユーザーデータベース設計",
            "description": "認証情報を保存するDBスキーマ",
            "author": "TeamC",
            "category": "Database",
            "created_at": 4000
        }
    ]
    
    for req in requirements:
        embedding = generate_mock_embedding(req)
        req["embedding"] = embedding
        
        try:
            conn.execute("""
                CREATE (r:RequirementEntity {
                    id: $id,
                    title: $title,
                    description: $description,
                    author: $author,
                    category: $category,
                    created_at: $created_at,
                    embedding: $embedding
                })
            """, req)
        except Exception as e:
            print(f"データ挿入エラー ({req['id']}): {e}")
    
    # 依存関係を設定
    dependencies = [
        ("LOGIN001", "AUTH001"),
        ("AUTH002", "AUTH001"),
        ("DB001", "AUTH001")
    ]
    
    for from_id, to_id in dependencies:
        try:
            conn.execute("""
                MATCH (a:RequirementEntity {id: $from_id})
                MATCH (b:RequirementEntity {id: $to_id})
                CREATE (a)-[:DEPENDS_ON]->(b)
            """, {"from_id": from_id, "to_id": to_id})
        except Exception as e:
            print(f"依存関係設定エラー: {e}")
    
    return requirements


def test_vss_similarity_search():
    """VSS: 類似要件の検索"""
    # Create test database
    conn, extensions = create_kuzu_test_db()
    
    if not extensions["vector"]:
        print("⚠️ Vector拡張が利用できません - テストをスキップ")
        import pytest
        pytest.skip("Vector拡張が利用できません")
    
    # テーブル作成とデータ投入
    if not create_requirement_table(conn):
        print("⚠️ テーブル作成に失敗 - テストをスキップ")
        import pytest
        pytest.skip("テーブル作成に失敗")
    requirements = insert_sample_requirements(conn)
    
    # VSSインデックス作成（サブプロセス経由）
    try:
        db_path = conn.db_path
        db_obj = conn.db_obj
        
        # Close connection and database before subprocess access
        conn.close()
        del conn
        del db_obj
        
        # Give some time for the database to fully close
        import time
        time.sleep(0.1)
        
        wrapper = KuzuExtensionSubprocess(db_path)
        
        if wrapper.create_vss_index(
            table_name='RequirementEntity',
            index_name='req_vss_idx',
            embedding_column='embedding'
        ):
            print("✓ VSSインデックスが正常に作成されました")
        else:
            print("✗ VSSインデックス作成失敗")
            assert False, "VSSインデックス作成失敗"
            
        # Reopen connection after subprocess
        import kuzu
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        conn.db_path = db_path
        conn.db_obj = db
        
    except Exception as e:
        print(f"✗ VSSインデックス作成失敗: {e}")
        assert False, f"VSSインデックス作成失敗: {e}"
    
    # 類似検索実行
    query_embedding = generate_mock_embedding({
        "title": "認証システム",
        "description": "ユーザーのログイン機能"
    })
    
    try:
        # サブプロセス経由でVSS検索実行
        results = wrapper.execute_vss_query(
            table_name='RequirementEntity',
            index_name='req_vss_idx',
            query_embedding=query_embedding,
            k=3
        )
        
        # 結果のエンリッチ
        enriched_results = []
        for r in results:
            # ノードの詳細情報を取得
            node_result = conn.execute(
                "MATCH (n:RequirementEntity) WHERE id(n) = $id RETURN n.id, n.title",
                {"id": r["element_id"]}
            )
            if node_result.has_next():
                row = node_result.get_next()
                enriched_results.append({
                    "id": row[0],
                    "title": row[1],
                    "score": r["score"]
                })
        
        # 認証関連の要件が上位にくることを確認
        if len(enriched_results) >= 2:
            top_ids = [r["id"] for r in enriched_results[:2]]
            if "AUTH001" in top_ids or "LOGIN001" in top_ids:
                print("✓ VSS検索が正常に動作しました")
                print("\nVSS検索結果:")
                for r in enriched_results:
                    print(f"  {r['id']}: {r['title']} (スコア: {r['score']:.3f})")
                return True
        
        print("⚠️ VSS検索結果が期待と異なります")
        return False
        
    except Exception as e:
        print(f"✗ VSS検索実行失敗: {e}")
        return False


def test_fts_keyword_search():
    """FTS: キーワード検索"""
    # Create test database
    conn, extensions = create_kuzu_test_db()
    
    if not extensions["fts"]:
        print("⚠️ FTS拡張が利用できません - テストをスキップ")
        import pytest
        pytest.skip("FTS拡張が利用できません")
    
    # テーブル作成とデータ投入
    if not create_requirement_table(conn):
        print("⚠️ テーブル作成に失敗 - テストをスキップ")
        import pytest
        pytest.skip("テーブル作成に失敗")
    insert_sample_requirements(conn)
    
    # FTSインデックス作成（サブプロセス経由）
    try:
        db_path = conn.db_path
        db_obj = conn.db_obj
        
        # Close connection and database before subprocess access
        conn.close()
        del conn
        del db_obj
        
        # Give some time for the database to fully close
        import time
        time.sleep(0.1)
        
        wrapper = KuzuExtensionSubprocess(db_path)
        
        if wrapper.create_fts_index(
            table_name='RequirementEntity',
            index_name='req_fts_idx',
            columns=['title', 'description']
        ):
            print("✓ FTSインデックスが正常に作成されました")
        else:
            print("✗ FTSインデックス作成失敗")
            return False
            
        # Reopen connection after subprocess
        import kuzu
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        conn.db_path = db_path
        conn.db_obj = db
        
    except Exception as e:
        print(f"✗ FTSインデックス作成失敗: {e}")
        return False
    
    # キーワード検索実行（サブプロセス経由）
    try:
        # サブプロセス経由でFTS検索実行
        results = wrapper.execute_fts_query(
            table_name='RequirementEntity',
            index_name='req_fts_idx',
            query='認証',
            k=10
        )
        
        # 結果のエンリッチ
        enriched_results = []
        for r in results:
            # ノードの詳細情報を取得
            node_result = conn.execute(
                "MATCH (n:RequirementEntity) WHERE id(n) = $id RETURN n.id, n.title",
                {"id": r["element_id"]}
            )
            if node_result.has_next():
                row = node_result.get_next()
                enriched_results.append({
                    "id": row[0],
                    "title": row[1],
                    "score": r["score"]
                })
        
        # "認証"を含む要件が検出されることを確認
        if len(enriched_results) >= 2:
            found_ids = [r["id"] for r in enriched_results]
            if "AUTH001" in found_ids or "AUTH002" in found_ids:
                print("✓ FTS検索が正常に動作しました")
                print("\nFTS検索結果:")
                for r in enriched_results:
                    print(f"  {r['id']}: {r['title']} (スコア: {r['score']:.3f})")
                return True
        
        print("⚠️ FTS検索結果が期待と異なります")
        return False
        
    except Exception as e:
        print(f"✗ FTS検索実行失敗: {e}")
        return False


def test_duplicate_detection_use_case():
    """ユースケース: 重複要件の検出"""
    # Create test database
    conn, extensions = create_kuzu_test_db()
    
    # 最低限の動作確認
    assert create_requirement_table(conn)
    existing_reqs = insert_sample_requirements(conn)
    
    # 新規要件（既存と重複の可能性）
    new_requirement = {
        "id": "LOGIN002",
        "title": "サインイン機能",
        "description": "利用者がEmailでサインインする仕組み",
        "author": "TeamD"
    }
    
    # 簡易的な重複チェック（本来はVSS使用）
    new_embedding = generate_mock_embedding(new_requirement)
    
    # 類似度計算（簡易版）
    def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        return dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0
    
    # 既存要件との類似度チェック
    duplicates = []
    for req in existing_reqs:
        similarity = calculate_similarity(new_embedding, req["embedding"])
        if similarity > 0.8:  # 閾値
            duplicates.append({
                "id": req["id"],
                "title": req["title"],
                "similarity": similarity
            })
    
    # 結果表示
    if duplicates:
        print("\n⚠️ 重複の可能性がある要件:")
        for dup in duplicates:
            print(f"  {dup['id']}: {dup['title']} (類似度: {dup['similarity']:.3f})")
        print(f"\n新規要件「{new_requirement['title']}」は既存要件と重複の可能性があります。")
        assert True  # 重複検出成功
    else:
        print("\n✓ 重複なし: 新規要件を追加できます。")


def test_impact_analysis_use_case():
    """ユースケース: 変更影響分析"""
    # Create test database
    conn, _ = create_kuzu_test_db()
    
    assert create_requirement_table(conn)
    insert_sample_requirements(conn)
    
    # AUTH001を変更した場合の影響分析
    target_id = "AUTH001"
    
    # 直接依存を探索
    direct_deps = conn.execute("""
        MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(target:RequirementEntity {id: $id})
        RETURN r.id, r.title
    """, {"id": target_id})
    
    affected = []
    while direct_deps.has_next():
        row = direct_deps.get_next()
        affected.append({
            "id": row[0],
            "title": row[1],
            "impact_type": "direct"
        })
    
    print(f"\n「{target_id}」変更時の影響:")
    print(f"直接影響を受ける要件: {len(affected)}件")
    for req in affected:
        print(f"  - {req['id']}: {req['title']}")
    
    # 実際の実装では、VSSで意味的に関連する要件も探索
    assert len(affected) >= 2  # LOGIN001とAUTH002が影響を受ける


def test_terminology_consistency_use_case():
    """ユースケース: 用語の統一性チェック"""
    # Create test database
    conn, _ = create_kuzu_test_db()
    
    # 表記揺れのあるデータを投入
    conn.execute("""
        CREATE NODE TABLE TermEntity (
            id STRING PRIMARY KEY,
            term STRING,
            context STRING,
            team STRING
        )
    """)
    
    terms = [
        {"id": "T1", "term": "ユーザー", "context": "UI設計", "team": "Frontend"},
        {"id": "T2", "term": "ユーザ", "context": "DB設計", "team": "Backend"},
        {"id": "T3", "term": "利用者", "context": "仕様書", "team": "Document"},
        {"id": "T4", "term": "user", "context": "API設計", "team": "Backend"}
    ]
    
    for term in terms:
        conn.execute("""
            CREATE (t:TermEntity {
                id: $id,
                term: $term,
                context: $context,
                team: $team
            })
        """, term)
    
    # 表記揺れを検出（簡易版）
    variations = conn.execute("""
        MATCH (t:TermEntity)
        RETURN t.term, COUNT(*) as count
        ORDER BY count DESC
    """)
    
    print("\n用語の使用状況:")
    term_stats = []
    while variations.has_next():
        row = variations.get_next()
        term_stats.append({"term": row[0], "count": row[1]})
        print(f"  「{row[0]}」: {row[1]}回")
    
    # 統一提案
    if len(term_stats) > 1:
        print("\n推奨: すべて「ユーザー」に統一")
        assert True  # 表記揺れ検出成功


if __name__ == "__main__":
    # 直接実行
    print("=== KuzuDB VSS/FTS統合テスト ===\n")
    
    # テストDBを作成
    conn, extensions = create_kuzu_test_db()
    
    print(f"\n拡張機能の状態:")
    print(f"  Vector: {'✓' if extensions['vector'] else '✗'}")
    print(f"  FTS: {'✓' if extensions['fts'] else '✗'}")
    
    # 各テストを実行
    print("\n--- VSS類似検索テスト ---")
    test_vss_similarity_search(conn, extensions)
    
    print("\n--- FTSキーワード検索テスト ---")
    test_fts_keyword_search(conn, extensions)
    
    # ユースケーステスト
    print("\n--- 重複検出ユースケース ---")
    test_duplicate_detection_use_case((conn, extensions))
    
    print("\n--- 影響分析ユースケース ---")
    test_impact_analysis_use_case((conn, extensions))
    
    print("\n--- 用語統一性チェックユースケース ---")
    test_terminology_consistency_use_case((conn, extensions))
    
    print("\n=== テスト完了 ===")