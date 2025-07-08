# RGL テストパターン集

このドキュメントは、RGLシステムの様々な利用シナリオとレビューパターンを記載しています。
インタラクティブにクエリを実行して、要件の状態を確認・レビューすることができます。

## 1. 初めてのユーザーシナリオ

### 基本的な要件登録
```bash
# ECサイトの基本要件を登録
echo '{"type": "cypher", "query": "CREATE (r:RequirementEntity {id: \"EC_SITE_001\", title: \"ECサイト構築\", description: \"新規ECサイトの構築\", priority: 200, status: \"approved\"})" }' | nix run .#run

# 技術要件を追加
echo '{"type": "cypher", "query": "CREATE (r:RequirementEntity {id: \"AUTH_001\", title: \"認証システム\", description: \"OAuth2.0ベースの認証\", priority: 180, requirement_type: \"technical\"})" }' | nix run .#run

# 依存関係を設定
echo '{"type": "cypher", "query": "MATCH (a:RequirementEntity {id: \"AUTH_001\"}), (b:RequirementEntity {id: \"EC_SITE_001\"}) CREATE (a)-[:DEPENDS_ON]->(b)" }' | nix run .#run
```

### よくある間違いと学習
```bash
# 循環依存の検出（エラーになることを確認）
echo '{"type": "cypher", "query": "MATCH (a:RequirementEntity {id: \"EC_SITE_001\"}), (b:RequirementEntity {id: \"AUTH_001\"}) CREATE (a)-[:DEPENDS_ON]->(b)" }' | nix run .#run

# 曖昧な要件（低スコアになることを確認）
echo '{"type": "cypher", "query": "CREATE (r:RequirementEntity {id: \"UI_001\", title: \"使いやすいUI\", description: \"ユーザーフレンドリーなインターフェース\"})" }' | nix run .#run
```

## 2. 複雑なプロジェクトシナリオ（AIプラットフォーム）

### 役割別の要件追加パターン

#### オーナー視点（ビジネス要件）
```bash
# プラットフォーム基本要件
echo '{"type": "cypher", "query": "CREATE (platform:RequirementEntity {id: \"AI_PLATFORM_001\", title: \"AIアシスタント統合プラットフォーム\", description: \"複数のAIモデルを統合し、企業向けに提供するプラットフォーム\", priority: 250, status: \"approved\", requirement_type: \"business\"})" }' | nix run .#run

# セキュリティ要件（最重要）
echo '{"type": "cypher", "query": "CREATE (security:RequirementEntity {id: \"AI_SECURITY_001\", title: \"エンタープライズセキュリティ\", description: \"SOC2準拠、データ暗号化、アクセス制御\", priority: 240, status: \"approved\", requirement_type: \"security\", verification_required: true, acceptance_criteria: \"1. SOC2 Type II認証取得\\n2. AES-256暗号化\\n3. OAuth2.0/SAML認証\\n4. 監査ログ完備\"})" }' | nix run .#run

# AI機能要件
echo '{"type": "cypher", "query": "CREATE (llm:RequirementEntity {id: \"AI_LLM_001\", title: \"大規模言語モデル統合\", description: \"GPT-4, Claude, Geminiなど複数のLLMを統合\", priority: 200, status: \"approved\", requirement_type: \"functional\", technical_specifications: \"{\\\"models\\\": [\\\"GPT-4\\\", \\\"Claude-3\\\", \\\"Gemini-Pro\\\"], \\\"rate_limit\\\": \\\"1000req/min\\\"}\"}) CREATE (vision:RequirementEntity {id: \"AI_VISION_001\", title: \"画像認識AI統合\", description: \"Vision API, DALL-E, Stable Diffusionの統合\", priority: 180, status: \"proposed\", requirement_type: \"functional\"})" }' | nix run .#run
```

#### マネージャー視点（技術・運用要件）
```bash
# アーキテクチャ要件
echo '{"type": "cypher", "query": "CREATE (arch:RequirementEntity {id: \"AI_ARCH_001\", title: \"マイクロサービスアーキテクチャ\", description: \"各AIモデルを独立したサービスとして実装\", priority: 230, status: \"proposed\", requirement_type: \"technical\", technical_specifications: \"{\\\"architecture\\\": \\\"microservices\\\", \\\"api_style\\\": \\\"REST/GraphQL\\\", \\\"container\\\": \\\"Docker/K8s\\\"}\"}) CREATE (gateway:RequirementEntity {id: \"AI_GATEWAY_001\", title: \"統合APIゲートウェイ\", description: \"すべてのAIサービスへの単一エントリーポイント\", priority: 220, status: \"proposed\", requirement_type: \"technical\"})" }' | nix run .#run

# インフラ要件
echo '{"type": "cypher", "query": "CREATE (cache:RequirementEntity {id: \"AI_CACHE_001\", title: \"レスポンスキャッシュシステム\", description: \"AIレスポンスの高速化のためのRedisベースキャッシュ\", priority: 190, status: \"proposed\", requirement_type: \"technical\", acceptance_criteria: \"1. キャッシュヒット率80%以上\\n2. TTL設定可能\\n3. LRU eviction policy\"})" }' | nix run .#run

# コスト管理要件
echo '{"type": "cypher", "query": "CREATE (cost:RequirementEntity {id: \"AI_COST_001\", title: \"AIコスト最適化システム\", description: \"各AIモデルの利用コストを監視し、予算内で最適配分\", priority: 210, status: \"proposed\", requirement_type: \"operational\", implementation_details: \"{\\\"budget_limit\\\": \\\"$50000/month\\\", \\\"cost_allocation\\\": {\\\"GPT-4\\\": 40, \\\"Claude\\\": 30, \\\"Others\\\": 30}, \\\"alert_threshold\\\": 80}\"}" }' | nix run .#run
```

### 複雑な依存関係の設定
```bash
# セキュリティを中心とした依存関係
echo '{"type": "cypher", "query": "MATCH (security:RequirementEntity {id: \"AI_SECURITY_001\"}), (platform:RequirementEntity {id: \"AI_PLATFORM_001\"}) CREATE (security)-[:DEPENDS_ON]->(platform) WITH security MATCH (gateway:RequirementEntity {id: \"AI_GATEWAY_001\"}) CREATE (gateway)-[:DEPENDS_ON]->(security)" }' | nix run .#run

# 機能要件の依存関係
echo '{"type": "cypher", "query": "MATCH (llm:RequirementEntity {id: \"AI_LLM_001\"}), (gateway:RequirementEntity {id: \"AI_GATEWAY_001\"}) CREATE (llm)-[:DEPENDS_ON]->(gateway)" }' | nix run .#run
```

## 3. レビュークエリパターン

### 要件一覧の確認
```bash
# 優先度順で全要件を表示
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.id STARTS WITH \"AI_\" RETURN r.id, r.title, r.priority, r.status, r.requirement_type ORDER BY r.priority DESC" }' | nix run .#run

# 承認済み要件のみ
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.status = \"approved\" AND r.id STARTS WITH \"AI_\" RETURN r.title, r.priority, r.requirement_type ORDER BY r.priority DESC" }' | nix run .#run

# タイプ別集計
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.id STARTS WITH \"AI_\" RETURN r.requirement_type, count(*) as count, collect(r.title) ORDER BY count DESC" }' | nix run .#run
```

### 依存関係の可視化
```bash
# 直接の依存関係
echo '{"type": "cypher", "query": "MATCH (a:RequirementEntity)-[:DEPENDS_ON]->(b:RequirementEntity) WHERE a.id STARTS WITH \"AI_\" RETURN a.title, a.priority, b.title, b.priority ORDER BY a.priority DESC" }' | nix run .#run

# 特定要件の依存チェーン（上流）
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity {id: \"AI_LLM_001\"})-[:DEPENDS_ON*]->(dep:RequirementEntity) RETURN r.title, collect(dep.title) as dependencies" }' | nix run .#run

# 特定要件に依存する要件（下流）
echo '{"type": "cypher", "query": "MATCH (dep:RequirementEntity)-[:DEPENDS_ON*]->(r:RequirementEntity {id: \"AI_PLATFORM_001\"}) RETURN r.title, collect(dep.title) as dependents" }' | nix run .#run
```

### 詳細情報の確認
```bash
# 技術仕様を持つ要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.technical_specifications IS NOT NULL AND r.id STARTS WITH \"AI_\" RETURN r.title, r.technical_specifications" }' | nix run .#run

# 受け入れ条件を持つ要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.acceptance_criteria IS NOT NULL AND r.id STARTS WITH \"AI_\" RETURN r.title, r.acceptance_criteria" }' | nix run .#run

# 検証が必要な要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.verification_required = true AND r.id STARTS WITH \"AI_\" RETURN r.title, r.requirement_type, r.acceptance_criteria" }' | nix run .#run
```

## 4. トレーサビリティ分析パターン

### ビジネス要件からの追跡
```bash
# ビジネス要件から技術要件への追跡
echo '{"type": "cypher", "query": "MATCH (business:RequirementEntity {requirement_type: \"business\"})<-[:DEPENDS_ON*]-(technical:RequirementEntity) WHERE business.id STARTS WITH \"AI_\" AND technical.requirement_type = \"technical\" RETURN business.title, collect(DISTINCT technical.title)" }' | nix run .#run

# 実装状況の確認（IS_IMPLEMENTED_BY関係を使用する場合）
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.id STARTS WITH \"AI_\" OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(impl) RETURN r.title, r.status, count(impl) as implementation_count ORDER BY r.priority DESC" }' | nix run .#run
```

### ギャップ分析
```bash
# 依存関係がない孤立した要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.id STARTS WITH \"AI_\" AND NOT (r)-[:DEPENDS_ON]->() AND NOT ()-[:DEPENDS_ON]->(r) RETURN r.title, r.priority, r.status" }' | nix run .#run

# 高優先度だが未承認の要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.id STARTS WITH \"AI_\" AND r.priority > 200 AND r.status != \"approved\" RETURN r.title, r.priority, r.status ORDER BY r.priority DESC" }' | nix run .#run
```

### 影響分析
```bash
# 特定要件を変更した場合の影響範囲
echo '{"type": "cypher", "query": "MATCH (changed:RequirementEntity {id: \"AI_SECURITY_001\"})<-[:DEPENDS_ON*]-(affected:RequirementEntity) RETURN changed.title as changed_requirement, collect(affected.title) as affected_requirements, count(affected) as impact_count" }' | nix run .#run

# クリティカルパス分析（最も多くの要件が依存している要件）
echo '{"type": "cypher", "query": "MATCH (critical:RequirementEntity)<-[:DEPENDS_ON]-(dependent:RequirementEntity) WHERE critical.id STARTS WITH \"AI_\" RETURN critical.title, critical.priority, count(dependent) as dependency_count ORDER BY dependency_count DESC" }' | nix run .#run
```

## 5. 要件完全性チェックパターン

### 不完全な要件の検出
```bash
# 高優先度で受け入れ条件がない要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.priority >= 200 AND (r.acceptance_criteria IS NULL OR trim(r.acceptance_criteria) = \"\") RETURN r.id, r.title, r.priority, \"Missing acceptance criteria\" as issue ORDER BY r.priority DESC" }' | nix run .#run

# 技術要件で技術仕様がない要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.requirement_type IN [\"technical\", \"infrastructure\"] AND (r.technical_specifications IS NULL OR trim(r.technical_specifications) = \"\") RETURN r.id, r.title, r.requirement_type, \"Missing technical specifications\" as issue" }' | nix run .#run

# 検証必須だがテストがない要件
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.verification_required = true AND NOT (r)-[:IS_VERIFIED_BY]->() RETURN r.id, r.title, \"No verification tests\" as issue" }' | nix run .#run
```

### 完全性レポート
```bash
# 要件完全性サマリー
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WITH r, CASE WHEN r.priority >= 200 AND (r.acceptance_criteria IS NULL OR trim(r.acceptance_criteria) = \"\") THEN 1 ELSE 0 END as missing_criteria, CASE WHEN r.requirement_type IN [\"technical\", \"infrastructure\"] AND (r.technical_specifications IS NULL OR trim(r.technical_specifications) = \"\") THEN 1 ELSE 0 END as missing_specs, CASE WHEN r.verification_required = true AND NOT (r)-[:IS_VERIFIED_BY]->() THEN 1 ELSE 0 END as missing_tests RETURN count(r) as total_requirements, sum(missing_criteria) as missing_acceptance_criteria, sum(missing_specs) as missing_technical_specs, sum(missing_tests) as missing_verification" }' | nix run .#run
```

## 6. スコア分析パターン

### 摩擦分析
```bash
# 現在のスコアを確認（要件追加後に実行）
echo '{"type": "cypher", "query": "CREATE (test:RequirementEntity {id: \"TEST_SCORE_001\", title: \"スコアテスト\"})" }' | nix run .#run
# → レスポンスのscoreセクションを確認

# 高優先度要件の競合確認
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) WHERE r.priority > 200 RETURN r.title, r.priority, r.status ORDER BY r.priority DESC" }' | nix run .#run
```

## 使い方

1. 上記のクエリをコピーして実行
2. 必要に応じてIDやタイムスタンプを変更
3. レスポンスを確認してシステムの状態を把握
4. 複数のクエリを組み合わせて総合的なレビューを実施

## ヒント

- `WHERE r.id STARTS WITH "AI_"` の部分を変更して、特定のプロジェクトの要件のみを抽出
- タイムスタンプを含むIDを使用することで、並行して複数のテストを実行可能
- JSONフィールド（technical_specifications等）はエスケープに注意
- 複雑なクエリは段階的に構築（まず簡単なクエリで確認してから拡張）