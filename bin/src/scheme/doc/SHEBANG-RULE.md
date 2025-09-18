# Shebang ルール

このドキュメントでは、/home/nixos/scheme プロジェクトで使用される Shebang のルールを説明します。

## 標準 Shebang ルール

プロジェクト内の実行可能なTypeScriptファイルでは、以下の Shebang 行を使用します：

```
#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run [必要な権限フラグ]
```

### 説明

- `#!/usr/bin/env -S` - 環境変数を使用して複数の引数を持つコマンドを実行可能にする
- `nix shell nixpkgs#deno --command` - Nix パッケージマネージャを使用して Deno を一時的にシェル環境にインストールし、コマンドを実行
- `deno run` - Deno ランタイムでスクリプトを実行
- `[必要な権限フラグ]` - スクリプトが必要とする Deno の権限フラグ（--allow-read, --allow-write, --allow-run など）

### 一般的な権限フラグの組み合わせ

スクリプトの目的に応じて、以下の権限フラグを組み合わせて使用します：

- ファイル読み取り専用: `--allow-read`
- ファイル読み書き: `--allow-read --allow-write`
- 外部コマンド実行: `--allow-run`
- ファイル操作と外部コマンド実行: `--allow-read --allow-write --allow-run`

## 例

1. ファイル読み書きのみを行うスクリプト：

```
#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write
```

2. 外部コマンドも実行するスクリプト：

```
#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run
```

## 適用されているファイル

プロジェクト内では、以下のファイルにこのShebangルールが適用されています：

1. `demo.generate.ts` - 各型の生成デモ用スクリプト
2. `run_deps_test.ts` - 依存関係解析テスト用スクリプト
3. `requirements-generator.ts` - 要件生成スクリプト
4. `requirements-deps.ts` - 要件依存関係解析スクリプト
5. `requirements-to-function.ts` - 要件から関数定義JSON生成スクリプト

## 例外のファイル

標準ルールの例外となるファイルがある場合は、ここに記載します。

## 注意事項

- スクリプトファイルの実行権限を設定するのを忘れないでください：
  ```
  chmod +x your-script.ts
  ```
- 必要最小限の権限のみを付与するようにしてください（最小権限の原則）
- スクリプトの冒頭に必ずこのShebangルールを適用してください
