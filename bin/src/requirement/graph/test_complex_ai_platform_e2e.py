"""
複雑なAIプラットフォーム要件のE2Eテスト

オーナーとマネージャーが協力して、AIアシスタント統合プラットフォームの
要件を構築する複雑なシナリオのテスト。
"""
import json
import subprocess
import os
import pytest
import time


class TestComplexAIPlatformE2E:
    """AIプラットフォーム要件の複雑なE2Eテスト"""
    
    def setup_method(self):
        """各テストの前に環境を準備"""
        self.env = os.environ.copy()
        self.env['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'
        self.env['RGL_SKIP_SCHEMA_CHECK'] = 'true'
        
        # タイムスタンプを使ってユニークなIDを生成
        self.timestamp = str(int(time.time() * 1000))
        
        # スキーマを初期化
        self._init_schema()
    
    def _init_schema(self):
        """スキーマを初期化"""
        result = subprocess.run(
            ['nix', 'run', '.#init'],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode != 0:
            print(f"Schema initialization failed: {result.stderr}")
            raise RuntimeError("Failed to initialize schema")
    
    def run_query(self, query: str) -> dict:
        """Cypherクエリを実行してレスポンスを取得"""
        input_data = json.dumps({
            "type": "cypher",
            "query": query
        })
        
        result = subprocess.run(
            ['nix', 'run', '.#run'],
            input=input_data,
            capture_output=True,
            text=True,
            env=self.env,
            cwd=os.path.dirname(__file__)
        )
        
        # JSONL形式のレスポンスをパース
        lines = result.stdout.strip().split('\n')
        responses = []
        for line in lines:
            if line:
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "responses": responses,
            "stderr": result.stderr
        }
    
    def test_ai_platform_requirements_construction(self):
        """AIプラットフォーム要件の構築テスト"""
        print("\n=== AIアシスタント統合プラットフォーム要件構築 ===")
        
        # 1. オーナー: メインプラットフォーム要件
        print("\n[オーナー] プラットフォーム基本要件を登録")
        platform_query = f"""
        CREATE (platform:RequirementEntity {{
            id: 'AI_PLATFORM_{self.timestamp}',
            title: 'AIアシスタント統合プラットフォーム',
            description: '複数のAIモデルを統合し、企業向けに提供するプラットフォーム',
            priority: 250,
            status: 'approved',
            requirement_type: 'business'
        }})
        """
        result = self.run_query(platform_query)
        assert result["status"] == "success"
        
        # 2. マネージャー: 技術アーキテクチャ要件
        print("\n[マネージャー] 技術アーキテクチャ要件を追加")
        arch_query = f"""
        CREATE (arch:RequirementEntity {{
            id: 'AI_ARCH_{self.timestamp}',
            title: 'マイクロサービスアーキテクチャ',
            description: '各AIモデルを独立したサービスとして実装し、API Gateway経由で統合',
            priority: 230,
            status: 'proposed',
            requirement_type: 'technical',
            technical_specifications: '{{"architecture": "microservices", "api_style": "REST/GraphQL", "container": "Docker/K8s"}}'
        }})
        CREATE (gateway:RequirementEntity {{
            id: 'AI_GATEWAY_{self.timestamp}',
            title: '統合APIゲートウェイ',
            description: 'すべてのAIサービスへの単一エントリーポイント',
            priority: 220,
            status: 'proposed',
            requirement_type: 'technical'
        }})
        """
        result = self.run_query(arch_query)
        assert result["status"] == "success"
        
        # 3. 依存関係設定
        print("\n[依存関係] Gateway → Architecture → Platform")
        dep_query = f"""
        MATCH (arch:RequirementEntity {{id: 'AI_ARCH_{self.timestamp}'}}),
              (platform:RequirementEntity {{id: 'AI_PLATFORM_{self.timestamp}'}})
        CREATE (arch)-[:DEPENDS_ON]->(platform)
        WITH arch, platform
        MATCH (gateway:RequirementEntity {{id: 'AI_GATEWAY_{self.timestamp}'}})
        CREATE (gateway)-[:DEPENDS_ON]->(arch)
        """
        result = self.run_query(dep_query)
        assert result["status"] == "success"
        
        # 4. オーナー: AI機能要件
        print("\n[オーナー] 具体的なAI機能要件を追加")
        ai_features_query = f"""
        CREATE (llm:RequirementEntity {{
            id: 'AI_LLM_{self.timestamp}',
            title: '大規模言語モデル統合',
            description: 'GPT-4, Claude, Geminiなど複数のLLMを統合',
            priority: 200,
            status: 'approved',
            requirement_type: 'functional',
            technical_specifications: '{{"models": ["GPT-4", "Claude-3", "Gemini-Pro"], "rate_limit": "1000req/min"}}'
        }})
        CREATE (vision:RequirementEntity {{
            id: 'AI_VISION_{self.timestamp}',
            title: '画像認識AI統合',
            description: 'Vision API, DALL-E, Stable Diffusionの統合',
            priority: 180,
            status: 'proposed',
            requirement_type: 'functional'
        }})
        CREATE (voice:RequirementEntity {{
            id: 'AI_VOICE_{self.timestamp}',
            title: '音声認識・合成AI統合',
            description: 'Whisper, ElevenLabsなど音声AIの統合',
            priority: 170,
            status: 'proposed',
            requirement_type: 'functional'
        }})
        """
        result = self.run_query(ai_features_query)
        assert result["status"] == "success"
        
        # 5. マネージャー: インフラ要件
        print("\n[マネージャー] インフラストラクチャ要件を追加")
        infra_query = f"""
        CREATE (cache:RequirementEntity {{
            id: 'AI_CACHE_{self.timestamp}',
            title: 'レスポンスキャッシュシステム',
            description: 'AIレスポンスの高速化のためのRedisベースキャッシュ',
            priority: 190,
            status: 'proposed',
            requirement_type: 'technical',
            acceptance_criteria: '1. キャッシュヒット率80%以上\\n2. TTL設定可能\\n3. LRU eviction policy'
        }})
        CREATE (monitor:RequirementEntity {{
            id: 'AI_MONITOR_{self.timestamp}',
            title: 'AIモデル監視システム',
            description: '各AIモデルの性能、コスト、エラー率を監視',
            priority: 195,
            status: 'approved',
            requirement_type: 'operational'
        }})
        """
        result = self.run_query(infra_query)
        assert result["status"] == "success"
        
        # 6. AI機能の依存関係
        print("\n[依存関係] AI機能 → Gateway")
        ai_dep_query = f"""
        MATCH (llm:RequirementEntity {{id: 'AI_LLM_{self.timestamp}'}}),
              (gateway:RequirementEntity {{id: 'AI_GATEWAY_{self.timestamp}'}})
        CREATE (llm)-[:DEPENDS_ON]->(gateway)
        WITH llm, gateway
        MATCH (vision:RequirementEntity {{id: 'AI_VISION_{self.timestamp}'}})
        CREATE (vision)-[:DEPENDS_ON]->(gateway)
        WITH vision, gateway
        MATCH (voice:RequirementEntity {{id: 'AI_VOICE_{self.timestamp}'}})
        CREATE (voice)-[:DEPENDS_ON]->(gateway)
        """
        result = self.run_query(ai_dep_query)
        assert result["status"] == "success"
        
        # 7. オーナー: セキュリティ要件
        print("\n[オーナー] エンタープライズセキュリティ要件を追加")
        security_query = f"""
        CREATE (security:RequirementEntity {{
            id: 'AI_SECURITY_{self.timestamp}',
            title: 'エンタープライズセキュリティ',
            description: 'SOC2準拠、データ暗号化、アクセス制御',
            priority: 240,
            status: 'approved',
            requirement_type: 'security',
            verification_required: true,
            acceptance_criteria: '1. SOC2 Type II認証取得\\n2. AES-256暗号化\\n3. OAuth2.0/SAML認証\\n4. 監査ログ完備'
        }})
        """
        result = self.run_query(security_query)
        assert result["status"] == "success"
        
        # 8. セキュリティ依存関係
        print("\n[依存関係] Security → Platform, Others → Security")
        sec_dep_query = f"""
        MATCH (security:RequirementEntity {{id: 'AI_SECURITY_{self.timestamp}'}}),
              (platform:RequirementEntity {{id: 'AI_PLATFORM_{self.timestamp}'}})
        CREATE (security)-[:DEPENDS_ON]->(platform)
        WITH security
        MATCH (gateway:RequirementEntity {{id: 'AI_GATEWAY_{self.timestamp}'}})
        CREATE (gateway)-[:DEPENDS_ON]->(security)
        WITH security
        MATCH (cache:RequirementEntity {{id: 'AI_CACHE_{self.timestamp}'}})
        CREATE (cache)-[:DEPENDS_ON]->(security)
        """
        result = self.run_query(sec_dep_query)
        assert result["status"] == "success"
        
        # 9. マネージャー: コスト管理要件
        print("\n[マネージャー] コスト最適化要件を追加")
        cost_query = f"""
        CREATE (cost:RequirementEntity {{
            id: 'AI_COST_{self.timestamp}',
            title: 'AIコスト最適化システム',
            description: '各AIモデルの利用コストを監視し、予算内で最適配分',
            priority: 210,
            status: 'proposed',
            requirement_type: 'operational',
            implementation_details: '{{"budget_limit": "$50000/month", "cost_allocation": {{"GPT-4": 40, "Claude": 30, "Others": 30}}, "alert_threshold": 80}}'
        }})
        """
        result = self.run_query(cost_query)
        assert result["status"] == "success"
        
        print("\n✅ すべての要件が正常に登録されました")
    
    def test_requirements_review_queries(self):
        """要件レビュー用のクエリテスト"""
        # 前提: 要件が既に登録されている
        self._setup_test_requirements()
        
        print("\n=== 要件レビュークエリ ===")
        
        # 1. 全要件の一覧
        print("\n[1] AIプラットフォーム要件一覧（優先度順）")
        list_query = f"""
        MATCH (r:RequirementEntity)
        WHERE r.id STARTS WITH 'AI_' AND r.id CONTAINS '{self.timestamp}'
        RETURN r.id, r.title, r.priority, r.status, r.requirement_type
        ORDER BY r.priority DESC
        """
        result = self.run_query(list_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                print("\n優先度 | ID | タイトル | ステータス | タイプ")
                print("-" * 80)
                for row in result_line["data"]:
                    print(f"{row[2]:3d} | {row[0]:20s} | {row[1]:30s} | {row[3]:10s} | {row[4]}")
        
        # 2. 依存関係の確認
        print("\n[2] 依存関係グラフ")
        dep_query = f"""
        MATCH (a:RequirementEntity)-[:DEPENDS_ON]->(b:RequirementEntity)
        WHERE a.id STARTS WITH 'AI_' AND a.id CONTAINS '{self.timestamp}'
        RETURN a.title, b.title
        ORDER BY a.priority DESC
        """
        result = self.run_query(dep_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                print("\n依存元 → 依存先")
                print("-" * 60)
                for row in result_line["data"]:
                    print(f"{row[0]:30s} → {row[1]}")
        
        # 3. 承認済み要件
        print("\n[3] 承認済み要件のみ")
        approved_query = f"""
        MATCH (r:RequirementEntity)
        WHERE r.status = 'approved' AND r.id STARTS WITH 'AI_' AND r.id CONTAINS '{self.timestamp}'
        RETURN r.title, r.priority, r.requirement_type
        ORDER BY r.priority DESC
        """
        result = self.run_query(approved_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                print("\n承認済み要件:")
                for row in result_line["data"]:
                    print(f"- {row[0]} (優先度: {row[1]}, タイプ: {row[2]})")
        
        # 4. 技術仕様の確認
        print("\n[4] 技術仕様が定義されている要件")
        tech_spec_query = f"""
        MATCH (r:RequirementEntity)
        WHERE r.technical_specifications IS NOT NULL 
          AND r.id STARTS WITH 'AI_' 
          AND r.id CONTAINS '{self.timestamp}'
        RETURN r.title, r.technical_specifications
        """
        result = self.run_query(tech_spec_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                print("\n技術仕様:")
                for row in result_line["data"]:
                    print(f"\n要件: {row[0]}")
                    try:
                        specs = json.loads(row[1])
                        for key, value in specs.items():
                            print(f"  - {key}: {value}")
                    except:
                        print(f"  仕様: {row[1]}")
        
        # 5. 受け入れ条件の確認
        print("\n[5] 受け入れ条件が定義されている要件")
        acceptance_query = f"""
        MATCH (r:RequirementEntity)
        WHERE r.acceptance_criteria IS NOT NULL 
          AND r.id STARTS WITH 'AI_' 
          AND r.id CONTAINS '{self.timestamp}'
        RETURN r.title, r.acceptance_criteria
        """
        result = self.run_query(acceptance_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                print("\n受け入れ条件:")
                for row in result_line["data"]:
                    print(f"\n要件: {row[0]}")
                    criteria = row[1].replace('\\n', '\n')
                    for line in criteria.split('\n'):
                        print(f"  {line}")
    
    def test_traceability_documentation(self):
        """トレーサビリティドキュメントの生成テスト"""
        # 前提: 要件が既に登録されている
        self._setup_test_requirements()
        
        print("\n=== トレーサビリティドキュメント ===")
        
        # 1. 要件階層の可視化
        print("\n[要件階層構造]")
        hierarchy_query = f"""
        MATCH (r:RequirementEntity)
        WHERE r.id STARTS WITH 'AI_' AND r.id CONTAINS '{self.timestamp}'
        OPTIONAL MATCH (r)-[:DEPENDS_ON]->(parent:RequirementEntity)
        RETURN r.id, r.title, r.priority, parent.id, parent.title
        ORDER BY r.priority DESC
        """
        result = self.run_query(hierarchy_query)
        
        requirements = {}
        dependencies = []
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                for row in result_line["data"]:
                    req_id = row[0]
                    requirements[req_id] = {
                        "title": row[1],
                        "priority": row[2],
                        "depends_on": []
                    }
                    if row[3]:  # 親が存在する場合
                        requirements[req_id]["depends_on"].append(row[3])
                        dependencies.append((req_id, row[3]))
        
        # 2. トレーサビリティマトリックス
        print("\n[トレーサビリティマトリックス]")
        print("\nビジネス要件からの追跡:")
        
        # ビジネス要件を起点とした前方追跡
        forward_trace_query = f"""
        MATCH (business:RequirementEntity {{requirement_type: 'business'}})
        WHERE business.id STARTS WITH 'AI_' AND business.id CONTAINS '{self.timestamp}'
        OPTIONAL MATCH path = (req:RequirementEntity)-[:DEPENDS_ON*]->(business)
        WHERE req.id STARTS WITH 'AI_' AND req.id CONTAINS '{self.timestamp}'
        RETURN business.title, collect(DISTINCT req.title) as dependent_requirements
        """
        result = self.run_query(forward_trace_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                for row in result_line["data"]:
                    print(f"\n{row[0]}:")
                    if row[1]:
                        for dep in row[1]:
                            print(f"  ← {dep}")
        
        # 3. 実装状況サマリー
        print("\n[実装状況サマリー]")
        status_summary_query = f"""
        MATCH (r:RequirementEntity)
        WHERE r.id STARTS WITH 'AI_' AND r.id CONTAINS '{self.timestamp}'
        RETURN r.status, count(*) as count, collect(r.title) as requirements
        ORDER BY count DESC
        """
        result = self.run_query(status_summary_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                total = sum(row[1] for row in result_line["data"])
                print(f"\n総要件数: {total}")
                print("\nステータス別内訳:")
                for row in result_line["data"]:
                    percentage = (row[1] / total * 100) if total > 0 else 0
                    print(f"  {row[0]:10s}: {row[1]:2d}件 ({percentage:5.1f}%)")
                    for req in row[2][:3]:  # 最初の3件のみ表示
                        print(f"    - {req}")
                    if len(row[2]) > 3:
                        print(f"    ... 他 {len(row[2]) - 3}件")
        
        # 4. 検証要件の確認
        print("\n[検証が必要な要件]")
        verification_query = f"""
        MATCH (r:RequirementEntity)
        WHERE r.verification_required = true 
          AND r.id STARTS WITH 'AI_' 
          AND r.id CONTAINS '{self.timestamp}'
        RETURN r.title, r.requirement_type, r.acceptance_criteria
        """
        result = self.run_query(verification_query)
        
        if result["status"] == "success":
            result_line = next((r for r in result["responses"] if r.get("type") == "result"), None)
            if result_line and result_line["data"]:
                for row in result_line["data"]:
                    print(f"\n要件: {row[0]} ({row[1]})")
                    if row[2]:
                        print("受け入れ条件:")
                        criteria = row[2].replace('\\n', '\n')
                        for line in criteria.split('\n'):
                            print(f"  {line}")
    
    def _setup_test_requirements(self):
        """テスト用の要件をセットアップ（簡易版）"""
        # 基本的な要件だけ作成
        queries = [
            f"""CREATE (p:RequirementEntity {{id: 'AI_PLATFORM_{self.timestamp}', title: 'AIプラットフォーム', priority: 250, status: 'approved', requirement_type: 'business'}})""",
            f"""CREATE (s:RequirementEntity {{id: 'AI_SECURITY_{self.timestamp}', title: 'セキュリティ', priority: 240, status: 'approved', requirement_type: 'security', verification_required: true, acceptance_criteria: '1. SOC2準拠\\n2. 暗号化'}})""",
            f"""CREATE (g:RequirementEntity {{id: 'AI_GATEWAY_{self.timestamp}', title: 'APIゲートウェイ', priority: 220, status: 'proposed', requirement_type: 'technical'}})""",
            f"""CREATE (c:RequirementEntity {{id: 'AI_CACHE_{self.timestamp}', title: 'キャッシュ', priority: 190, status: 'proposed', requirement_type: 'technical', acceptance_criteria: '1. ヒット率80%\\n2. TTL設定'}})""",
            f"""CREATE (l:RequirementEntity {{id: 'AI_LLM_{self.timestamp}', title: 'LLM統合', priority: 200, status: 'approved', requirement_type: 'functional', technical_specifications: '{{"models": ["GPT-4", "Claude"]}}'}}""",
        ]
        
        for query in queries:
            self.run_query(query)
        
        # 依存関係
        dep_queries = [
            f"""MATCH (s:RequirementEntity {{id: 'AI_SECURITY_{self.timestamp}'}}), (p:RequirementEntity {{id: 'AI_PLATFORM_{self.timestamp}'}}) CREATE (s)-[:DEPENDS_ON]->(p)""",
            f"""MATCH (g:RequirementEntity {{id: 'AI_GATEWAY_{self.timestamp}'}}), (s:RequirementEntity {{id: 'AI_SECURITY_{self.timestamp}'}}) CREATE (g)-[:DEPENDS_ON]->(s)""",
            f"""MATCH (l:RequirementEntity {{id: 'AI_LLM_{self.timestamp}'}}), (g:RequirementEntity {{id: 'AI_GATEWAY_{self.timestamp}'}}) CREATE (l)-[:DEPENDS_ON]->(g)""",
        ]
        
        for query in dep_queries:
            self.run_query(query)


if __name__ == "__main__":
    # 直接実行してレビューを確認
    test = TestComplexAIPlatformE2E()
    test.setup_method()
    
    print("=== AIプラットフォーム要件構築E2Eテスト ===")
    print("登場人物:")
    print("- オーナー: ビジネス要件と優先順位を決定")
    print("- マネージャー: 技術要件と実装詳細を定義")
    print("")
    
    # 要件構築
    test.test_ai_platform_requirements_construction()
    
    # レビュークエリ
    print("\n" + "="*80)
    test.test_requirements_review_queries()
    
    # トレーサビリティ
    print("\n" + "="*80)
    test.test_traceability_documentation()