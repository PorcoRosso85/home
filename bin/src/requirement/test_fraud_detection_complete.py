#!/usr/bin/env python3
"""
不正検知システムの完全なシミュレーションテスト
TDDアプローチ: RED -> GREEN -> REFACTOR
"""
import sys
import os
import pytest

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

from graph.infrastructure.cypher_executor import CypherExecutor


class TestFraudDetectionSimulation:
    """不正検知システムシミュレーションのテストクラス"""
    
    @pytest.fixture
    def db_connection(self):
        """テスト用のデータベース接続"""
        os.environ["LD_LIBRARY_PATH"] = "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
        os.environ["RGL_DB_PATH"] = "/home/nixos/bin/src/kuzu/kuzu_db"
        
        # 直接KuzuDBに接続
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "kuzu", 
            "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu/__init__.py"
        )
        kuzu = importlib.util.module_from_spec(spec)
        sys.modules['kuzu'] = kuzu
        spec.loader.exec_module(kuzu)
        
        db = kuzu.Database("/home/nixos/bin/src/kuzu/kuzu_db")
        return kuzu.Connection(db)
    
    @pytest.fixture
    def executor(self, db_connection):
        """Cypherクエリ実行用"""
        return CypherExecutor(db_connection)
    
    def test_01_要件ノード作成_全20件以上(self, executor):
        """REDフェーズ: 20件以上の要件ノードが作成されることを確認"""
        # 要件の総数を確認
        result = executor.execute("""
            MATCH (r:RequirementEntity)
            RETURN count(r) as count
        """)
        
        assert result["data"][0][0] >= 20, f"要件数が不足: {result['data'][0][0]}件（20件以上必要）"
    
    def test_02_階層構造_親子関係が存在(self, executor):
        """REDフェーズ: CONTAINS_LOCATION関係が存在することを確認"""
        # 親子関係の数を確認
        result = executor.execute("""
            MATCH (parent:LocationURI)-[:CONTAINS_LOCATION]->(child:LocationURI)
            RETURN count(*) as count
        """)
        
        assert result["data"][0][0] > 0, "親子関係（CONTAINS_LOCATION）が1つも存在しない"
    
    def test_03_依存関係_DEPENDS_ONが存在(self, executor):
        """REDフェーズ: DEPENDS_ON関係が存在することを確認"""
        # 依存関係の数を確認
        result = executor.execute("""
            MATCH (r1:RequirementEntity)-[:DEPENDS_ON]->(r2:RequirementEntity)
            RETURN count(*) as count
        """)
        
        assert result["data"][0][0] > 0, "依存関係（DEPENDS_ON）が1つも存在しない"
    
    def test_04_階層構造_3階層以上の深さ(self, executor):
        """REDフェーズ: 3階層以上の深さがあることを確認"""
        # 最大の階層深さを取得
        result = executor.execute("""
            MATCH path = (root:LocationURI)-[:CONTAINS_LOCATION*]->(leaf:LocationURI)
            WHERE NOT (leaf)-[:CONTAINS_LOCATION]->(:LocationURI)
            RETURN max(length(path)) as max_depth
        """)
        
        max_depth = result["data"][0][0] if result["data"] else 0
        assert max_depth >= 2, f"階層の深さが不足: {max_depth + 1}階層（3階層以上必要）"
    
    def test_05_不正検知システム_メイン要件が存在(self, executor):
        """REDフェーズ: 不正検知システムのメイン要件が存在することを確認"""
        result = executor.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.title CONTAINS '不正検知システム'
            RETURN r.id, r.title
        """)
        
        assert len(result["data"]) > 0, "不正検知システムのメイン要件が存在しない"
    
    def test_06_パフォーマンス要件_階層が正しい(self, executor):
        """REDフェーズ: パフォーマンス要件が正しい階層にあることを確認"""
        result = executor.execute("""
            MATCH (main:RequirementEntity)-[:DEPENDS_ON*0..3]-(perf:RequirementEntity)
            WHERE main.title CONTAINS '不正検知システム'
            AND perf.title CONTAINS 'パフォーマンス'
            RETURN perf.id, perf.title
        """)
        
        assert len(result["data"]) > 0, "パフォーマンス要件が不正検知システムの階層下に存在しない"
    
    def test_07_DQLで親子関係を取得可能(self, executor):
        """REDフェーズ: DQLで親子関係を正しく取得できることを確認"""
        # 親から子への関係を取得
        result = executor.execute("""
            MATCH (parent:LocationURI)-[:CONTAINS_LOCATION]->(child:LocationURI)
            MATCH (parent)-[:LOCATES_LocationURI_RequirementEntity]->(pr:RequirementEntity)
            MATCH (child)-[:LOCATES_LocationURI_RequirementEntity]->(cr:RequirementEntity)
            RETURN pr.title as parent_title, cr.title as child_title
            LIMIT 5
        """)
        
        assert len(result["data"]) > 0, "DQLで親子関係を取得できない"
        
        # 取得した関係が正しいことを確認
        for parent_title, child_title in result["data"]:
            assert parent_title is not None, "親要件のタイトルがnull"
            assert child_title is not None, "子要件のタイトルがnull"
    
    def test_08_実装詳細_欠落情報の確認(self, executor):
        """GREENフェーズ: 実装に必要な詳細が欠落していることを確認"""
        # 機械学習モデル要件を取得
        result = executor.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.title CONTAINS '機械学習' OR r.title CONTAINS 'モデル'
            RETURN r.title, r.description
        """)
        
        if len(result["data"]) > 0:
            for title, description in result["data"]:
                # 具体的なパラメータが記載されていないことを確認
                assert "木の数" not in description, "Random Forestの具体的パラメータが含まれている"
                assert "ユニット数" not in description, "LSTMの具体的パラメータが含まれている"


def test_DQL実行結果_部下視点での分析():
    """部下視点でのデータベース内容分析"""
    print("\n=== 部下視点でのデータベース内容分析 ===")
    print("※実際のテスト実行後に詳細な分析を実施")
    print("- 取得可能な情報の一覧")
    print("- 実装に不足している情報の一覧")
    print("- 結論: データベースだけで実装可能か")


if __name__ == "__main__":
    # pytestを使わない場合の簡易実行
    print("テストを実行するには pytest を使用してください:")
    print("pytest test_fraud_detection_complete.py -v")