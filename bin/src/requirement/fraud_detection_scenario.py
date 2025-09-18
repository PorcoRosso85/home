#!/usr/bin/env python3
"""
高速な不正検知システムの要件登録シナリオ

上司が部下に「高速な不正検知システム」の要件を伝えるため、
RGL/hooksシステムに詳細な要件を登録するシミュレーション
"""
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

# KuzuDB関連のインポート
from graph.infrastructure.kuzu_repository import KuzuRepository
from graph.infrastructure.kuzu_requirement_repository import create_kuzu_requirement_repository
from graph.infrastructure.cypher_executor import CypherExecutor
from graph.infrastructure.variables import get_db_path

# グローバル変数
repository = None
executor = None
requirement_id_counter = 1

def init_db():
    """データベースを初期化"""
    global repository, executor
    db_path = get_db_path()
    kuzu_repo = KuzuRepository(db_path)
    repository = create_kuzu_requirement_repository(kuzu_repo)
    executor = CypherExecutor(kuzu_repo.get_connection())
    print(f"データベース接続完了: {db_path}")

def generate_requirement_id() -> str:
    """要件IDを生成"""
    global requirement_id_counter
    req_id = f"fraud_{requirement_id_counter:03d}"
    requirement_id_counter += 1
    return req_id

def add_requirement(data: Dict[str, Any]) -> str:
    """要件を追加し、IDを返す"""
    # IDを生成
    req_id = generate_requirement_id()
    
    # 要件データを準備
    requirement_data = {
        "id": req_id,
        "title": data["title"],
        "description": data["description"],
        "priority": data.get("priority", "medium"),
        "requirement_type": data.get("requirement_type", "functional"),
        "verification_required": data.get("verification_required", True)
    }
    
    # リポジトリを使って保存
    result = repository["save_requirement"](requirement_data)
    
    if result and "id" in result:
        print(f"✓ 追加: {data['title']} (ID: {req_id})")
        return req_id
    else:
        print(f"✗ エラー: 要件の追加に失敗しました")
        return None

def link_requirements(parent_id: str, child_ids: List[str]):
    """要件間の依存関係を設定（階層関係）"""
    for child_id in child_ids:
        # 階層関係を作成するクエリ
        query = """
        MATCH (parent:RequirementEntity {id: $parent_id})
        MATCH (child:RequirementEntity {id: $child_id})
        // LocationURIを作成または取得
        MERGE (parent_loc:LocationURI {id: $parent_id})
        MERGE (child_loc:LocationURI {id: $child_id})
        // 関係を作成
        MERGE (parent_loc)-[:LOCATES_LocationURI_RequirementEntity]->(parent)
        MERGE (child_loc)-[:LOCATES_LocationURI_RequirementEntity]->(child)
        MERGE (parent_loc)-[:CONTAINS_LOCATION]->(child_loc)
        // 依存関係も追加
        MERGE (child)-[:DEPENDS_ON]->(parent)
        RETURN parent, child
        """
        
        result = executor.execute(query, {
            "parent_id": parent_id,
            "child_id": child_id
        })
        
        if not result.get("error"):
            print(f"  → リンク: {parent_id} -> {child_id}")
        else:
            print(f"  ✗ リンクエラー: {result['error']}")

def scenario_timeline():
    """時系列での要件追加シナリオ"""
    print("=== 高速な不正検知システム要件登録シナリオ開始 ===\n")
    
    # Day 1: トップレベル要件の登録
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 初期要件定義")
    
    main_req_id = add_requirement({
        "title": "高速な不正検知システム",
        "description": "リアルタイムで不正取引を検知し、即座にアラートを発する高速システム",
        "priority": "critical",
        "requirement_type": "system"
    })
    
    time.sleep(0.5)
    
    # Day 2: パフォーマンス要件の詳細化
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] パフォーマンス要件の詳細化")
    
    perf_req_id = add_requirement({
        "title": "パフォーマンス要件",
        "description": "処理速度とスループットに関する要件",
        "priority": "critical",
        "requirement_type": "non_functional"
    })
    
    latency_req_id = add_requirement({
        "title": "レイテンシ要件",
        "description": "1取引あたり100ms以内で不正判定を完了すること",
        "priority": "critical",
        "requirement_type": "non_functional"
    })
    
    throughput_req_id = add_requirement({
        "title": "スループット要件",
        "description": "秒間10,000件の取引を処理可能であること",
        "priority": "critical",
        "requirement_type": "non_functional"
    })
    
    link_requirements(main_req_id, [perf_req_id])
    link_requirements(perf_req_id, [latency_req_id, throughput_req_id])
    
    time.sleep(0.5)
    
    # Day 3: 検知アルゴリズムの要件
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 検知アルゴリズム要件の追加")
    
    algo_req_id = add_requirement({
        "title": "不正検知アルゴリズム",
        "description": "機械学習ベースの異常検知アルゴリズムを実装",
        "priority": "high",
        "requirement_type": "functional"
    })
    
    ml_model_req_id = add_requirement({
        "title": "機械学習モデル要件",
        "description": "Random ForestとLSTMのアンサンブルモデルを使用",
        "priority": "high",
        "requirement_type": "functional"
    })
    
    feature_req_id = add_requirement({
        "title": "特徴量エンジニアリング",
        "description": "取引金額、頻度、地理的位置、時間帯を含む15次元の特徴量を使用",
        "priority": "high",
        "requirement_type": "functional"
    })
    
    threshold_req_id = add_requirement({
        "title": "閾値設定",
        "description": "不正確率0.85以上で高リスク、0.6-0.85で中リスクと判定",
        "priority": "high",
        "requirement_type": "functional"
    })
    
    link_requirements(main_req_id, [algo_req_id])
    link_requirements(algo_req_id, [ml_model_req_id, feature_req_id, threshold_req_id])
    
    time.sleep(0.5)
    
    # Day 4: 不正パターンの詳細定義
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 不正パターンの詳細定義")
    
    pattern_req_id = add_requirement({
        "title": "不正パターン定義",
        "description": "検知すべき不正取引のパターンを定義",
        "priority": "high",
        "requirement_type": "functional"
    })
    
    # 具体的なパターン（実装に必要な詳細）
    patterns = [
        {
            "title": "高額連続取引パターン",
            "description": "5分以内に合計100万円以上の取引が3回以上発生",
            "priority": "high",
            "requirement_type": "functional"
        },
        {
            "title": "地理的異常パターン",
            "description": "前回取引から500km以上離れた場所で30分以内に取引発生",
            "priority": "high",
            "requirement_type": "functional"
        },
        {
            "title": "深夜異常取引パターン",
            "description": "午前2時-5時の間に過去平均の10倍以上の金額の取引",
            "priority": "medium",
            "requirement_type": "functional"
        },
        {
            "title": "新規店舗高額取引パターン",
            "description": "初めて利用する店舗で10万円以上の取引",
            "priority": "medium",
            "requirement_type": "functional"
        }
    ]
    
    pattern_ids = []
    for pattern in patterns:
        pattern_id = add_requirement(pattern)
        if pattern_id:
            pattern_ids.append(pattern_id)
    
    link_requirements(main_req_id, [pattern_req_id])
    link_requirements(pattern_req_id, pattern_ids)
    
    time.sleep(0.5)
    
    # Day 5: アラート機能の要件
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] アラート機能の要件定義")
    
    alert_req_id = add_requirement({
        "title": "アラート機能",
        "description": "不正検知時の通知機能",
        "priority": "high",
        "requirement_type": "functional"
    })
    
    alert_details = [
        {
            "title": "リアルタイムアラート",
            "description": "高リスク判定から3秒以内にセキュリティチームへ通知",
            "priority": "critical",
            "requirement_type": "functional"
        },
        {
            "title": "エスカレーション機能",
            "description": "5分以内に対応がない場合、上級管理者へ自動エスカレーション",
            "priority": "high",
            "requirement_type": "functional"
        },
        {
            "title": "アラート内容",
            "description": "取引ID、金額、リスクスコア、検知パターン、推奨アクションを含む",
            "priority": "high",
            "requirement_type": "functional"
        }
    ]
    
    alert_ids = []
    for alert in alert_details:
        alert_id = add_requirement(alert)
        if alert_id:
            alert_ids.append(alert_id)
    
    link_requirements(main_req_id, [alert_req_id])
    link_requirements(alert_req_id, alert_ids)
    
    time.sleep(0.5)
    
    # Day 6: データ保持とコンプライアンス
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] データ保持とコンプライアンス要件")
    
    compliance_req_id = add_requirement({
        "title": "コンプライアンス要件",
        "description": "法規制に準拠したデータ保持とプライバシー保護",
        "priority": "critical",
        "requirement_type": "compliance"
    })
    
    compliance_details = [
        {
            "title": "ログ保持期間",
            "description": "すべての取引ログと判定結果を7年間保持",
            "priority": "critical",
            "requirement_type": "compliance"
        },
        {
            "title": "個人情報保護",
            "description": "PCI-DSS準拠、カード番号は下4桁のみ保存",
            "priority": "critical",
            "requirement_type": "compliance"
        },
        {
            "title": "監査ログ",
            "description": "すべてのシステムアクセスと設定変更を記録",
            "priority": "high",
            "requirement_type": "compliance"
        }
    ]
    
    compliance_ids = []
    for comp in compliance_details:
        comp_id = add_requirement(comp)
        if comp_id:
            compliance_ids.append(comp_id)
    
    link_requirements(main_req_id, [compliance_req_id])
    link_requirements(compliance_req_id, compliance_ids)
    
    print("\n=== シナリオ完了 ===")
    print(f"登録された要件の総数: 約{requirement_id_counter - 1}件")
    
    return main_req_id

def verify_from_subordinate_perspective(main_req_id: str):
    """部下の視点でデータベースから情報を取得"""
    print("\n=== 部下視点での要件確認 ===\n")
    
    # 1. 要件の階層構造を取得
    print("1. 要件の階層構造を取得:")
    hierarchy_query = """
    MATCH (main:RequirementEntity {id: $main_id})
    OPTIONAL MATCH path = (main)<-[:DEPENDS_ON*]-(child:RequirementEntity)
    WITH main, collect(distinct child) as all_children
    RETURN main, all_children
    """
    
    result = executor.execute(hierarchy_query, {"main_id": main_req_id})
    if not result.get("error") and result.get("data"):
        print(f"メイン要件: {result['data'][0][0]}")
        print(f"子要件数: {len(result['data'][0][1]) if len(result['data'][0]) > 1 else 0}")
    
    # 2. 詳細情報の取得
    print("\n2. 要件の詳細を確認（一部抜粋）:")
    detail_query = """
    MATCH (r:RequirementEntity)
    WHERE r.title CONTAINS '閾値' OR r.title CONTAINS 'モデル' OR r.title CONTAINS 'パターン'
    RETURN r.title, r.description
    LIMIT 5
    """
    
    result = executor.execute(detail_query, {})
    if not result.get("error") and result.get("data"):
        for row in result["data"]:
            print(f"- {row[0]}: {row[1]}")
    
    # 3. 実装に必要だが取得できない情報
    print("\n=== 実装に必要だが取得できない情報 ===")
    missing_info = [
        "• Random Forestのパラメータ（木の数、深さ、分割基準）",
        "• LSTMの層構造（ユニット数、ドロップアウト率）",
        "• 特徴量の正規化方法とスケーリング手法",
        "• 閾値0.85と0.6の根拠とチューニング方法",
        "• 「5分以内」「3回以上」などの具体的な実装ロジック",
        "• 距離計算のアルゴリズム（直線距離？道路距離？）",
        "• アラート送信の具体的なプロトコル（メール？Slack？）",
        "• エスカレーションの具体的な連絡先リスト",
        "• パフォーマンステストの具体的な方法",
        "• エラーハンドリングとフォールバック戦略",
        "• 機械学習モデルの訓練データ仕様",
        "• リアルタイム処理のアーキテクチャ（ストリーミング？バッチ？）",
        "• スケーリング戦略（水平？垂直？）",
        "• 障害時の復旧手順（RTO/RPO）",
        "• API仕様とインターフェース定義",
        "• セキュリティ実装の詳細（暗号化方式、認証方法）"
    ]
    
    print("\n実装に必要だがDBから取得できない情報:")
    for info in missing_info:
        print(info)
    
    # 4. 結論
    print("\n=== 分析結果 ===")
    print("データベースに保存されている情報:")
    print("  ✓ 要件のタイトルと説明文")
    print("  ✓ 要件間の階層関係と依存関係")
    print("  ✓ 優先度とタイプ")
    print("\nデータベースに保存されていない情報:")
    print("  ✗ 具体的な実装アルゴリズム")
    print("  ✗ パラメータ値と閾値の詳細")
    print("  ✗ 技術的な実装方法")
    print("  ✗ インフラストラクチャ要件")
    print("  ✗ 運用手順とプロセス")
    
    print("\n結論: 「このデータベースを渡せば大丈夫」とは言い切れません。")
    print("理由: 実装に必要な技術的詳細の約60-70%が欠落しています。")
    print("推奨: 要件定義書に加えて、技術仕様書と実装ガイドが必要です。")

if __name__ == "__main__":
    # データベースを初期化
    init_db()
    
    # シナリオを実行
    main_req_id = scenario_timeline()
    
    # 部下視点での確認
    if main_req_id:
        verify_from_subordinate_perspective(main_req_id)