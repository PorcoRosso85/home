# Requirement Graph System

## 目的 (Purpose)

継続的なフィードバックループを通じて、整合性が高く重複の少ない要件グラフを構築するシステムです。

複雑なプロジェクトでは、異なる立場（経営、PM、開発者）から出される要件同士が、意図せず矛盾したり、重複したり、依存関係が不健全になったりします。本システムは、これらの問題を検知し、具体的な修正を促すことで、プロジェクトの初期段階で要件の品質を最大化することを目的とします。

## 本質

概念とその関係性を有向グラフとして管理する汎用システム。適用領域は使用者が定義する。

### 設計思想: Append-Only Architecture

本システムは**Git-likeなappend-only**アーキテクチャを採用しています：

- **イミュータブルな要件**: 一度作成された要件は削除・更新されず、新しいバージョンが追加される
- **完全な履歴追跡**: すべての変更は新しいバージョンとして記録され、過去の状態を完全に再現可能
- **データの整合性**: 削除や更新による不整合が発生しない
- **監査可能性**: いつ、誰が、何を、なぜ変更したかを完全に追跡

この設計により、要件の進化過程を透明化し、意思決定の根拠を永続的に保持します。

## アーキテクチャ

- [`domain/`](./domain/README.md) - 要件グラフのルールと制約
- [`application/`](./application/README.md) - 操作可能なユースケース（削減済み）
- [`infrastructure/`](./infrastructure/README.md) - 技術的実現手段

## 現在の状態

Phase 3完了により、以下の機能を提供：
- テンプレートベースの安全な要件操作
- POC searchによる重複検出（VSS+FTSハイブリッド検索）
- 循環依存の検出とフィードバック
- 深さ制限によるグラフ構造の健全性保証

利用可能なテンプレート：
- `create_requirement`: 要件作成（重複チェック付き）
- `find_requirement`: 要件検索
- `list_requirements`: 要件一覧
- `add_dependency`: 依存関係追加（循環検出付き）
- `find_dependencies`: 依存関係検索

## システムの流れ

```
┌─────────┐        ┌──────────┐        ┌─────────┐
│ Me/LLM  │        │  System  │        │ KuzuDB  │
└────┬────┘        └────┬─────┘        └────┬────┘
     │                   │                   │
     │ Template Input    │                   │
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

| 入力 (テンプレートの意図) | システムからのフィードバック (抜粋) | 問題点と次のアクション |
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
# または
echo '{"type": "schema", "action": "apply"}' | nix run .#run

# 基本的な要件作成（テンプレート入力）
echo '{"type": "template", "template": "create_requirement", "parameters": {"id": "req_001", "title": "ユーザー認証機能", "description": "安全なログイン機能を提供"}}' | nix run .#run

# 詳細な要件作成（ステータス指定）
echo '{"type": "template", "template": "create_requirement", "parameters": {"id": "req_002", "title": "二要素認証", "description": "セキュリティ強化のための2FA実装", "status": "proposed"}}' | nix run .#run

# 依存関係の作成（req_002はreq_001に依存）
echo '{"type": "template", "template": "add_dependency", "parameters": {"child_id": "req_002", "parent_id": "req_001"}}' | nix run .#run

# 要件の検索
echo '{"type": "template", "template": "find_requirement", "parameters": {"id": "req_001"}}' | nix run .#run

# 要件の一覧取得
echo '{"type": "template", "template": "list_requirements", "parameters": {"limit": 10}}' | nix run .#run

# 依存関係の検索
echo '{"type": "template", "template": "find_dependencies", "parameters": {"requirement_id": "req_002", "depth": 2}}' | nix run .#run
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

### "テンプレートが見つからない"
```bash
# ❌ 間違い
{"type": "template", "template": "add_requirement", "parameters": {...}}

# ✅ 正しいテンプレート名
{"type": "template", "template": "create_requirement", "parameters": {...}}
```

### "必須パラメータが不足"
```bash
# ❌ 間違い（idとtitleが必須）
{"type": "template", "template": "create_requirement", "parameters": {}}

# ✅ 正しい
{"type": "template", "template": "create_requirement", "parameters": {
  "id": "req_001",
  "title": "要件名"
}}
```

### "循環依存が検出されました"
```bash
# ❌ 間違い（A→B→Aの循環）
{"type": "template", "template": "add_dependency", 
 "parameters": {"child_id": "req_001", "parent_id": "req_002"}}

# ✅ 解決策：依存関係を見直し、循環を断ち切る
```

### グラフ深さ制限違反
```bash
# 深い依存関係チェーンを避ける
# A→B→C→D→E→F（深さ6）は制限違反の可能性

# 解決策：中間要件でグループ化
# A→G、B→G、G→D、E→D、F→D
```
