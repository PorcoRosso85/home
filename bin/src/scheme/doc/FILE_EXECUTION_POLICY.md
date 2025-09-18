# ファイル実行ポリシー

## 実行権限について

このプロジェクトでは、コマンドラインインターフェースとして実行するファイルには適切な実行権限を付与する必要があります。

### 主要なエントリポイント

以下のファイルは実行権限が必要です：

- `/home/nixos/scheme/src/interface/cli.ts` - メインエントリポイント

```bash
# 実行権限を付与するコマンド
chmod +x /home/nixos/scheme/src/interface/cli.ts
```

### シェバンルール

すべての実行可能なスクリプトには適切なシェバンを指定します。このプロジェクトでは、nix shellを使用してDenoを実行する形式を採用しています。

```bash
#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run
```

この形式は以下の利点があります：
- Nix環境でDenoが利用可能になる
- 適切なDeno実行権限が自動的に指定される
- プロジェクト全体で一貫した実行環境が維持される

### コマンド実行

統合されたCLIコマンドは次のように実行できます：

```bash
# ヘルプを表示
./src/interface/cli.ts --help

# メタスキーマを登録
./src/interface/cli.ts register ./data/meta/String.meta.json

# その他のコマンド
./src/interface/cli.ts <コマンド> [引数...]
```

## エントリポイントの一元化

プロジェクト内の複数のエントリポイントは、一つの統合されたCLIインターフェース（`cli.ts`）に集約されています。これにより：

1. コマンドの呼び出しがシンプルになる
2. ヘルプとドキュメントが一元管理される
3. 依存関係の管理が改善される
4. 一貫したエラーハンドリングが可能になる

### 現在サポートされているサブコマンド

`cli.ts` は以下のサブコマンドをサポートしています：

- `register` - メタスキーマを登録
- `generate` - スキーマを生成
- `validate` - スキーマを検証
- `diagnose` - メタスキーマや設定ファイルを診断
- `list` - 登録済みのメタスキーマ一覧を表示
- `deps` - 型の依存関係を再帰的に表示
- `req-deps` - 要件間の依存関係を解析
- `req-to-function` - 要件から関数定義JSONを生成
- `req-gen` - 統一要件JSONの生成と管理
- `generate-types` - 統一要件から型スキーマを一括生成
