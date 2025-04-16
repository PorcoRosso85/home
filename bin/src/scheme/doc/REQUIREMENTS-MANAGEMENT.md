# 要件管理システム

このドキュメントでは、要件管理システムの使用方法について説明します。要件管理システムは、機能要件を定義し、それらの間の依存関係を管理するためのツールセットです。

## 概要

要件管理システムは以下の機能を提供します：

1. 要件の定義と管理
2. 要件間の依存関係の解析と可視化
3. 要件からの関数定義JSONの生成

各要件は独自のJSONファイルとして保存され、一つの要件が一つの機能（関数、構造体など）に対応します。

## ディレクトリ構造

```
/home/nixos/scheme/
├── data/
│   ├── requirements.meta/     # 要件メタスキーマ
│   │   └── Requirement.meta.json   # 要件のメタスキーマ定義
│   └── requirements.generated/ # 生成された要件JSON
│       ├── UserManager.json    # 要件例：ユーザー管理機能
│       └── UserRegister.json   # 要件例：ユーザー登録機能
├── doc/
│   └── REQUIREMENTS-MANAGEMENT.md # このドキュメント
└── src/
    └── ... # 実装ファイル
```

## インストールと使用準備

各スクリプトは実行権限が必要です：

```bash
# 実行権限の付与
chmod +x requirements-generator.ts requirements-deps.ts requirements-to-function.ts
```

スクリプトはNixとDenoを使用します。Shebang行が正しく設定されていれば、必要な環境が自動的に設定されます。実行時にはNixシェルが一時的にDeno環境を提供します。

必要なディレクトリ構造は以下の通りです：

```
/home/nixos/scheme/
├── data/
│   ├── requirements.meta/     # 要件メタスキーマ
│   │   └── Requirement.meta.json
│   └── requirements.generated/ # 生成された要件JSON
└── scripts/
    ├── requirements-generator.ts  # 要件生成スクリプト
    ├── requirements-deps.ts      # 依存関係解析スクリプト
    └── requirements-to-function.ts # 関数定義生成スクリプト
```

### 1. 要件生成スクリプト (requirements-generator.ts)

新しい要件の作成、既存の要件からの派生、要件一覧の表示、要件の検証などの機能を提供します。

#### 使用例

```bash
# 新しい要件を作成
deno run --allow-read --allow-write requirements-generator.ts create UserSearch \
  --title="ユーザー検索機能" \
  --desc="ユーザーを名前やメールアドレスで検索する機能" \
  --type=function \
  --deps=UserManager

# 既存の要件から新しい要件を派生
deno run --allow-read --allow-write requirements-generator.ts derive UserManager UserLogin \
  --title="ユーザーログイン機能" \
  --desc="ユーザー認証とログイン処理を行う機能"

# 要件一覧を表示
deno run --allow-read --allow-write requirements-generator.ts list

# 要件を検証
deno run --allow-read --allow-write requirements-generator.ts validate UserManager
```

### 2. 依存関係解析スクリプト (requirements-deps.ts)

要件間の依存関係を解析し、ツリー構造やグラフとして表示します。

#### 使用例

```bash
# 特定の要件の依存関係を表示
deno run --allow-read --allow-write requirements-deps.ts deps UserManager

# 全要件の依存関係グラフを表示
deno run --allow-read --allow-write requirements-deps.ts graph

# Mermaid形式で依存関係を出力
deno run --allow-read --allow-write requirements-deps.ts deps UserManager --format=mermaid

# 全要件を一覧表示
deno run --allow-read --allow-write requirements-deps.ts list
```

### 3. 関数定義生成スクリプト (requirements-to-function.ts)

要件JSONから関数定義JSONを生成します。この関数定義JSONは、既存の生成システムで使用されます。

#### 使用例

```bash
# 要件から関数定義JSONを生成
deno run --allow-read --allow-write requirements-to-function.ts UserManager

# 出力先ディレクトリを指定して生成
deno run --allow-read --allow-write requirements-to-function.ts UserManager --outDir=./data/config

# 既存の関数定義を上書き
deno run --allow-read --allow-write requirements-to-function.ts UserManager --force

# 内容のみ表示（実際には出力しない）
deno run --allow-read --allow-write requirements-to-function.ts UserManager --dryRun
```

## 要件の構造

要件JSONは以下の基本構造を持ちます：

```json
{
  "$schema": "/home/nixos/scheme/data/requirements.meta/Requirement.meta.json",
  "$metaSchema": "Requirement",
  "id": "UserManager",
  "title": "ユーザー管理機能",
  "description": "ユーザー情報の登録・取得・更新・削除を行う基本的なユーザー管理機能",
  "outputType": "function",
  "outputPath": {
    "default": "/src/user/UserManager.js",
    "typescript": "/src/user/UserManager.ts",
    "python": "/src/user/user_manager.py"
  },
  "outputInfo": {
    "function": {
      "parameters": { /*...*/ },
      "returnType": { /*...*/ },
      "async": true
    }
  },
  "dependencies": ["User", "UserError"],
  "tags": ["user", "authentication", "core"],
  "priority": "high",
  "status": "approved",
  "createdAt": "2025-03-21T14:40:00Z",
  "updatedAt": "2025-03-21T14:40:00Z"
}
```

### 主要なフィールド

- `id` - 要件の一意識別子
- `title` - 要件のタイトル
- `description` - 要件の詳細説明
- `outputType` - 出力タイプ（"function", "struct", "string", "enum"のいずれか）
- `outputPath` - 各言語での実装パス
- `outputInfo` - 出力タイプに応じた詳細情報
- `dependencies` - この要件が依存する他の要件のID一覧
- `tags` - 要件に関連するタグ
- `priority` - 優先度（"high", "medium", "low"）
- `status` - 状態（"draft", "pending", "approved", "implemented", "deprecated"）

## 依存関係の構造

要件間の依存関係は、親要件（依存される側）と子要件（依存する側）の関係として表現されます。

例えば：
- `UserManager` には `UserRegister`, `UserLogin`, `UserSearch` などの子要件が依存します
- `UserRegister` は `User`, `Email`, `Password` などの型要件に依存するかもしれません

依存関係はグラフ構造として表現され、循環参照も検出されます。

## ワークフロー例

1. 機能の要件を定義：
   ```bash
   deno run --allow-read --allow-write requirements-generator.ts create OrderManager \
     --title="注文管理機能" \
     --type=function
   ```

2. 子要件を派生：
   ```bash
   deno run --allow-read --allow-write requirements-generator.ts derive OrderManager PlaceOrder \
     --title="注文作成機能" \
     --desc="新しい注文を作成し、在庫確認と価格計算を行う"
   ```

3. 依存関係を確認：
   ```bash
   deno run --allow-read --allow-write requirements-deps.ts graph
   ```

4. 関数定義を生成：
   ```bash
   deno run --allow-read --allow-write requirements-to-function.ts PlaceOrder
   ```

## 注意事項

- 要件IDには英数字、ハイフン、アンダースコアのみ使用できます
- 要件間の循環参照は避けることを推奨します
- 生成された関数定義は手動で調整が必要な場合があります
