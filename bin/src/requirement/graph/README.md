# Requirement Graph System

## 目的 (Purpose)

継続的なフィードバックループを通じて、整合性が高く重複の少ない要件グラフを構築するシステムです。

複雑なプロジェクトでは、異なる立場（経営、PM、開発者）から出される要件同士が、意図せず矛盾したり、重複したり、依存関係が不健全になったりします。本システムは、これらの問題を検知し、具体的な修正を促すことで、プロジェクトの初期段階で要件の品質を最大化することを目的とします。

## 本質

概念とその関係性を有向グラフとして管理する汎用システム。適用領域は使用者が定義する。

### 設計思想: ドメイン知識を持たないシステム

本システムは**要件の内容について一切の知識・判断を持ちません**：

- **ドメイン非依存**: 「要件」が何を意味するかはユーザーが定義
- **純粋なグラフ操作**: ノードとエッジの構造的な制約のみを扱う
- **意味解釈の委譲**: 要件間の矛盾や整合性の判断はユーザーに委ねる

この設計により、あらゆる領域の概念管理に適用可能な汎用性を実現しています。

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

Phase 5.11完了により、以下の機能を提供：
- テンプレートベースの安全な要件操作
- Search serviceによる重複検出（VSS+FTSハイブリッド検索、類似度0.98達成）
- 循環依存の検出とフィードバック
- 深さ制限によるグラフ構造の健全性保証
- 256次元embeddingによる高精度な意味的類似性検索

利用可能なテンプレート：
- `create_requirement`: 要件作成（重複チェック付き）
- `find_requirement`: 要件検索
- `list_requirements`: 要件一覧
- `add_dependency`: 依存関係追加（循環検出付き）
- `find_dependencies`: 依存関係検索
- `search_requirements`: 意味的類似検索（VSS）による要件探索

## 実装状況と将来対応

### ✅ 実装済み
- **重複検出**: Search serviceハイブリッド検索（VSS+FTS）による高精度検出
- **循環依存検出**: 依存関係の健全性保証
- **データ整合性**: Append-onlyアーキテクチャによる完全履歴追跡
- **基本UI**: Template入力によるJSON APIインターフェース（必要十分）

### 🔄 進行中
- **E2Eテスト**: ユーザーワークフローの包括的テスト

### 📋 将来対応
- **[Smart Threshold & Graph-Aware Duplicate Detection](./docs/future/smart_threshold.md)**: グラフ構造を活用した高精度重複検出システム
- **FTS完全インデックス化**: KuzuDBネイティブの全文検索インデックス実装（現在はCONTAINS演算子のみ）
- **修正案提示機能**: 重複・矛盾検出時の具体的修正案自動生成
- **パフォーマンス計測**: 大規模データでの性能指標測定
- **マルチユーザー対応**: 同時アクセス・競合状態の処理
- **メッセージ充実度計測**: フィードバック品質の定量的評価
- **矛盾検出機能**: システムは要件の意味を理解しないため、論理的矛盾の判断は現時点では実装しない
  - **代替案**: 重複検出により類似要件を提示し、ユーザーが矛盾を判断
  - **理由**: ドメイン知識を持たないシステムが「オンプレ」と「クラウド」の矛盾を判断することは設計思想に反する
  - **将来的な対応**: LocationURIと同様に、外部システムとの連携により実現可能

### ❌ 対応予定なし
- **既存ツール連携**: Jira、GitHub Issues等との統合機能
- **WebUI**: ブラウザベースのユーザーインターフェース

### 📚 ドキュメント
現在のREADMEで基本的な使用方法を提供。USAGE.mdの追加も検討可能。

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

# 意味的類似検索による要件探索
echo '{"type": "template", "template": "search_requirements", "parameters": {"query": "認証機能", "limit": 5}}' | nix run .#run
```

### 検索機能について

RGLは高度な検索機能を搭載しています：

- **ハイブリッド検索**: Vector Similarity Search (VSS) と Full-Text Search (FTS) を組み合わせた高精度検索
- **256次元embedding**: OpenAI text-embedding-3-smallモデルによる意味的類似性の計算
- **重複検出**: 類似度0.98以上の要件を自動的に検出し、重複を防止
- **柔軟な検索**: `search_requirements`テンプレートで自然言語クエリによる要件探索が可能

例：「ユーザー認証」で検索すると、「ログイン機能」「二要素認証」「パスワード管理」など意味的に関連する要件がランク付けされて返されます。

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
{"type": "error", "level": "error", "message": "...", "details": {...}, "timestamp": "2025-01-01T00:00:02Z"}
```


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
