# requirement/graph を使った要件グラフ構築デモ

## プロジェクト: ECサイトの要件管理

### 1. プロジェクト開始 - 要件グラフの初期化

```bash
# プロジェクトディレクトリで要件DBを初期化
$ cd ~/projects/ec-site
$ nix run github:company/requirement-graph#init
✅ Schema applied successfully
データベースが ./rgl_db に作成されました
```

### 2. トップレベル要件の登録

```bash
# 最上位の要件を登録
$ cat > requirements/top-level.json << 'EOF'
{
  "action": "add",
  "requirement": {
    "id": "REQ-001",
    "title": "ECサイトシステム",
    "description": "BtoC向けECサイトの構築。商品検索、カート、決済、会員管理を含む",
    "type": "epic",
    "priority": "critical"
  }
}
EOF

$ cat requirements/top-level.json | nix run github:company/requirement-graph#run
✅ 要件 REQ-001 を登録しました
```

### 3. 機能要件の階層構築

```bash
# ユーザー管理機能
$ echo '{
  "action": "add",
  "requirement": {
    "id": "REQ-100",
    "title": "ユーザー管理機能",
    "description": "会員登録、ログイン、プロファイル管理",
    "type": "feature",
    "parent": "REQ-001"
  }
}' | nix run github:company/requirement-graph#run

# 商品管理機能
$ echo '{
  "action": "add",
  "requirement": {
    "id": "REQ-200",
    "title": "商品カタログ機能",
    "description": "商品検索、カテゴリ、詳細表示",
    "type": "feature",
    "parent": "REQ-001"
  }
}' | nix run github:company/requirement-graph#run

# カート機能
$ echo '{
  "action": "add",
  "requirement": {
    "id": "REQ-300",
    "title": "ショッピングカート機能",
    "description": "カート追加、数量変更、保存",
    "type": "feature",
    "parent": "REQ-001"
  }
}' | nix run github:company/requirement-graph#run
```

### 4. 詳細要件と依存関係の追加

```bash
# 認証要件（ユーザー管理の子要件）
$ cat > requirements/auth-requirements.json << 'EOF'
{
  "batch": [
    {
      "action": "add",
      "requirement": {
        "id": "REQ-101",
        "title": "メール/パスワード認証",
        "description": "基本的なメールアドレスとパスワードによる認証",
        "type": "story",
        "parent": "REQ-100"
      }
    },
    {
      "action": "add",
      "requirement": {
        "id": "REQ-102",
        "title": "ソーシャルログイン",
        "description": "Google, Facebook, Twitterでのログイン",
        "type": "story",
        "parent": "REQ-100"
      }
    },
    {
      "action": "add",
      "requirement": {
        "id": "REQ-103",
        "title": "二要素認証",
        "description": "SMS/TOTP による追加認証オプション",
        "type": "story",
        "parent": "REQ-100"
      }
    }
  ]
}
EOF

$ cat requirements/auth-requirements.json | nix run github:company/requirement-graph#run
✅ 3件の要件を追加しました
```

### 5. 依存関係の定義

```bash
# カート機能は認証が必要
$ echo '{
  "action": "add_dependency",
  "from": "REQ-300",
  "to": "REQ-100",
  "type": "requires",
  "reason": "カート機能は認証されたユーザーのみ利用可能"
}' | nix run github:company/requirement-graph#run

# 決済は複数の機能に依存
$ cat > requirements/payment-deps.json << 'EOF'
{
  "batch": [
    {
      "action": "add",
      "requirement": {
        "id": "REQ-400",
        "title": "決済機能",
        "description": "クレジットカード、銀行振込、コンビニ決済",
        "type": "feature"
      }
    },
    {
      "action": "add_dependency",
      "from": "REQ-400",
      "to": "REQ-300",
      "type": "requires",
      "reason": "決済にはカート内容が必要"
    },
    {
      "action": "add_dependency", 
      "from": "REQ-400",
      "to": "REQ-100",
      "type": "requires",
      "reason": "決済には認証が必要"
    }
  ]
}
EOF

$ cat requirements/payment-deps.json | nix run github:company/requirement-graph#run
```

### 6. 要件の検索と重複チェック

```bash
# 新しい要件を追加する前に重複チェック
$ echo '{
  "action": "check_duplicate",
  "text": "ユーザーがメールアドレスでログインする機能",
  "threshold": 0.7
}' | nix run github:company/requirement-graph#run

出力:
{
  "duplicates": [
    {
      "id": "REQ-101",
      "title": "メール/パスワード認証",
      "score": 0.85,
      "description": "基本的なメールアドレスとパスワードによる認証"
    }
  ],
  "recommendation": "REQ-101 と重複の可能性があります"
}

# 要件の検索
$ echo '{
  "action": "search",
  "query": "認証 ログイン",
  "type": "hybrid"
}' | nix run github:company/requirement-graph#run

結果:
{
  "results": [
    {"id": "REQ-100", "title": "ユーザー管理機能", "score": 0.92},
    {"id": "REQ-101", "title": "メール/パスワード認証", "score": 0.95},
    {"id": "REQ-102", "title": "ソーシャルログイン", "score": 0.88},
    {"id": "REQ-103", "title": "二要素認証", "score": 0.75}
  ]
}
```

### 7. 依存関係グラフの可視化

```bash
# 特定の要件の依存関係を確認
$ echo '{
  "action": "get_dependencies",
  "requirement_id": "REQ-400",
  "depth": 2
}' | nix run github:company/requirement-graph#run

結果:
{
  "requirement": "REQ-400: 決済機能",
  "depends_on": [
    {
      "id": "REQ-300",
      "title": "ショッピングカート機能",
      "depends_on": [
        {"id": "REQ-100", "title": "ユーザー管理機能"}
      ]
    },
    {
      "id": "REQ-100", 
      "title": "ユーザー管理機能"
    }
  ]
}

# 影響分析 - この要件を変更したら何に影響するか
$ echo '{
  "action": "get_dependents",
  "requirement_id": "REQ-100"
}' | nix run github:company/requirement-graph#run

結果:
{
  "requirement": "REQ-100: ユーザー管理機能",
  "impacts": [
    {"id": "REQ-300", "title": "ショッピングカート機能"},
    {"id": "REQ-400", "title": "決済機能"},
    {"id": "REQ-500", "title": "注文履歴機能"},
    {"id": "REQ-600", "title": "レビュー機能"}
  ],
  "total_impact_count": 4
}
```

### 8. バージョン管理と変更追跡

```bash
# 要件の更新
$ echo '{
  "action": "update",
  "requirement": {
    "id": "REQ-101",
    "title": "メール/パスワード認証",
    "description": "メールアドレスとパスワードによる認証。パスワードリセット機能を含む",
    "version": "1.1",
    "change_reason": "パスワードリセット要件の追加"
  }
}' | nix run github:company/requirement-graph#run

# 変更履歴の確認
$ echo '{
  "action": "get_history",
  "requirement_id": "REQ-101"
}' | nix run github:company/requirement-graph#run

結果:
{
  "history": [
    {
      "version": "1.0",
      "timestamp": "2024-01-15T10:00:00Z",
      "description": "基本的なメールアドレスとパスワードによる認証"
    },
    {
      "version": "1.1",
      "timestamp": "2024-01-16T14:30:00Z",
      "description": "メールアドレスとパスワードによる認証。パスワードリセット機能を含む",
      "change_reason": "パスワードリセット要件の追加"
    }
  ]
}
```

### 9. 複雑なクエリと分析

```bash
# 実装優先度の分析 - 依存されている数でランキング
$ echo '{
  "action": "analyze",
  "type": "priority_ranking"
}' | nix run github:company/requirement-graph#run

結果:
{
  "ranking": [
    {"id": "REQ-100", "title": "ユーザー管理機能", "dependency_count": 8, "priority": "critical"},
    {"id": "REQ-200", "title": "商品カタログ機能", "dependency_count": 5, "priority": "high"},
    {"id": "REQ-300", "title": "ショッピングカート機能", "dependency_count": 3, "priority": "high"}
  ]
}

# 循環依存の検出
$ echo '{
  "action": "validate",
  "type": "circular_dependency"
}' | nix run github:company/requirement-graph#run

結果:
{
  "status": "ok",
  "circular_dependencies": [],
  "message": "循環依存は検出されませんでした"
}
```

### 10. レポート生成

```bash
# 要件グラフの統計情報
$ echo '{
  "action": "report",
  "type": "statistics"
}' | nix run github:company/requirement-graph#run

結果:
{
  "statistics": {
    "total_requirements": 47,
    "by_type": {
      "epic": 1,
      "feature": 12,
      "story": 34
    },
    "total_dependencies": 68,
    "max_dependency_depth": 4,
    "isolated_requirements": 3,
    "highly_connected": [
      {"id": "REQ-100", "connections": 15},
      {"id": "REQ-200", "connections": 12}
    ]
  }
}

# 実装計画の生成（トポロジカルソート）
$ echo '{
  "action": "generate_plan",
  "type": "implementation_order"
}' | nix run github:company/requirement-graph#run

結果:
{
  "implementation_phases": [
    {
      "phase": 1,
      "requirements": ["REQ-100", "REQ-200"],
      "reason": "他の機能が依存する基盤機能"
    },
    {
      "phase": 2,
      "requirements": ["REQ-300", "REQ-201", "REQ-202"],
      "reason": "基盤機能に依存する機能"
    },
    {
      "phase": 3,
      "requirements": ["REQ-400", "REQ-500"],
      "reason": "複数の機能に依存する統合機能"
    }
  ]
}
```

## 構築された要件グラフの活用

1. **開発計画**: 依存関係から実装順序を自動決定
2. **影響分析**: 要件変更時の影響範囲を即座に把握
3. **重複防止**: 類似要件の自動検出で品質向上
4. **進捗管理**: 依存関係を考慮した進捗の可視化
5. **リスク管理**: 高依存度要件の特定と対策