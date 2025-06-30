"""
プロダクトマネージャー視点の要件追加テスト

このファイルは、PM視点から要件管理システムに追加すべき要件を定義します。
階層ルール（Level 0:ビジョン、Level 1:アーキテクチャ、Level 2:モジュール、Level 3:コンポーネント、Level 4:タスク）に従います。
"""

# PM視点の要件定義例
PM_REQUIREMENTS = {
    # ユーザビリティに関する要件
    "usability_requirements": [
        {
            "query": """
            CREATE (r:RequirementEntity {
                id: 'vision_usability_001',
                title: 'ユーザー中心の要件管理システム',
                description: '技術者だけでなく、ビジネスステークホルダーも簡単に理解・操作できる要件管理システムの実現',
                priority: 3,
                requirement_type: 'non-functional',
                status: 'proposed',
                acceptance_criteria: '1. 非技術者でも要件の追加・閲覧が可能 2. ビジュアルな要件関係図の提供 3. 自然言語での要件検索'
            })
            CREATE (l:LocationURI {id: 'loc://vision/usability_001'})
            CREATE (l)-[:LOCATES]->(r)
            RETURN r.id as requirement_id, r.title as title
            """,
            "expected": "success",
            "reason": "Level 0のビジョンとして定義"
        },
        {
            "query": """
            MATCH (vision:RequirementEntity {id: 'vision_usability_001'})
            CREATE (ui:RequirementEntity {
                id: 'arch_ui_layer_001',
                title: 'ユーザーインターフェース層',
                description: 'ビジネスユーザー向けの直感的なUIを提供するアーキテクチャ層',
                priority: 2,
                requirement_type: 'functional',
                status: 'proposed',
                acceptance_criteria: '1. Web UI提供 2. ドラッグ&ドロップ操作 3. リアルタイム更新'
            })
            CREATE (l:LocationURI {id: 'loc://architecture/ui_layer_001'})
            CREATE (l)-[:LOCATES]->(ui)
            CREATE (ui)-[:DEPENDS_ON {dependency_type: 'implements', reason: 'ビジョンを実現するUI層'}]->(vision)
            RETURN ui.id as requirement_id, ui.title as title
            """,
            "expected": "success",
            "reason": "Level 1のアーキテクチャとして、Level 0のビジョンに依存"
        }
    ],
    
    # ビジネス価値に関する要件
    "business_value_requirements": [
        {
            "query": """
            CREATE (r:RequirementEntity {
                id: 'vision_business_value_001',
                title: 'ビジネス価値の可視化と最大化',
                description: '各要件のビジネス価値を定量化し、ROIを最大化する要件管理を実現',
                priority: 4,
                requirement_type: 'business',
                status: 'proposed',
                acceptance_criteria: '1. 各要件のビジネス価値スコアリング 2. ROI計算機能 3. 価値ベースの優先順位付け',
                implementation_details: '{"value_metrics": ["revenue_impact", "cost_reduction", "user_satisfaction", "time_to_market"]}'
            })
            CREATE (l:LocationURI {id: 'loc://vision/business_value_001'})
            CREATE (l)-[:LOCATES]->(r)
            RETURN r.id as requirement_id, r.title as title
            """,
            "expected": "success",
            "reason": "Level 0のビジョンとして定義"
        },
        {
            "query": """
            MATCH (vision:RequirementEntity {id: 'vision_business_value_001'})
            CREATE (analytics:RequirementEntity {
                id: 'arch_analytics_engine_001',
                title: 'ビジネス分析エンジン',
                description: 'ビジネス価値を計算・分析するためのアナリティクスエンジン',
                priority: 3,
                requirement_type: 'functional',
                status: 'proposed',
                acceptance_criteria: '1. 価値計算アルゴリズム実装 2. ダッシュボード機能 3. レポート生成'
            })
            CREATE (l:LocationURI {id: 'loc://architecture/analytics_engine_001'})
            CREATE (l)-[:LOCATES]->(analytics)
            CREATE (analytics)-[:DEPENDS_ON {dependency_type: 'implements', reason: '価値可視化を実現する分析エンジン'}]->(vision)
            RETURN analytics.id as requirement_id, analytics.title as title
            """,
            "expected": "success",
            "reason": "Level 1のアーキテクチャとして、Level 0のビジョンに依存"
        }
    ],
    
    # 優先順位管理に関する要件
    "priority_management_requirements": [
        {
            "query": """
            CREATE (r:RequirementEntity {
                id: 'vision_priority_mgmt_001',
                title: 'インテリジェントな優先順位管理',
                description: 'ビジネス価値、技術的依存関係、リソース制約を考慮した動的な優先順位付け',
                priority: 5,
                requirement_type: 'functional',
                status: 'proposed',
                acceptance_criteria: '1. 多次元優先度計算 2. 制約条件の考慮 3. 優先順位の自動更新'
            })
            CREATE (l:LocationURI {id: 'loc://vision/priority_mgmt_001'})
            CREATE (l)-[:LOCATES]->(r)
            RETURN r.id as requirement_id, r.title as title
            """,
            "expected": "success",
            "reason": "Level 0のビジョンとして定義"
        },
        {
            "query": """
            MATCH (vision:RequirementEntity {id: 'vision_priority_mgmt_001'})
            CREATE (optimizer:RequirementEntity {
                id: 'module_priority_optimizer_001',
                title: '優先順位最適化モジュール',
                description: '制約条件下での優先順位最適化を行うアルゴリズムモジュール',
                priority: 4,
                requirement_type: 'functional',
                status: 'proposed',
                acceptance_criteria: '1. 線形計画法による最適化 2. リアルタイム再計算 3. What-if分析'
            })
            CREATE (l:LocationURI {id: 'loc://module/priority_optimizer_001'})
            CREATE (l)-[:LOCATES]->(optimizer)
            CREATE (optimizer)-[:DEPENDS_ON {dependency_type: 'implements', reason: '優先順位管理を実現する最適化モジュール'}]->(vision)
            RETURN optimizer.id as requirement_id, optimizer.title as title
            """,
            "expected": "error",
            "reason": "Level 2のモジュールが直接Level 0のビジョンに依存（階層違反）"
        }
    ],
    
    # ステークホルダー管理に関する要件
    "stakeholder_requirements": [
        {
            "query": """
            CREATE (r:RequirementEntity {
                id: 'vision_stakeholder_001',
                title: 'ステークホルダー協調プラットフォーム',
                description: '開発者、PM、経営層、顧客など全ステークホルダーが協調して要件を管理できるプラットフォーム',
                priority: 3,
                requirement_type: 'business',
                status: 'proposed',
                acceptance_criteria: '1. 役割ベースのアクセス制御 2. コメント・議論機能 3. 承認ワークフロー',
                implementation_details: '{"roles": ["developer", "pm", "executive", "customer"], "workflows": ["review", "approval", "change_request"]}'
            })
            CREATE (l:LocationURI {id: 'loc://vision/stakeholder_001'})
            CREATE (l)-[:LOCATES]->(r)
            RETURN r.id as requirement_id, r.title as title
            """,
            "expected": "success",
            "reason": "Level 0のビジョンとして定義"
        },
        {
            "query": """
            MATCH (vision:RequirementEntity {id: 'vision_stakeholder_001'})
            CREATE (collab:RequirementEntity {
                id: 'arch_collaboration_layer_001',
                title: 'コラボレーション層',
                description: 'ステークホルダー間の協調を実現するアーキテクチャ層',
                priority: 2,
                requirement_type: 'functional',
                status: 'proposed',
                acceptance_criteria: '1. リアルタイム通知 2. バージョン管理 3. 監査証跡'
            })
            CREATE (l:LocationURI {id: 'loc://architecture/collaboration_layer_001'})
            CREATE (l)-[:LOCATES]->(collab)
            CREATE (collab)-[:DEPENDS_ON {dependency_type: 'implements', reason: 'ステークホルダー協調を実現するコラボレーション層'}]->(vision)
            RETURN collab.id as requirement_id, collab.title as title
            """,
            "expected": "success",
            "reason": "Level 1のアーキテクチャとして、Level 0のビジョンに依存"
        },
        {
            "query": """
            MATCH (arch:RequirementEntity {id: 'arch_collaboration_layer_001'})
            CREATE (notif:RequirementEntity {
                id: 'module_notification_001',
                title: '通知管理モジュール',
                description: 'ステークホルダーへの通知を管理するモジュール',
                priority: 2,
                requirement_type: 'functional',
                status: 'proposed',
                acceptance_criteria: '1. Email/Slack通知 2. 通知設定管理 3. 通知履歴'
            })
            CREATE (l:LocationURI {id: 'loc://module/notification_001'})
            CREATE (l)-[:LOCATES]->(notif)
            CREATE (notif)-[:DEPENDS_ON {dependency_type: 'part_of', reason: 'コラボレーション層の一部'}]->(arch)
            RETURN notif.id as requirement_id, notif.title as title
            """,
            "expected": "success",
            "reason": "Level 2のモジュールがLevel 1のアーキテクチャに依存（正しい階層）"
        }
    ],
    
    # 階層違反の例（システムから拒否されるべき要件）
    "violation_examples": [
        {
            "query": """
            CREATE (task:RequirementEntity {
                id: 'task_implement_001',
                title: 'APIエンドポイント実装',
                description: '要件一覧取得APIの実装',
                priority: 1,
                requirement_type: 'task',
                status: 'proposed'
            })
            CREATE (vision:RequirementEntity {
                id: 'vision_violation_001',
                title: '要件管理ビジョン',
                description: 'タスクに依存するビジョン（階層違反）',
                priority: 5,
                requirement_type: 'vision',
                status: 'proposed'
            })
            CREATE (l1:LocationURI {id: 'loc://task/implement_001'})
            CREATE (l2:LocationURI {id: 'loc://vision/violation_001'})
            CREATE (l1)-[:LOCATES]->(task)
            CREATE (l2)-[:LOCATES]->(vision)
            CREATE (vision)-[:DEPENDS_ON {dependency_type: 'requires', reason: '階層違反の例'}]->(task)
            RETURN vision.id as requirement_id, vision.title as title
            """,
            "expected": "error",
            "reason": "Level 0のビジョンがLevel 4のタスクに依存（階層違反）"
        },
        {
            "query": """
            CREATE (r:RequirementEntity {
                id: 'circular_001',
                title: '循環参照要件',
                description: '自己参照する要件（違反）',
                priority: 1,
                requirement_type: 'functional',
                status: 'proposed'
            })
            CREATE (l:LocationURI {id: 'loc://module/circular_001'})
            CREATE (l)-[:LOCATES]->(r)
            CREATE (r)-[:DEPENDS_ON {dependency_type: 'circular', reason: '自己参照'}]->(r)
            RETURN r.id as requirement_id, r.title as title
            """,
            "expected": "error",
            "reason": "自己参照（循環参照）"
        }
    ]
}

def create_pm_requirements_cypher():
    """PM視点の要件をCypherクエリとして出力"""
    all_queries = []
    
    for category, requirements in PM_REQUIREMENTS.items():
        all_queries.append(f"-- {category}")
        for req in requirements:
            all_queries.append(f"-- Expected: {req['expected']} - {req['reason']}")
            all_queries.append(req['query'])
            all_queries.append("")
    
    return "\n".join(all_queries)

if __name__ == "__main__":
    print("=== PM視点の要件追加クエリ ===")
    print(create_pm_requirements_cypher())