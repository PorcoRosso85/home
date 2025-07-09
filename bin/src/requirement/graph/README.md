# Requirement Graph Logic (RGL)

## 目的 (Purpose)

RGLは、**継続的なフィードバックループを通じて、整合性が高く摩擦の少ない要件グラフを構築する**ためのシステムです。

複雑なプロジェクトでは、異なる立場（経営、PM、開発者）から出される要件同士が、意図せず矛盾したり、曖昧だったり、依存関係が不健全になったりします。RGLは、これらの"摩擦"をリアルタイムで検知・スコアリングし、具体的な修正を促すことで、プロジェクトの初期段階で要件の品質を最大化することを目的とします。

## コアコンセプト：対話的な要件構築

RGLの利用は、一方的な命令ではなく、システムとの対話によって進みます。

1.  **提案 (Propose):** ユーザーはCypherクエリを使って、新しい要件や依存関係をシステムに提案します。
2.  **評価 (Evaluate):** RGLは提案された内容を即座に評価し、グラフ制約違反、循環参照、曖昧さなどの"摩擦"を検知してスコアを返します。
3.  **改善 (Refine):** ユーザーはスコアやエラーメッセージという具体的なフィードバックを元に、Cypherクエリを修正・改善します。

この「提案→評価→改善」のサイクルを繰り返すことで、個々の要件がシステム全体の整合性と調和し、最終的に健全で摩擦の少ない要件グラフが構築されます。

## システムの流れ

```
┌─────────┐        ┌──────────┐        ┌─────────┐
│ Me/LLM  │        │  System  │        │ KuzuDB  │
└────┬────┘        └────┬─────┘        └────┬────┘
     │                   │                   │
     │ Cypher Query      │                   │
     ├──────────────────>│                   │
     │ (1. Propose)      │                   │
     │                   │                   │
     │                   ├─ 2. Evaluate     │
     │                   │  (グラフ検証, 摩擦分析) │
     │                   │                   │
     │ JSONL Response    │                   │
     │ (score, errors)   │                   │
     │<──────────────────┤                   │
     │                   │                   │
     │ 3. Refine Query   │                   │
     ├──────────────────>│                   │
     │ ...               │                   │
```

### フィードバックの例と改善アクション

| 入力 (Cypherクエリの意図) | システムからのフィードバック (抜粋) | 問題点と次のアクション |
| :--- | :--- | :--- |
| 深いグラフ構造を作成（設定された深さ制限を超える） | `{"score": -1.0, "message": "グラフ深さ制限: ..."}` | **深さ制限違反。** プロジェクトで設定されたグラフの深さ上限を超えています。中間の要件を追加するか、依存関係を再構成する。 |
| A→B→C→Aという依存関係を作成 | `{"score": -1.0, "message": "循環参照: ..."}` | **依存関係のループ。** プロジェクトが進行不能になる。依存関係を見直し、循環を断ち切る。 |
| 「使いやすいUI」という曖昧な要件を追加 | `{"frictions": {"ambiguity": -0.6}}` | **要件の曖昧さ。** 「使いやすい」の定義が不明。より具体的な受け入れ基準（例：「ログインボタンは画面右上に配置」）を持つ子要件に分解する。 |
| 複数チームが同じ機能に異なる優先度で要件を追加 | `{"frictions": {"priority": -0.7}}` | **優先度の競合。** 関係者間の合意が取れていない可能性。優先度についてチーム間で協議し、値を統一する。 |

## クイックスタート

```bash
# 開発環境
nix develop

# テスト実行（必須方法 - 直接pytestは禁止）
nix run .#test

# 実行
nix run .#run
```

## 使い方

```bash
# スキーマ初期化（初回のみ）
nix run .#init

# 基本的な要件作成
echo '{"type": "cypher", "query": "CREATE (r:RequirementEntity {id: \"req_001\", title: \"ユーザー認証機能\", description: \"安全なログイン機能を提供\"})"}' | nix run .#run

# 詳細な要件作成（より多くのプロパティを使用）
echo '{"type": "cypher", "query": "CREATE (r:RequirementEntity {id: \"req_002\", title: \"二要素認証\", description: \"セキュリティ強化のための2FA実装\", status: \"proposed\"})"}' | nix run .#run

# 依存関係の作成（req_002はreq_001に依存）
echo '{"type": "cypher", "query": "MATCH (a:RequirementEntity {id: \"req_002\"}), (b:RequirementEntity {id: \"req_001\"}) CREATE (a)-[:DEPENDS_ON]->(b)"}' | nix run .#run

# 要件の確認
echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) RETURN r.id, r.title, r.status ORDER BY r.id"}' | nix run .#run

# 依存関係の確認
echo '{"type": "cypher", "query": "MATCH (a:RequirementEntity)-[:DEPENDS_ON]->(b:RequirementEntity) RETURN a.id, a.title, b.id, b.title"}' | nix run .#run
```

### デバッグ/トレース

システムの動作を詳しく追跡したい場合は、環境変数 `RGL_LOG_LEVEL` を使用します：

```bash
# すべてのモジュールのトレースログを有効化
RGL_LOG_LEVEL="*:TRACE" echo '{"type": "cypher", "query": "MATCH (r:RequirementEntity) RETURN r"}' | nix run .#run

# 特定モジュールのデバッグログ
RGL_LOG_LEVEL="rgl.main:DEBUG" echo '{"type": "cypher", "query": "CREATE (r:RequirementEntity {id: \"req_debug\"})"}' | nix run .#run

# 複数モジュールの設定
RGL_LOG_LEVEL="*:WARN,rgl.validator:DEBUG,rgl.scorer:TRACE" echo '{"type": "cypher", "query": "MATCH (r) RETURN r"}' | nix run .#run

# DBパスも指定する場合
RGL_DB_PATH="/tmp/my_rgl_db" RGL_LOG_LEVEL="*:DEBUG" echo '{"type": "cypher", "query": "MATCH (r) RETURN r"}' | nix run .#run
```

ログレベル（詳細度順）：
- `TRACE`: 最も詳細な実行トレース
- `DEBUG`: デバッグ情報
- `INFO`: 一般的な情報
- `WARN`: 警告（デフォルト）
- `ERROR`: エラーのみ

## スキーマ定義

RGLのスキーマ（ノード、プロパティ、リレーション）の詳細については以下を参照してください：

- **現在のスキーマ**: `ddl/migrations/3.3.0_simplified.cypher`
- **マイグレーション履歴**: `ddl/migrations/`

主要なノードタイプ：
- **RequirementEntity**: 要件を表現
- **LocationURI**: 要件の識別子を管理
- **VersionState**: バージョン履歴を追跡

主要なリレーション：
- **DEPENDS_ON**: 要件間の依存関係を表現
- **LOCATES**: LocationURIと要件の関連付け
- **TRACKS_STATE_OF**: バージョン状態の追跡

## 出力フォーマット

すべての出力はJSONL（JSON Lines）形式で返されます：

```jsonl
{"type": "result", "level": "info", "data": [...], "timestamp": "2025-01-01T00:00:00Z"}
{"type": "score", "level": "info", "data": {"frictions": {...}, "total": {...}}, "timestamp": "2025-01-01T00:00:01Z"}
{"type": "error", "level": "error", "message": "...", "details": {...}, "timestamp": "2025-01-01T00:00:02Z"}
```

### 摩擦スコアの解釈

- **0.0**: 問題なし（健全）
- **-0.1 〜 -0.3**: 軽微な問題（要注意）
- **-0.4 〜 -0.7**: 中程度の問題（要改善）
- **-0.8 〜 -1.0**: 深刻な問題（要対応）

## よくあるエラーと対処法

### "Cannot find property parent_id"
```bash
# ❌ 間違い
CREATE (r:RequirementEntity {id: "req_002", parent_id: "req_001"})

# ✅ 正しい方法（依存関係を使用）
MATCH (a:RequirementEntity {id: "req_002"}), (b:RequirementEntity {id: "req_001"})
CREATE (a)-[:DEPENDS_ON]->(b)
```

### "Binder exception: Table PARENT_OF does not exist"
```bash
# ❌ 間違い（存在しないリレーション）
CREATE (a)-[:PARENT_OF]->(b)

# ✅ 正しいリレーション
CREATE (a)-[:DEPENDS_ON]->(b)
```

### グラフ深さ制限違反
```bash
# 深い依存関係チェーンを避ける
# A→B→C→D→E→F（深さ6）は制限違反の可能性

# 解決策：中間要件でグループ化
# A→G、B→G、G→D、E→D、F→D
```
