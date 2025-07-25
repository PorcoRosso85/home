# LocationURI Dataset Management POC

LocationURIのデータセット管理を実装したProof of Conceptです。

## 責務

- `requirement/graph/**` のスキーマ（特に `LocationURI` ノード）を使用
- `persistence/kuzu_py` を使用したデータベース操作
- 事前定義されたデータセットからのみノード作成を許可する制限機能

## アーキテクチャ

```
uri-poc/
├── mod.py          # コアビジネスロジック（データセット管理、検証、制限付きリポジトリ）
├── main.py         # CLIエントリポイント（LLM-first対話インターフェース）
├── test_mod.py     # ユニットテスト
├── pyproject.toml  # パッケージ設定
├── flake.nix       # Nix環境定義
└── README.md       # このファイル
```

## 主要機能

### 1. LocationURIデータセット管理

事前定義された有効なLocationURIのセットを管理します：

- ルートレベル要件: `req://system`, `req://architecture`, etc.
- サブ要件: `req://architecture/infrastructure`, `req://security/authentication`, etc.
- プロジェクト固有要件: `req://project/trd`, `req://project/kuzu_integration`, etc.

### 2. 制限付きノード作成

データセットに含まれるURIのみノード作成を許可します：

```python
# 許可されたURI（データセット内）
repo["create_locationuri_node"]("req://system")  # ✓ 成功

# 許可されないURI（データセット外）
repo["create_locationuri_node"]("req://custom/path")  # ✗ エラー
```

### 3. URI検証

LocationURIの形式とデータセット制限を検証：

- 形式: `req://` プレフィックス必須
- パス: 空でない、不正文字を含まない
- データセット: 指定時は含有チェック

## 使用方法

### 開発環境

```bash
# 開発シェルに入る
nix develop

# 利用可能なコマンドを表示
nix run .
```

### テスト実行

```bash
nix run .#test
```

### 対話的CLI

```bash
nix run .#cli
```

CLIでは以下のJSON形式でコマンドを入力します：

```json
// リポジトリ初期化
{"action": "init", "db_path": ":memory:"}

// 許可されたデータセット表示
{"action": "list_dataset"}

// ノード作成（データセット内のURIのみ成功）
{"action": "create_node", "uri": "req://system"}

// 作成済みノード一覧
{"action": "list_nodes"}

// URI検証
{"action": "validate", "uri": "req://custom/path"}
```

### デモ実行

```bash
nix run .#demo
```

デモでは以下を自動実行します：
1. インメモリリポジトリの初期化
2. 許可されたデータセットの表示
3. データセット内URIでのノード作成（成功）
4. データセット外URIでのノード作成（失敗）
5. 作成済みノード一覧表示

## 設計原則

### 1. スキーマ準拠

`requirement/graph/ddl/migrations/3.4.0_search_integration.cypher` で定義された `LocationURI` ノードテーブルに準拠します。

### 2. 薄いラッパー哲学

`persistence/kuzu_py` の設計思想に従い、KuzuDBのAPIを隠さず、必要最小限の機能のみ提供します。

### 3. 明示的な制限

データセット外のURIは明示的に拒否し、データ整合性を保証します。

### 4. Result型エラーハンドリング

例外を使わず、Result型パターンでエラーを扱います：

```python
# 成功時
{"type": "Success", "uri": "req://system", "message": "..."}

# エラー時
{"type": "ValidationError", "message": "...", "uri": "..."}
```

## 今後の拡張案

1. **動的データセット**: 外部ファイルやAPIからデータセットを読み込む
2. **階層検証**: 親URIが存在する場合のみ子URIを許可
3. **バージョニング**: LocationURIのバージョン管理機能
4. **権限管理**: ユーザー/ロールによる作成可能URIの制限

## 依存関係

- Python 3.11+
- kuzu_py (ローカルパッケージ)
- KuzuDB (Nix経由で提供)