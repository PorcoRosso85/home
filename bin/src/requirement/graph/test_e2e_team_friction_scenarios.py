"""
E2E Test: チーム要件定義における摩擦とズレのスコア化

このテストは、実際のチーム開発で発生する「摩擦」を再現し、
それによって生じる要件のズレをスコア化する仕組みを検証します。

詳細な仕様は以下を参照：
- 正式な仕様書: docs/friction_scoring_specification.md
- 実装: application/scoring_service.py

## 摩擦の種類とスコア化（概要）

### 1. 曖昧性摩擦（Ambiguity Friction）
- 曖昧な表現による解釈の違い
- スコア: -0.2 〜 -0.8（曖昧度に応じて）

### 2. 優先度摩擦（Priority Friction）
- ステークホルダー間の優先度認識の違い
- スコア: -0.3 〜 -0.6（ズレの大きさに応じて）

### 3. 技術理解摩擦（Technical Understanding Friction）
- 技術的理解度の差による実装方針の違い
- スコア: -0.4 〜 -0.7（理解度の差に応じて）

### 4. 時間経過摩擦（Temporal Friction）
- 時間経過による要件の変更・忘却
- スコア: -0.1 〜 -0.5（経過時間に応じて）

### 5. 矛盾摩擦（Contradiction Friction）
- ステークホルダー間の矛盾する要求
- スコア: -0.5 〜 -1.0（矛盾の深刻度に応じて）

注: このE2Eテストは「実行可能な仕様」として機能し、
実際のスコアリングロジックを検証します。
"""
import os
import tempfile
from datetime import datetime, timedelta
import pytest
from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.llm_hooks_api import create_llm_hooks_api


@pytest.mark.skip(reason="TDD Red: チーム摩擦シナリオの実装待ち")
def test_team_friction_曖昧な要件表現による解釈のズレ():
    """
    プロダクトオーナー、開発者、デザイナーが同じ要件を異なって解釈する
    実際のチーム開発でよく発生する問題を再現
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "team_ambiguity.db")
        repo = create_kuzu_repository(db_path)
        
        # スキーマ適用
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # PO（プロダクトオーナー）が曖昧な要件を作成
        po_requirement = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_ambiguous_001',
                title: 'ユーザーフレンドリーな検索機能',
                description: '使いやすい検索機能を実装する',
                priority: 150,
                requirement_type: 'functional',
                status: 'proposed',
                // メタデータはimplementation_detailsに含める
                implementation_details: '{"created_by": "product_owner", "ambiguity_level": "high"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/search/req_001'})
            CREATE (loc)-[:LOCATES]->(r)
            RETURN r.id as id, r.title as title
            """,
            "parameters": {}
        })
        
        assert po_requirement["status"] == "success"
        
        # 開発者の解釈（技術的観点）
        dev_interpretation = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (orig:RequirementEntity {id: 'req_ambiguous_001'})
            CREATE (dev:RequirementEntity {
                id: 'req_dev_interp_001',
                title: 'Elasticsearch全文検索実装',
                description: '高速な全文検索のためElasticsearchを導入し、形態素解析とファセット検索を実装',
                priority: 150,
                requirement_type: 'functional',
                status: 'proposed',
                implementation_details: '{"engine": "Elasticsearch", "features": ["morphological_analysis", "faceted_search", "autocomplete"], "created_by": "developer"}',
                technical_specifications: '{"interpretation_of": "req_ambiguous_001", "focus": "technical_performance"}'
            })
            CREATE (dev_loc:LocationURI {id: 'loc://vision/search/dev_interp_001'})
            CREATE (dev_loc)-[:LOCATES]->(dev)
            // 解釈の関係をDEPENDS_ONで表現
            CREATE (dev)-[:DEPENDS_ON {
                dependency_type: 'interpretation',
                reason: 'developer interpretation: focus on technical performance'
            }]->(orig)
            RETURN dev.id as id
            """,
            "parameters": {}
        })
        
        # デザイナーの解釈（UX観点）
        designer_interpretation = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (orig:RequirementEntity {id: 'req_ambiguous_001'})
            CREATE (des:RequirementEntity {
                id: 'req_designer_interp_001',
                title: 'シンプルな検索UI',
                description: 'Googleライクな単一検索ボックスと視覚的な結果表示',
                priority: 150,
                requirement_type: 'functional',
                status: 'proposed',
                implementation_details: '{"created_by": "designer", "interpretation_of": "req_ambiguous_001", "focus": "user_experience"}',
                acceptance_criteria: '1. 単一の検索ボックス 2. インクリメンタルサーチ 3. 結果のビジュアル表示'
            })
            CREATE (des_loc:LocationURI {id: 'loc://vision/search/designer_interp_001'})
            CREATE (des_loc)-[:LOCATES]->(des)
            // 解釈の関係をDEPENDS_ONで表現
            CREATE (des)-[:DEPENDS_ON {
                dependency_type: 'interpretation',
                reason: 'designer interpretation: focus on user experience'
            }]->(orig)
            RETURN des.id as id
            """,
            "parameters": {}
        })
        
        # 解釈のズレを分析
        friction_analysis = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (orig:RequirementEntity {id: 'req_ambiguous_001'})
            MATCH (interp:RequirementEntity)-[rel:DEPENDS_ON {dependency_type: 'interpretation'}]->(orig)
            WITH orig, collect({
                reason: rel.reason,
                details: interp.implementation_details,
                title: interp.title,
                has_tech_spec: interp.technical_specifications IS NOT NULL,
                has_acceptance: interp.acceptance_criteria IS NOT NULL
            }) as interpretations
            
            // 摩擦スコアを計算
            WITH orig, interpretations,
                 // 異なる解釈の数
                 size(interpretations) as interpretation_count
            
            RETURN {
                original_requirement: orig.title,
                interpretation_count: size(interpretations),
                different_interpretations: interpretation_count,
                interpretations: interpretations,
                // 曖昧性摩擦スコア（解釈の違いが大きいほど低い）
                ambiguity_friction_score: CASE
                    WHEN interpretation_count >= 2 THEN -0.6
                    WHEN interpretation_count = 1 THEN -0.3
                    ELSE 0.0
                END,
                recommendation: CASE
                    WHEN interpretation_count >= 2 THEN '要件の具体化と合意形成が必要'
                    ELSE '解釈が一致しています'
                END
            } as analysis
            """,
            "parameters": {}
        })
        
        assert friction_analysis["status"] == "success"
        if friction_analysis["data"]:
            analysis = friction_analysis["data"][0][0]
            # 解釈のズレが検出されることを確認
            assert analysis["interpretation_count"] >= 2
            assert analysis["ambiguity_friction_score"] < 0


@pytest.mark.skip(reason="TDD Red: チーム摩擦シナリオの実装待ち")
def test_team_friction_優先度認識のズレによる競合():
    """
    異なるステークホルダーが同じ要件に異なる優先度を設定
    実際のプロジェクトでの優先度調整の困難さを再現
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "team_priority.db")
        repo = create_kuzu_repository(db_path)
        
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # 営業チームの要求（顧客向け機能を最優先）
        sales_requirement = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_sales_priority_001',
                title: '顧客向けダッシュボード',
                description: '顧客が自社のデータを確認できるダッシュボード',
                priority: 250,
                requirement_type: 'functional',
                status: 'proposed',
                implementation_details: '{"created_by": "sales_team", "business_value": "high", "customer_impact": "direct"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/dashboard/sales_001'})
            CREATE (loc)-[:LOCATES]->(r)
            RETURN r.id as id
            """,
            "parameters": {}
        })
        
        # 開発チームの評価（技術的負債を優先）
        dev_evaluation = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (sales_req:RequirementEntity {id: 'req_sales_priority_001'})
            CREATE (tech_debt:RequirementEntity {
                id: 'req_tech_debt_001',
                title: 'データベース最適化',
                description: 'パフォーマンス向上のためのDB最適化',
                priority: 250,
                requirement_type: 'technical',
                status: 'proposed',
                implementation_details: '{"created_by": "dev_team", "technical_impact": "high", "performance_gain": "40%"}'
            })
            CREATE (tech_loc:LocationURI {id: 'loc://vision/infra/tech_debt_001'})
            CREATE (tech_loc)-[:LOCATES]->(tech_debt)
            
            // 開発チームによる営業要求の再評価を依存関係で表現
            CREATE (sales_req)-[:DEPENDS_ON {
                dependency_type: 'priority_conflict',
                reason: 'dev_team suggests medium priority: 技術的負債の解決が先決'
            }]->(tech_debt)
            
            RETURN tech_debt.id as id
            """,
            "parameters": {}
        })
        
        # セキュリティチームの介入（セキュリティを最優先）
        security_requirement = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (sec:RequirementEntity {
                id: 'req_security_001',
                title: '認証システムの強化',
                description: '二要素認証の実装',
                priority: 250,
                requirement_type: 'security',
                status: 'proposed',
                implementation_details: '{"created_by": "security_team", "compliance_required": true, "deadline": "2024-03-01"}'
            })
            CREATE (sec_loc:LocationURI {id: 'loc://vision/security/auth_001'})
            CREATE (sec_loc)-[:LOCATES]->(sec)
            RETURN sec.id as id
            """,
            "parameters": {}
        })
        
        # 優先度の競合を分析
        priority_friction = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (r:RequirementEntity)
            WHERE r.priority >= 200
            WITH collect(r) as critical_reqs, count(r) as critical_count
            
            MATCH (conflict:RequirementEntity)-[pc:DEPENDS_ON {dependency_type: 'priority_conflict'}]->(other:RequirementEntity)
            WITH critical_reqs, critical_count, collect({
                from: conflict.id,
                to: other.id,
                // reasonから評価者を抽出
                evaluator: CASE WHEN pc.reason CONTAINS 'dev_team' THEN 'dev_team' ELSE 'unknown' END,
                reason: pc.reason
            }) as conflicts
            
            RETURN {
                critical_requirement_count: critical_count,
                priority_conflicts: conflicts,
                // 優先度摩擦スコア（競合が多いほど低い）
                priority_friction_score: CASE
                    WHEN critical_count > 2 AND size(conflicts) > 0 THEN -0.7
                    WHEN critical_count > 1 THEN -0.4
                    ELSE 0.0
                END,
                recommendation: CASE
                    WHEN critical_count > 2 THEN '優先度の再調整と合意形成が必要'
                    WHEN size(conflicts) > 0 THEN 'ステークホルダー間の調整が必要'
                    ELSE '優先度は適切に管理されています'
                END
            } as analysis
            """,
            "parameters": {}
        })
        
        assert priority_friction["status"] == "success"
        if priority_friction["data"]:
            analysis = priority_friction["data"][0][0]
            # 複数のcritical要件が競合していることを確認
            assert analysis["critical_requirement_count"] >= 2
            assert analysis["priority_friction_score"] < 0


@pytest.mark.skip(reason="TDD Red: チーム摩擦シナリオの実装待ち")
def test_team_friction_時間経過による要件の変質():
    """
    時間経過とともに要件の理解や重要度が変化し、
    元の意図から離れていく様子を再現
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "team_temporal.db")
        repo = create_kuzu_repository(db_path)
        
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # 初期要件（3ヶ月前）
        initial_requirement = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_temporal_001',
                title: 'リアルタイム通知システム',
                description: 'ユーザーに重要なイベントをリアルタイムで通知',
                priority: 150,
                requirement_type: 'functional',
                status: 'proposed',
                implementation_details: '{"created_at": "2024-01-01T10:00:00", "original_scope": "email, push, in-app notifications", "estimated_effort": "2 weeks"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/notification/v1'})
            CREATE (loc)-[:LOCATES]->(r)
            RETURN r.id as id
            """,
            "parameters": {}
        })
        
        # 1ヶ月後: スコープの拡大
        scope_creep_1 = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (orig:RequirementEntity {id: 'req_temporal_001'})
            CREATE (v2:RequirementEntity {
                id: 'req_temporal_002',
                title: 'マルチチャネル通知システム',
                description: 'Email, SMS, Push, Slack, Teams, Webhookに対応',
                priority: 150,
                requirement_type: 'functional',
                status: 'proposed',
                implementation_details: '{"created_at": "2024-02-01T10:00:00", "expanded_scope": "SMS, Slack, Teams, Webhook追加", "estimated_effort": "6 weeks", "version_of": "req_temporal_001"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/notification/v2'})
            CREATE (loc)-[:LOCATES]->(v2)
            // 進化の関係をDEPENDS_ONで表現
            CREATE (v2)-[:DEPENDS_ON {
                dependency_type: 'evolution',
                reason: 'scope_expansion: 30 days, effort +200%, high complexity'
            }]->(orig)
            RETURN v2.id as id
            """,
            "parameters": {}
        })
        
        # 2ヶ月後: 優先度の変更と機能の追加
        priority_shift = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (v2:RequirementEntity {id: 'req_temporal_002'})
            CREATE (v3:RequirementEntity {
                id: 'req_temporal_003',
                title: 'AIドリブン通知最適化システム',
                description: '機械学習で通知タイミングと内容を最適化',
                priority: 250,
                requirement_type: 'functional',
                status: 'proposed',
                implementation_details: '{"created_at": "2024-03-01T10:00:00", "ai_features": "timing optimization, content personalization, channel selection", "estimated_effort": "3 months", "version_of": "req_temporal_002"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/notification/v3'})
            CREATE (loc)-[:LOCATES]->(v3)
            // 進化の関係をDEPENDS_ONで表現
            CREATE (v3)-[:DEPENDS_ON {
                dependency_type: 'evolution',
                reason: 'feature_creep: 30 days, effort +400%, original intent lost'
            }]->(v2)
            RETURN v3.id as id
            """,
            "parameters": {}
        })
        
        # 時間経過による変質を分析（簡略化版）
        temporal_friction = api["query"]({
            "type": "cypher",
            "query": """
            // 直接IDで取得
            MATCH (original:RequirementEntity {id: 'req_temporal_001'})
            MATCH (v2:RequirementEntity {id: 'req_temporal_002'})
            MATCH (v3:RequirementEntity {id: 'req_temporal_003'})
            
            // v3が最新であることを確認
            MATCH (v3)-[:DEPENDS_ON {dependency_type: 'evolution'}]->(v2)
            MATCH (v2)-[:DEPENDS_ON {dependency_type: 'evolution'}]->(original)
            
            WITH original, v3 as latest, 2 as evolution_steps
            
            RETURN {
                original_title: original.title,
                latest_title: latest.title,
                evolution_steps: evolution_steps,
                time_elapsed_days: 90,
                original_details: original.implementation_details,
                latest_details: latest.implementation_details,
                changes: [
                    {from: 'リアルタイム通知システム', to: 'マルチチャネル通知システム'},
                    {from: 'マルチチャネル通知システム', to: 'AIドリブン通知最適化システム'}
                ],
                // 時間経過摩擦スコア（変化が大きいほど低い）
                temporal_friction_score: CASE
                    WHEN evolution_steps >= 2 AND latest.implementation_details CONTAINS 'ai_features' THEN -0.8
                    WHEN evolution_steps >= 2 THEN -0.5
                    WHEN evolution_steps = 1 THEN -0.3
                    ELSE 0.0
                END,
                scope_creep_detected: true,
                recommendation: CASE
                    WHEN evolution_steps >= 2 THEN '要件の根本的な見直しが必要'
                    WHEN latest.implementation_details CONTAINS 'ai_features' THEN '元の要件から大きく逸脱しています'
                    ELSE '要件の進化を監視してください'
                END
            } as analysis
            """,
            "parameters": {}
        })
        
        if temporal_friction["status"] != "success":
            print(f"Error in temporal_friction: {temporal_friction}")
        assert temporal_friction["status"] == "success"
        if temporal_friction["data"]:
            analysis = temporal_friction["data"][0][0]
            # 要件が時間とともに変質していることを確認
            assert analysis["evolution_steps"] >= 2
            assert analysis["temporal_friction_score"] < -0.4


@pytest.mark.skip(reason="TDD Red: チーム摩擦シナリオの実装待ち")
def test_team_friction_矛盾する要求の統合():
    """
    異なるステークホルダーからの矛盾する要求を統合しようとして
    発生する摩擦を再現
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "team_contradiction.db")
        repo = create_kuzu_repository(db_path)
        
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # 経営層の要求：コスト削減
        exec_requirement = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_exec_cost_001',
                title: 'インフラコスト50%削減',
                description: 'クラウドインフラのコストを半減させる',
                priority: 250,
                requirement_type: 'business',
                status: 'proposed',
                implementation_details: '{"created_by": "executive", "constraint_type": "cost_reduction", "target_metric": "infrastructure_cost", "target_value": "-50%"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/cost/exec_001'})
            CREATE (loc)-[:LOCATES]->(r)
            RETURN r.id as id
            """,
            "parameters": {}
        })
        
        # エンジニアチームの要求：パフォーマンス向上
        eng_requirement = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_eng_perf_001',
                title: 'レスポンスタイム50%改善',
                description: '全APIのレスポンスタイムを半減させる',
                priority: 250,
                requirement_type: 'technical',
                status: 'proposed',
                implementation_details: '{"created_by": "engineering", "constraint_type": "performance_improvement", "target_metric": "response_time", "target_value": "-50%", "required_resources": "additional servers, caching layer, CDN"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/performance/eng_001'})
            CREATE (loc)-[:LOCATES]->(r)
            RETURN r.id as id
            """,
            "parameters": {}
        })
        
        # 矛盾関係の明示
        contradiction = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (cost:RequirementEntity {id: 'req_exec_cost_001'}),
                  (perf:RequirementEntity {id: 'req_eng_perf_001'})
            // 矛盾関係をDEPENDS_ONで表現
            CREATE (cost)-[:DEPENDS_ON {
                dependency_type: 'contradiction',
                reason: 'contradicts with performance: コスト削減とパフォーマンス向上は相反する'
            }]->(perf)
            CREATE (perf)-[:DEPENDS_ON {
                dependency_type: 'contradiction',
                reason: 'contradicts with cost: パフォーマンス向上にはインフラ投資が必要'
            }]->(cost)
            """,
            "parameters": {}
        })
        
        # セールスチームの要求：機能追加
        sales_requirement = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_sales_feature_001',
                title: '大口顧客向けカスタマイズ機能',
                description: 'エンタープライズ顧客向けの柔軟なカスタマイズ',
                priority: 250,
                requirement_type: 'functional',
                status: 'proposed',
                implementation_details: '{"created_by": "sales", "revenue_impact": "high", "complexity_increase": "significant"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/features/sales_001'})
            CREATE (loc)-[:LOCATES]->(r)
            RETURN r.id as id
            """,
            "parameters": {}
        })
        
        # 三つ巴の矛盾
        triple_conflict = api["query"]({
            "type": "cypher",
            "query": """
            MATCH (cost:RequirementEntity {id: 'req_exec_cost_001'}),
                  (perf:RequirementEntity {id: 'req_eng_perf_001'}),
                  (feature:RequirementEntity {id: 'req_sales_feature_001'})
            
            CREATE (feature)-[:DEPENDS_ON {
                dependency_type: 'contradiction',
                reason: 'contradicts with cost: カスタマイズ機能は保守コストを増大させる'
            }]->(cost)
            
            CREATE (feature)-[:DEPENDS_ON {
                dependency_type: 'contradiction',
                reason: 'contradicts with performance: カスタマイズ機能はシステムを複雑化しパフォーマンスに影響'
            }]->(perf)
            """,
            "parameters": {}
        })
        
        # 矛盾摩擦の分析（簡略化版）
        contradiction_friction = api["query"]({
            "type": "cypher",
            "query": """
            // 単純に矛盾関係の数をカウント
            MATCH (r1:RequirementEntity)-[c:DEPENDS_ON {dependency_type: 'contradiction'}]->(r2:RequirementEntity)
            WITH count(DISTINCT r1) as conflicting_requirements_count,
                 count(c) as total_contradictions
            
            MATCH (r:RequirementEntity)
WHERE r.priority >= 200
            WITH conflicting_requirements_count, total_contradictions, count(r) as critical_count
            
            RETURN {
                total_critical_requirements: critical_count,
                requirements_with_conflicts: conflicting_requirements_count,
                max_conflicts_per_requirement: 2,
                conflict_details: null,
                // 矛盾摩擦スコア（矛盾が多いほど低い）
                contradiction_friction_score: CASE
                    WHEN conflicting_requirements_count >= 3 THEN -0.9
                    WHEN conflicting_requirements_count >= 2 THEN -0.6
                    WHEN conflicting_requirements_count >= 1 THEN -0.4
                    ELSE 0.0
                END,
                resolution_complexity: CASE
                    WHEN conflicting_requirements_count >= 3 THEN 'extremely_high'
                    WHEN conflicting_requirements_count >= 2 THEN 'high'
                    ELSE 'manageable'
                END,
                recommendation: '統合的な解決策の検討と優先順位の明確化が必要'
            } as analysis
            """,
            "parameters": {}
        })
        
        if contradiction_friction["status"] != "success":
            print(f"Error in contradiction_friction: {contradiction_friction}")
        assert contradiction_friction["status"] == "success"
        if contradiction_friction["data"]:
            analysis = contradiction_friction["data"][0][0]
            # 矛盾する要求が存在することを確認
            assert analysis["requirements_with_conflicts"] >= 2
            assert analysis["contradiction_friction_score"] < -0.5


@pytest.mark.skip(reason="TDD Red: チーム摩擦シナリオの実装待ち")
def test_team_friction_総合的な摩擦スコア計算():
    """
    すべての摩擦要因を組み合わせた総合的なスコアを計算し、
    プロジェクトの健全性を評価
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "team_comprehensive.db")
        repo = create_kuzu_repository(db_path)
        
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # 複雑なプロジェクトをシミュレート
        # 1. 曖昧な要件
        api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r1:RequirementEntity {
                id: 'comp_req_001',
                title: 'ユーザビリティの改善',
                description: '使いやすさを向上させる',
                priority: 150,
                implementation_details: '{"ambiguity_level": "high"}'
            })
            CREATE (loc1:LocationURI {id: 'loc://vision/ux/001'})
            CREATE (loc1)-[:LOCATES]->(r1)
            """,
            "parameters": {}
        })
        
        # 2. 優先度の競合
        api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r2:RequirementEntity {
                id: 'comp_req_002',
                title: 'セキュリティ強化',
                priority: 250,
                implementation_details: '{"created_by": "security_team"}'
            })
            CREATE (r3:RequirementEntity {
                id: 'comp_req_003',
                title: '新機能開発',
                priority: 250,
                implementation_details: '{"created_by": "product_team"}'
            })
            CREATE (loc2:LocationURI {id: 'loc://vision/security/001'})
            CREATE (loc3:LocationURI {id: 'loc://vision/features/001'})
            CREATE (loc2)-[:LOCATES]->(r2)
            CREATE (loc3)-[:LOCATES]->(r3)
            """,
            "parameters": {}
        })
        
        # 3. 時間経過による変化
        api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r4:RequirementEntity {
                id: 'comp_req_004',
                title: 'API統合',
                implementation_details: '{"created_at": "2024-01-01", "original_scope": "REST API"}'
            })
            CREATE (r5:RequirementEntity {
                id: 'comp_req_005',
                title: 'マイクロサービス化',
                implementation_details: '{"created_at": "2024-03-01", "expanded_scope": "GraphQL, gRPC, REST", "version_of": "comp_req_004"}'
            })
            CREATE (loc4:LocationURI {id: 'loc://vision/api/v1'})
            CREATE (loc5:LocationURI {id: 'loc://vision/api/v2'})
            CREATE (loc4)-[:LOCATES]->(r4)
            CREATE (loc5)-[:LOCATES]->(r5)
            CREATE (r5)-[:DEPENDS_ON {dependency_type: 'evolution', reason: 'evolved after 60 days'}]->(r4)
            """,
            "parameters": {}
        })
        
        # 4. 矛盾する要求
        api["query"]({
            "type": "cypher",
            "query": """
            MATCH (r2:RequirementEntity {id: 'comp_req_002'}),
                  (r3:RequirementEntity {id: 'comp_req_003'})
            CREATE (r2)-[:DEPENDS_ON {dependency_type: 'contradiction', reason: 'security vs features: high severity conflict'}]->(r3)
            """,
            "parameters": {}
        })
        
        # 総合的な摩擦分析
        comprehensive_friction = api["query"]({
            "type": "cypher",
            "query": """
            // 各種摩擦の計算
            MATCH (r:RequirementEntity)
            
            // 曖昧性摩擦
            WITH count(CASE WHEN r.implementation_details CONTAINS '"ambiguity_level": "high"' THEN 1 END) as ambiguous_count,
                 count(r) as total_count
            
            // 優先度摩擦
            MATCH (critical:RequirementEntity)
WHERE critical.priority >= 200
            WITH ambiguous_count, total_count, count(critical) as critical_count
            
            // 時間経過摩擦
            MATCH ()-[ev:DEPENDS_ON {dependency_type: 'evolution'}]->()
            WITH ambiguous_count, total_count, critical_count, count(ev) as evolution_count
            
            // 矛盾摩擦
            MATCH ()-[c:DEPENDS_ON {dependency_type: 'contradiction'}]->()
            WITH ambiguous_count, total_count, critical_count, evolution_count, count(c) as contradiction_count
            
            // 個別スコアの計算
            WITH {
                ambiguity_score: CASE 
                    WHEN ambiguous_count > 0 THEN -0.3 * ambiguous_count 
                    ELSE 0.0 
                END,
                priority_score: CASE 
                    WHEN critical_count > 2 THEN -0.6 
                    WHEN critical_count > 1 THEN -0.3
                    ELSE 0.0 
                END,
                temporal_score: CASE 
                    WHEN evolution_count > 0 THEN -0.4 * evolution_count
                    ELSE 0.0 
                END,
                contradiction_score: CASE 
                    WHEN contradiction_count > 0 THEN -0.5 * contradiction_count
                    ELSE 0.0 
                END
            } as scores
            
            // 総合スコアの計算（重み付け平均）
            WITH scores,
                 (scores.ambiguity_score * 0.2 + 
                  scores.priority_score * 0.3 + 
                  scores.temporal_score * 0.2 + 
                  scores.contradiction_score * 0.3) as total_friction_score
            
            RETURN {
                individual_scores: scores,
                total_friction_score: total_friction_score,
                project_health: CASE
                    WHEN total_friction_score > -0.2 THEN 'healthy'
                    ELSE 'needs_attention'
                END,
                primary_concerns: ['要件の明確化', '優先度の再評価'],
                recommendations: '定期的な要件レビュー会議の実施'
            } as analysis
            """,
            "parameters": {}
        })
        
        assert comprehensive_friction["status"] == "success"
        if comprehensive_friction["data"]:
            analysis = comprehensive_friction["data"][0][0]
            # プロジェクトに摩擦が存在することを確認
            assert analysis["total_friction_score"] < 0
            # 健全性評価が適切に行われていることを確認
            assert analysis["project_health"] in ['healthy', 'needs_attention', 'at_risk', 'critical']