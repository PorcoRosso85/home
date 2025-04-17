# Deno スクリプト開発ガイドライン

## 基本ルール

1. **単一ファイル実行の原則**
   - スクリプトは単一ファイルで完結するように設計する
   - モジュールディレクトリを生成しない実装を優先する

2. **インポート方法**
   - URL直接インポートを使用する（ローカルインストール不要）
   - 例: `import { parse } from "https://deno.land/std@0.220.1/flags/mod.ts";`

3. **実行方法**
   - スクリプト先頭に Shebang を含める: `#!/usr/bin/env -S deno run --allow-read --allow-write`
   - Nixを使う場合: `nix run nixpkgs#deno -- run --allow-read --allow-write スクリプト名.ts`

4. **コマンドライン引数の処理**
   - std/flags モジュールを使用して引数をパース
   - 例: `const args = parse(Deno.args);`

5. **エントリーポイントの分離**
   - `if (import.meta.main) { main(); }` パターンを使用して、モジュールとして再利用可能にする

## セキュリティに関する注意

- 必要最小限のパーミッションを指定する
  - `--allow-read`: 特定のファイルやディレクトリの読み取りが必要な場合
  - `--allow-write`: ファイル書き込みが必要な場合
  - `--allow-net`: ネットワークアクセスが必要な場合

## メタスキーマCLIの使用方法

メタスキーマCLIは以下のコマンドで使用できます：

```bash
# メタスキーマを登録
nix run nixpkgs#deno -- run --allow-read --allow-write meta-schema-cli.ts register ./string-type-meta.json

# スキーマを生成
nix run nixpkgs#deno -- run --allow-read --allow-write meta-schema-cli.ts generate StringTypeMetaSchema ./userId-config.json ./generated-userId.json

# スキーマを検証
nix run nixpkgs#deno -- run --allow-read --allow-write meta-schema-cli.ts validate ./generated-userId.json
```

## 開発のベストプラクティス

1. **非同期処理**
   - `async/await` パターンを使用する
   - ファイル操作はすべて非同期APIを使用

2. **エラーハンドリング**
   - try/catchでエラーを適切に処理
   - エラーメッセージは具体的に

3. **型安全性**
   - TypeScriptの型システムを最大限活用する
   - インターフェースを明示的に定義

4. **テスト**
   - Denoの組み込みテスト機能を使用
   - 例: `deno test --allow-read test.ts`
