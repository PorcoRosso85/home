#!/usr/bin/env python3
"""
不正検知システムの完全なシミュレーション実装
TDDアプローチ: テストを通すための実装
"""
import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

# 環境変数設定
os.environ["LD_LIBRARY_PATH"] = "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
os.environ["RGL_DB_PATH"] = "/home/nixos/bin/src/kuzu/kuzu_db"

from graph.infrastructure.cypher_executor import CypherExecutor


class FraudDetectionSimulator:
    """不正検知システムのシミュレーター"""
    
    def __init__(self):
        # 直接KuzuDBに接続
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "kuzu", 
            "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu/__init__.py"
        )
        kuzu = importlib.util.module_from_spec(spec)
        sys.modules['kuzu'] = kuzu
        spec.loader.exec_module(kuzu)
        
        # データベース接続
        db = kuzu.Database("/home/nixos/bin/src/kuzu/kuzu_db")
        self.conn = kuzu.Connection(db)
        self.executor = CypherExecutor(self.conn)
        self.requirement_counter = 1
        self.created_requirements = []
    
    def generate_req_id(self) -> str:
        """要件IDを生成"""
        req_id = f"fraud_{self.requirement_counter:03d}"
        self.requirement_counter += 1
        return req_id
    
    def create_requirement(self, data: Dict[str, Any]) -> str:
        """要件ノードを作成"""
        req_id = self.generate_req_id()
        
        query = """
        CREATE (r:RequirementEntity {
            id: $id,
            title: $title,
            description: $description,
            priority: $priority,
            requirement_type: $requirement_type,
            verification_required: $verification_required
        })
        RETURN r
        """
        
        params = {
            "id": req_id,
            "title": data["title"],
            "description": data["description"],
            "priority": data.get("priority", "medium"),
            "requirement_type": data.get("requirement_type", "functional"),
            "verification_required": data.get("verification_required", True)
        }
        
        result = self.executor.execute(query, params)
        
        if not result.get("error"):
            self.created_requirements.append(req_id)
            print(f"✓ 作成: {data['title']} (ID: {req_id})")
            return req_id
        else:
            print(f"✗ エラー: {result['error']}")
            return None
    
    def create_hierarchy(self, parent_id: str, child_ids: List[str]):
        """階層関係を作成（CONTAINS_LOCATIONとDEPENDS_ON）"""
        for child_id in child_ids:
            # LocationURIノードを作成
            location_query = """
            MERGE (parent_loc:LocationURI {id: $parent_id})
            MERGE (child_loc:LocationURI {id: $child_id})
            MERGE (parent_loc)-[:CONTAINS_LOCATION]->(child_loc)
            """
            
            result = self.executor.execute(location_query, {
                "parent_id": parent_id,
                "child_id": child_id
            })
            
            if result.get("error"):
                print(f"✗ LocationURI作成エラー: {result['error']}")
                continue
            
            # RequirementEntityとLocationURIをリンク
            link_query = """
            MATCH (parent:RequirementEntity {id: $parent_id})
            MATCH (child:RequirementEntity {id: $child_id})
            MATCH (parent_loc:LocationURI {id: $parent_id})
            MATCH (child_loc:LocationURI {id: $child_id})
            MERGE (parent_loc)-[:LOCATES_LocationURI_RequirementEntity]->(parent)
            MERGE (child_loc)-[:LOCATES_LocationURI_RequirementEntity]->(child)
            MERGE (child)-[:DEPENDS_ON]->(parent)
            """
            
            result = self.executor.execute(link_query, {
                "parent_id": parent_id,
                "child_id": child_id
            })
            
            if not result.get("error"):
                print(f"  → リンク: {parent_id} -> {child_id}")
            else:
                print(f"  ✗ リンクエラー: {result['error']}")
    
    def run_complete_simulation(self):
        """完全なシミュレーションを実行"""
        print("=== 不正検知システム要件の完全登録開始 ===\n")
        
        # Level 1: メインシステム要件
        main_id = self.create_requirement({
            "title": "高速な不正検知システム",
            "description": "リアルタイムで不正取引を検知し、即座にアラートを発する高速システム",
            "priority": "critical",
            "requirement_type": "system"
        })
        
        # Level 2: 主要コンポーネント
        perf_id = self.create_requirement({
            "title": "パフォーマンス要件",
            "description": "処理速度とスループットに関する要件",
            "priority": "critical",
            "requirement_type": "non_functional"
        })
        
        algo_id = self.create_requirement({
            "title": "不正検知アルゴリズム",
            "description": "機械学習ベースの異常検知アルゴリズムを実装",
            "priority": "high",
            "requirement_type": "functional"
        })
        
        pattern_id = self.create_requirement({
            "title": "不正パターン定義",
            "description": "検知すべき不正取引のパターンを定義",
            "priority": "high",
            "requirement_type": "functional"
        })
        
        alert_id = self.create_requirement({
            "title": "アラート機能",
            "description": "不正検知時の通知機能",
            "priority": "high",
            "requirement_type": "functional"
        })
        
        compliance_id = self.create_requirement({
            "title": "コンプライアンス要件",
            "description": "法規制に準拠したデータ保持とプライバシー保護",
            "priority": "critical",
            "requirement_type": "compliance"
        })
        
        # メインの階層関係を作成
        if main_id:
            self.create_hierarchy(main_id, [perf_id, algo_id, pattern_id, alert_id, compliance_id])
        
        # Level 3: パフォーマンス要件の詳細
        latency_id = self.create_requirement({
            "title": "レイテンシ要件",
            "description": "1取引あたり100ms以内で不正判定を完了すること",
            "priority": "critical",
            "requirement_type": "non_functional"
        })
        
        throughput_id = self.create_requirement({
            "title": "スループット要件",
            "description": "秒間10,000件の取引を処理可能であること",
            "priority": "critical",
            "requirement_type": "non_functional"
        })
        
        scalability_id = self.create_requirement({
            "title": "スケーラビリティ要件",
            "description": "負荷に応じて水平スケーリング可能であること",
            "priority": "high",
            "requirement_type": "non_functional"
        })
        
        if perf_id:
            self.create_hierarchy(perf_id, [latency_id, throughput_id, scalability_id])
        
        # Level 3: アルゴリズム要件の詳細
        ml_model_id = self.create_requirement({
            "title": "機械学習モデル要件",
            "description": "Random ForestとLSTMのアンサンブルモデルを使用",
            "priority": "high",
            "requirement_type": "functional"
        })
        
        feature_id = self.create_requirement({
            "title": "特徴量エンジニアリング",
            "description": "取引金額、頻度、地理的位置、時間帯を含む15次元の特徴量を使用",
            "priority": "high",
            "requirement_type": "functional"
        })
        
        threshold_id = self.create_requirement({
            "title": "閾値設定",
            "description": "不正確率0.85以上で高リスク、0.6-0.85で中リスクと判定",
            "priority": "high",
            "requirement_type": "functional"
        })
        
        if algo_id:
            self.create_hierarchy(algo_id, [ml_model_id, feature_id, threshold_id])
        
        # Level 3: 不正パターンの詳細
        patterns = [
            {
                "title": "高額連続取引パターン",
                "description": "5分以内に合計100万円以上の取引が3回以上発生",
                "priority": "high"
            },
            {
                "title": "地理的異常パターン",
                "description": "前回取引から500km以上離れた場所で30分以内に取引発生",
                "priority": "high"
            },
            {
                "title": "深夜異常取引パターン",
                "description": "午前2時-5時の間に過去平均の10倍以上の金額の取引",
                "priority": "medium"
            },
            {
                "title": "新規店舗高額取引パターン",
                "description": "初めて利用する店舗で10万円以上の取引",
                "priority": "medium"
            }
        ]
        
        pattern_ids = []
        for pattern in patterns:
            pattern_id_sub = self.create_requirement(pattern)
            if pattern_id_sub:
                pattern_ids.append(pattern_id_sub)
        
        if pattern_id:
            self.create_hierarchy(pattern_id, pattern_ids)
        
        # Level 3: アラート機能の詳細
        realtime_alert_id = self.create_requirement({
            "title": "リアルタイムアラート",
            "description": "高リスク判定から3秒以内にセキュリティチームへ通知",
            "priority": "critical"
        })
        
        escalation_id = self.create_requirement({
            "title": "エスカレーション機能",
            "description": "5分以内に対応がない場合、上級管理者へ自動エスカレーション",
            "priority": "high"
        })
        
        alert_content_id = self.create_requirement({
            "title": "アラート内容",
            "description": "取引ID、金額、リスクスコア、検知パターン、推奨アクションを含む",
            "priority": "high"
        })
        
        if alert_id:
            self.create_hierarchy(alert_id, [realtime_alert_id, escalation_id, alert_content_id])
        
        # Level 3: コンプライアンス要件の詳細
        log_retention_id = self.create_requirement({
            "title": "ログ保持期間",
            "description": "すべての取引ログと判定結果を7年間保持",
            "priority": "critical",
            "requirement_type": "compliance"
        })
        
        privacy_id = self.create_requirement({
            "title": "個人情報保護",
            "description": "PCI-DSS準拠、カード番号は下4桁のみ保存",
            "priority": "critical",
            "requirement_type": "compliance"
        })
        
        audit_log_id = self.create_requirement({
            "title": "監査ログ",
            "description": "すべてのシステムアクセスと設定変更を記録",
            "priority": "high",
            "requirement_type": "compliance"
        })
        
        if compliance_id:
            self.create_hierarchy(compliance_id, [log_retention_id, privacy_id, audit_log_id])
        
        print(f"\n=== シミュレーション完了 ===")
        print(f"作成された要件の総数: {len(self.created_requirements)}件")
        
        return main_id
    
    def verify_hierarchy(self):
        """階層構造を検証"""
        print("\n=== 階層構造の検証 ===")
        
        # 親子関係の総数
        result = self.executor.execute("""
            MATCH (parent:LocationURI)-[:CONTAINS_LOCATION]->(child:LocationURI)
            RETURN count(*) as count
        """)
        print(f"親子関係（CONTAINS_LOCATION）の総数: {result['data'][0][0]}件")
        
        # 依存関係の総数
        result = self.executor.execute("""
            MATCH (r1:RequirementEntity)-[:DEPENDS_ON]->(r2:RequirementEntity)
            RETURN count(*) as count
        """)
        print(f"依存関係（DEPENDS_ON）の総数: {result['data'][0][0]}件")
        
        # 最大階層深さ
        result = self.executor.execute("""
            MATCH path = (root:LocationURI)-[:CONTAINS_LOCATION*]->(leaf:LocationURI)
            WHERE NOT (leaf)-[:CONTAINS_LOCATION]->(:LocationURI)
            RETURN max(length(path)) as max_depth
        """)
        max_depth = result["data"][0][0] if result["data"] else 0
        print(f"最大階層深さ: {max_depth + 1}階層")
    
    def demonstrate_dql_queries(self):
        """DQLクエリの実証"""
        print("\n=== DQLクエリの実証 ===")
        
        print("\n1. 親子関係の取得:")
        result = self.executor.execute("""
            MATCH (parent:LocationURI)-[:CONTAINS_LOCATION]->(child:LocationURI)
            MATCH (parent)-[:LOCATES_LocationURI_RequirementEntity]->(pr:RequirementEntity)
            MATCH (child)-[:LOCATES_LocationURI_RequirementEntity]->(cr:RequirementEntity)
            RETURN pr.title as parent_title, cr.title as child_title
            ORDER BY pr.title
            LIMIT 10
        """)
        
        for parent, child in result["data"]:
            print(f"  {parent} -> {child}")
        
        print("\n2. 特定要件の子要件一覧:")
        result = self.executor.execute("""
            MATCH (parent:RequirementEntity {title: 'パフォーマンス要件'})
            MATCH (child:RequirementEntity)-[:DEPENDS_ON]->(parent)
            RETURN child.title, child.description
        """)
        
        for title, desc in result["data"]:
            print(f"  - {title}: {desc}")
        
        print("\n3. 階層をたどる（トップダウン）:")
        result = self.executor.execute("""
            MATCH (main:RequirementEntity {title: '高速な不正検知システム'})
            OPTIONAL MATCH (main)<-[:DEPENDS_ON]-(level2:RequirementEntity)
            OPTIONAL MATCH (level2)<-[:DEPENDS_ON]-(level3:RequirementEntity)
            RETURN main.title, collect(distinct level2.title) as level2_titles, 
                   collect(distinct level3.title) as level3_titles
        """)
        
        if result["data"]:
            main, level2, level3 = result["data"][0]
            print(f"  メイン: {main}")
            if level2:
                print(f"  レベル2: {', '.join(level2[:5])}...")
            if level3:
                print(f"  レベル3: {', '.join(level3[:5])}...")
    
    def analyze_from_subordinate_perspective(self):
        """部下視点での分析"""
        print("\n=== 部下視点でのデータベース分析 ===")
        
        print("\n取得可能な情報:")
        print("✓ 要件の階層構造（誰が親で誰が子か）")
        print("✓ 要件のタイトルと説明")
        print("✓ 優先度（critical, high, medium）")
        print("✓ 要件タイプ（functional, non_functional, compliance）")
        print("✓ 依存関係")
        
        print("\n実装に必要だが取得できない情報:")
        missing_info = [
            "✗ Random Forestの具体的なパラメータ（木の数、深さ、分割基準）",
            "✗ LSTMの層構造（ユニット数、活性化関数、ドロップアウト率）",
            "✗ 100msレイテンシの測定方法（平均？95パーセンタイル？）",
            "✗ 10,000件/秒の前提条件（CPUコア数、メモリ容量）",
            "✗ 特徴量15次元の具体的な定義と計算方法",
            "✗ 地理的距離の計算アルゴリズム（直線距離？道路距離？）",
            "✗ アラート送信の実装方法（メール？Slack？Webhook？）",
            "✗ データベーススキーマ設計",
            "✗ APIインターフェース仕様",
            "✗ エラーハンドリングとリトライ戦略"
        ]
        
        for info in missing_info:
            print(f"  {info}")
        
        print("\n結論:")
        print("データベースには要件の「構造」と「関係性」は完全に保存されている。")
        print("しかし、実装の「詳細」と「方法」は含まれていない。")
        print("実装に必要な情報の約30-40%しかデータベースから取得できない。")
        print("\n「このデータベースを渡せば大丈夫」とは言い切れません。")


def main():
    """メイン実行関数"""
    simulator = FraudDetectionSimulator()
    
    # 既存データをクリア（オプション）
    print("既存データをクリアしますか？ (y/n): ", end="")
    if input().lower() == 'y':
        simulator.executor.execute("MATCH (n) DETACH DELETE n")
        print("データをクリアしました。")
    
    # シミュレーション実行
    main_req_id = simulator.run_complete_simulation()
    
    # 階層構造の検証
    simulator.verify_hierarchy()
    
    # DQLクエリの実証
    simulator.demonstrate_dql_queries()
    
    # 部下視点での分析
    simulator.analyze_from_subordinate_perspective()


if __name__ == "__main__":
    main()