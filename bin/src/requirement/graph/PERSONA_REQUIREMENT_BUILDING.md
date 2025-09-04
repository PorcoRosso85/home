# requirement/graph 実践使用記録とレビュー

## ペルソナ紹介

### 山田さん（プロダクトマネージャー）
- 技術背景: 元エンジニア、現在はビジネス寄り
- 役割: 要件定義、ステークホルダー調整
- ツール経験: Jira、Confluence、Excel

### 佐藤さん（テックリード）  
- 技術背景: フルスタックエンジニア
- 役割: アーキテクチャ設計、技術要件定義
- ツール経験: GitHub Issues、Notion、PlantUML

## プロジェクト: 社内業務管理システムのリニューアル

---

## Day 1: 初期セットアップと最初の要件

### 山田さん（14:00）
```bash
# 佐藤さんから教えてもらったコマンドでセットアップ
$ cd ~/projects/internal-system
$ nix run github:company/requirement-graph#init
✅ Schema applied successfully
データベースが ./rgl_db に作成されました

# とりあえずトップレベルの要件を登録してみる
$ echo '{
  "action": "add",
  "requirement": {
    "id": "BIZ-001",
    "title": "業務管理システムリニューアル",
    "description": "レガシーシステムの刷新。勤怠、経費精算、申請ワークフローを統合",
    "type": "epic"
  }
}' | nix run github:company/requirement-graph#run
✅ 要件 BIZ-001 を登録しました

# 「お、JSONで入力するのか。最初は戸惑うけど、構造化されてていいかも」
```

### 佐藤さん（14:30）
```bash
# 技術的な要件を追加
$ cat > tech-requirements.json << 'EOF'
{
  "batch": [
    {
      "action": "add",
      "requirement": {
        "id": "TECH-001",
        "title": "マイクロサービス化",
        "description": "勤怠、経費、ワークフローを独立したサービスとして実装",
        "type": "feature",
        "parent": "BIZ-001"
      }
    },
    {
      "action": "add",
      "requirement": {
        "id": "TECH-002",
        "title": "認証基盤",
        "description": "OAuth2/OIDC準拠のSSO基盤",
        "type": "feature",
        "parent": "BIZ-001"
      }
    }
  ]
}
EOF

$ cat tech-requirements.json | nix run github:company/requirement-graph#run
✅ 2件の要件を追加しました

# 依存関係も定義
$ echo '{
  "action": "add_dependency",
  "from": "TECH-001",
  "to": "TECH-002",
  "type": "requires",
  "reason": "各マイクロサービスは共通認証基盤を使用"
}' | nix run github:company/requirement-graph#run
✅ 依存関係を追加しました
```

---

## Day 2: 要件の詳細化と重複発見

### 山田さん（10:00）
```bash
# ビジネス要件を詳細化
$ echo '{
  "action": "add",
  "requirement": {
    "id": "BIZ-100",
    "title": "勤怠管理機能",
    "description": "出退勤、休暇申請、シフト管理",
    "type": "feature",
    "parent": "BIZ-001"
  }
}' | nix run github:company/requirement-graph#run

# 新しい要件を追加しようとして...
$ echo '{
  "action": "check_duplicate",
  "text": "従業員の出勤時間と退勤時間を記録する機能",
  "threshold": 0.6
}' | nix run github:company/requirement-graph#run

{
  "duplicates": [
    {
      "id": "BIZ-100",
      "title": "勤怠管理機能",
      "score": 0.78,
      "description": "出退勤、休暇申請、シフト管理"
    }
  ]
}

# 「おお！重複を検出してくれた。これは便利」
# 「Excelだと気づかずに似たような要件を書いちゃうことがあったんだよね」
```

### 佐藤さん（11:00）
```bash
# 技術要件の検索
$ echo '{
  "action": "search",
  "query": "認証 セキュリティ SSO",
  "type": "hybrid"
}' | nix run github:company/requirement-graph#run

{
  "results": [
    {"id": "TECH-002", "title": "認証基盤", "score": 0.95},
    {"id": "TECH-015", "title": "API認証", "score": 0.72},
    {"id": "SEC-001", "title": "セキュリティ要件", "score": 0.68}
  ]
}

# 既存の認証要件を確認してから、詳細要件を追加
$ cat > auth-details.json << 'EOF'
{
  "batch": [
    {
      "action": "add",
      "requirement": {
        "id": "TECH-002-1",
        "title": "SAML連携",
        "description": "既存AD連携のためのSAML2.0サポート",
        "type": "story",
        "parent": "TECH-002"
      }
    },
    {
      "action": "add",
      "requirement": {
        "id": "TECH-002-2",
        "title": "MFA対応",
        "description": "TOTP/WebAuthnによる多要素認証",
        "type": "story",
        "parent": "TECH-002"
      }
    }
  ]
}
EOF

$ cat auth-details.json | nix run github:company/requirement-graph#run
```

---

## Day 3: 影響分析と優先度決定

### 山田さん（13:00）
```bash
# 認証基盤の変更がどこに影響するか確認
$ echo '{
  "action": "get_dependents",
  "requirement_id": "TECH-002"
}' | nix run github:company/requirement-graph#run

{
  "requirement": "TECH-002: 認証基盤",
  "impacts": [
    {"id": "TECH-001", "title": "マイクロサービス化"},
    {"id": "BIZ-100", "title": "勤怠管理機能"},
    {"id": "BIZ-200", "title": "経費精算機能"},
    {"id": "BIZ-300", "title": "ワークフロー機能"}
  ],
  "total_impact_count": 4
}

# 「認証基盤って全部に影響するんだ...これ最初にやらないとダメだね」
```

### 佐藤さん（15:00）
```bash
# 実装順序の分析
$ echo '{
  "action": "generate_plan",
  "type": "implementation_order"
}' | nix run github:company/requirement-graph#run

{
  "implementation_phases": [
    {
      "phase": 1,
      "requirements": ["TECH-002", "INFRA-001"],
      "reason": "他の全機能が依存する基盤"
    },
    {
      "phase": 2,
      "requirements": ["TECH-001", "DB-001"],
      "reason": "アプリケーション基盤"
    },
    {
      "phase": 3,
      "requirements": ["BIZ-100", "BIZ-200", "BIZ-300"],
      "reason": "ビジネス機能"
    }
  ]
}

# プロジェクト統計も確認
$ echo '{
  "action": "report",
  "type": "statistics"
}' | nix run github:company/requirement-graph#run

{
  "statistics": {
    "total_requirements": 42,
    "by_type": {
      "epic": 1,
      "feature": 15,
      "story": 26
    },
    "total_dependencies": 38,
    "max_dependency_depth": 4
  }
}
```

---

## Day 5: 変更管理とレビュー

### 山田さん（16:00）
```bash
# ステークホルダーからのフィードバックで要件更新
$ echo '{
  "action": "update",
  "requirement": {
    "id": "BIZ-100",
    "title": "勤怠管理機能",
    "description": "出退勤、休暇申請、シフト管理、リモートワーク対応",
    "version": "1.1",
    "change_reason": "コロナ後のリモートワーク要件追加"
  }
}' | nix run github:company/requirement-graph#run

# 変更履歴を確認
$ echo '{
  "action": "get_history",
  "requirement_id": "BIZ-100"
}' | nix run github:company/requirement-graph#run

# 「バージョン管理があるのはいいね。Excelだと変更履歴が追えなくて困ってた」
```

---

## 使用後のレビュー

### 山田さんのレビュー ⭐⭐⭐⭐☆

**良かった点:**
- 重複検出が本当に便利。似た要件を書きそうになったら警告してくれる
- 影響分析機能で、要件変更の影響範囲がすぐ分かる
- バージョン管理で変更履歴が追える
- 検索が高速で、過去の要件を探しやすい

**改善してほしい点:**
- JSON入力は慣れるまで大変。Web UIかExcelインポートが欲しい
- 要件のテンプレート機能があるといい
- ガントチャートやカンバンビューでの可視化が欲しい
- 承認ワークフローとの連携

**総評:**
「最初はJSON入力に戸惑ったけど、慣れると構造化されていて良い。特に重複検出と影響分析は、今までのツールにない価値。ただ、非エンジニアのステークホルダーに使ってもらうにはUIが必要」

### 佐藤さんのレビュー ⭐⭐⭐⭐⭐

**良かった点:**
- グラフDBで依存関係が自然に表現できる
- VSS/FTSの検索精度が高い
- Nixで環境構築が簡単、チーム全員が同じ環境を使える
- APIとして使えるので、CI/CDに組み込みやすい
- 実装順序の自動生成が便利

**改善してほしい点:**
- GraphQLやREST APIがあると、他システムとの連携が楽
- 要件からテストケースの自動生成があるといい
- PlantUMLやMermaidでの図の自動生成
- より高度な分析（クリティカルパス、ボトルネック検出）

**総評:**
「技術的には非常に良くできている。グラフDBの利点を活かした設計で、複雑な依存関係も簡単に扱える。JSON入力も、プログラマブルで自動化しやすくて良い。あとはAPIやプラグイン機構があれば完璧」

## まとめ

両者とも高評価だが、視点の違いが明確：
- **山田さん（PM）**: UI/UX、他ツールとの連携、非技術者への配慮を求める
- **佐藤さん（Tech Lead）**: API、自動化、技術的な拡張性を評価

共通して評価された点：
1. **重複検出機能**
2. **依存関係の可視化と影響分析**
3. **高速な検索機能**
4. **バージョン管理**

このツールは技術者には即座に価値を提供するが、非技術者向けにはUIレイヤーが必要という結論。