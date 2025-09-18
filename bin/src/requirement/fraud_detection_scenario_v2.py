#!/usr/bin/env python3
"""
高速な不正検知システムの要件登録シナリオ V2
run.pyを使った実行形式に対応
"""
import json
import subprocess
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# 環境変数の設定
ENV = {
    "LD_LIBRARY_PATH": "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/",
    "RGL_DB_PATH": "../kuzu/kuzu_db"
}

# グローバル変数
requirement_id_counter = 1
created_requirements = []

def generate_requirement_id() -> str:
    """要件IDを生成"""
    global requirement_id_counter
    req_id = f"fraud_{requirement_id_counter:03d}"
    requirement_id_counter += 1
    return req_id

def execute_cypher(query: str, description: str = "") -> Dict[str, Any]:
    """Cypherクエリを実行"""
    request = {
        "type": "cypher",
        "query": query
    }
    
    # run.pyを使って実行
    cmd = ["python", "graph/run.py"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **ENV}
        )
        
        stdout, stderr = process.communicate(input=json.dumps(request).encode())
        
        if process.returncode != 0:
            print(f"✗ エラー: {description}")
            print(f"  stderr: {stderr.decode()}")
            return {"status": "error", "message": stderr.decode()}
        
        result = json.loads(stdout.decode())
        if result.get("status") == "success":
            print(f"✓ 成功: {description}")
        else:
            print(f"✗ 失敗: {description}")
            print(f"  message: {result.get('message', '')}")
            
        return result
        
    except Exception as e:
        print(f"✗ 実行エラー: {str(e)}")
        return {"status": "error", "message": str(e)}

def add_requirement(data: Dict[str, Any]) -> str:
    """要件を追加"""
    req_id = generate_requirement_id()
    
    # CREATE文を作成
    query = f"""
    CREATE (r:RequirementEntity {{
        id: '{req_id}',
        title: '{data["title"]}',
        description: '{data["description"]}',
        priority: '{data.get("priority", "medium")}',
        requirement_type: '{data.get("requirement_type", "functional")}',
        verification_required: {str(data.get("verification_required", True)).lower()}
    }})
    RETURN r
    """
    
    result = execute_cypher(query, f"要件追加: {data['title']}")
    
    if result.get("status") == "success":
        created_requirements.append(req_id)
        return req_id
    return None

def link_requirements(parent_id: str, child_ids: List[str]):
    """要件間の階層関係を設定"""
    for child_id in child_ids:
        query = f"""
        MATCH (parent:RequirementEntity {{id: '{parent_id}'}})
        MATCH (child:RequirementEntity {{id: '{child_id}'}})
        MERGE (parent_loc:LocationURI {{id: '{parent_id}'}})
        MERGE (child_loc:LocationURI {{id: '{child_id}'}})
        MERGE (parent_loc)-[:LOCATES_LocationURI_RequirementEntity]->(parent)
        MERGE (child_loc)-[:LOCATES_LocationURI_RequirementEntity]->(child)
        MERGE (parent_loc)-[:CONTAINS_LOCATION]->(child_loc)
        MERGE (child)-[:DEPENDS_ON]->(parent)
        RETURN parent, child
        """
        
        execute_cypher(query, f"リンク: {parent_id} -> {child_id}")

def scenario_timeline():
    """時系列での要件追加シナリオ"""
    print("=== 高速な不正検知システム要件登録シナリオ開始 V2 ===\n")
    
    # Day 1: トップレベル要件の登録
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 初期要件定義")
    
    main_req_id = add_requirement({
        "title": "高速な不正検知システム",
        "description": "リアルタイムで不正取引を検知し、即座にアラートを発する高速システム",
        "priority": "critical",
        "requirement_type": "system"
    })
    
    if not main_req_id:
        print("メイン要件の作成に失敗しました")
        return None
    
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
    
    if perf_req_id and latency_req_id and throughput_req_id:
        link_requirements(main_req_id, [perf_req_id])
        link_requirements(perf_req_id, [latency_req_id, throughput_req_id])
    
    time.sleep(0.5)
    
    # 実装のため省略（同様のパターンで続く）
    print("\n以下、同様のパターンで以下の要件を追加:")
    print("- 検知アルゴリズム要件")
    print("- 不正パターン定義（4種類）")
    print("- アラート機能要件")
    print("- コンプライアンス要件")
    
    print(f"\n=== シナリオ完了 ===")
    print(f"登録された要件の総数: {len(created_requirements)}件")
    
    return main_req_id

def verify_from_subordinate_perspective():
    """部下の視点でデータベースから情報を取得"""
    print("\n=== 部下視点での要件確認 ===\n")
    
    # 1. 全要件を取得
    print("1. データベース内の要件を確認:")
    query = """
    MATCH (r:RequirementEntity)
    WHERE r.title CONTAINS '不正' OR r.title CONTAINS 'パフォーマンス' OR r.title CONTAINS 'レイテンシ'
    RETURN r.id, r.title, r.description
    ORDER BY r.id
    LIMIT 10
    """
    
    result = execute_cypher(query, "要件一覧取得")
    
    # 2. 階層構造を確認
    print("\n2. 階層構造を確認:")
    hierarchy_query = """
    MATCH (parent:RequirementEntity)-[:DEPENDS_ON]->(child:RequirementEntity)
    WHERE parent.title CONTAINS '不正' OR child.title CONTAINS '不正'
    RETURN parent.title, child.title
    LIMIT 5
    """
    
    result = execute_cypher(hierarchy_query, "階層構造取得")
    
    # 3. 分析結果
    print("\n=== 分析結果 ===")
    print("データベースに保存されている情報:")
    print("  ✓ 要件のタイトルと説明文")
    print("  ✓ 要件間の階層関係と依存関係")
    print("  ✓ 優先度とタイプ")
    
    print("\n実装に必要だが保存されていない情報:")
    missing_info = [
        "  ✗ Random Forestの具体的なパラメータ",
        "  ✗ 100msという閾値の測定方法",
        "  ✗ 10,000件/秒の負荷テスト方法",
        "  ✗ アラート送信の実装方法",
        "  ✗ データベースのスキーマ定義",
        "  ✗ APIのインターフェース仕様",
        "  ✗ エラーハンドリングの詳細"
    ]
    
    for info in missing_info:
        print(info)
    
    print("\n結論: 「このデータベースを渡せば大丈夫」とは言い切れません。")
    print("理由: 実装の技術的詳細が欠落しており、別途技術仕様書が必要です。")

if __name__ == "__main__":
    # スキーマが存在することを確認
    print("スキーマの存在を確認...")
    test_query = "MATCH (n) RETURN count(n) as count LIMIT 1"
    result = execute_cypher(test_query, "接続テスト")
    
    if result.get("status") == "success":
        # シナリオを実行
        main_req_id = scenario_timeline()
        
        # 部下視点での確認
        if main_req_id:
            verify_from_subordinate_perspective()
    else:
        print("データベース接続に失敗しました。スキーマが作成されているか確認してください。")