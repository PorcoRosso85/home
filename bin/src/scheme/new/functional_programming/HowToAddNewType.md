# 新しい型スキーマの生成方法

このドキュメントでは、様々な型スキーマを生成するための具体的な使用例を示します。

## 関数型スキーマの生成例

### 基本的な関数型スキーマ

最もシンプルな生成方法は、デフォルト設定を使用する方法です。

```bash
./interface/cli.ts generate-new
```

これにより、基本的な関数型メタスキーマ（Function__Meta.json）が生成されます。

### カスタム関数型スキーマ

特定の設定でカスタマイズされた関数型スキーマを生成できます。

```bash
./interface/cli.ts generate-new \
  --type function \
  --title "UserAuth Function" \
  --desc "ユーザー認証を行う関数" \
  --resource-uri "file:///src/auth/userAuth.ts" \
  --output ./UserAuth__Function.json
```

### 特定のプロパティをスキップした関数型スキーマ

不要なプロパティをスキップして、より軽量なスキーマを生成できます。

```bash
./interface/cli.ts generate-new \
  --title "UserAuth Function" \
  --desc "ユーザー認証を行う関数" \
  --skip multipleReturns,composition,thrownExceptions \
  --output ./UserAuth__Function.json
```

### 機能カテゴリ全体をスキップした関数型スキーマ

機能カテゴリー全体をスキップすることも可能です。

```bash
./interface/cli.ts generate-new \
  --title "UserAuth Function" \
  --desc "ユーザー認証を行う関数" \
  --skip features \
  --output ./UserAuth__Function.json
```

## 構造体型スキーマの生成例（将来的な拡張）

現在のバージョンでは関数型のみがサポートされていますが、将来的には以下のような構造体型スキーマの生成もサポート予定です。

```bash
# 将来的にサポート予定の構造体型スキーマ生成コマンド
./interface/cli.ts generate-new \
  --type struct \
  --title "User Struct" \
  --desc "ユーザー情報を表す構造体" \
  --resource-uri "file:///src/models/user.ts" \
  --output ./User__Struct.json
```

## データベース連携

生成したスキーマをデータベースに保存することも可能です。

```bash
./interface/cli.ts generate-new \
  --title "UserAuth Function" \
  --db \
  --db-type cozo \
  --output ./UserAuth__Function.json
```

## 詳細表示とドライラン

生成前に詳細な設定を確認したり、実際のファイル生成をせずに結果を確認したりできます。

```bash
# 詳細設定表示
./interface/cli.ts generate-new --verbose

# ドライラン（ファイル生成なし）
./interface/cli.ts generate-new --dry-run

# 詳細表示とドライラン
./interface/cli.ts generate-new --verbose --dry-run
```

## スキップ可能なプロパティ一覧

以下は、`--skip`フラグで指定可能な主なプロパティです：

- `features` - 機能特性全体
- `composition` - 関数合成情報
- `tests` - テスト情報
- `multipleReturns` - 複数戻り値機能
- `thrownExceptions` - 例外情報
- `usageExamples` - 使用例
- `externalDependencies` - 外部依存関係

複数のプロパティをスキップする場合は、カンマで区切って指定します：

```bash
./interface/cli.ts generate-new --skip composition,tests,multipleReturns
```

## サポートされている型種別（タイプ）

現在サポートされている型種別と将来的にサポート予定の型種別：

- `function` - 関数型（現在サポート済み）
- `struct` - 構造体型（将来対応予定）
- `list` - リスト型（将来対応予定）
- `enum` - 列挙型（将来対応予定）
- `union` - 共用体型（将来対応予定）
- `primitive` - プリミティブ型（将来対応予定）

## ヘルプ情報の表示

コマンドのヘルプ情報を表示するには：

```bash
./interface/cli.ts generate-new --help
# または
./interface/cli.ts help generate-new
```
