# CLIコマンド 移行ガイド

このドキュメントでは、schemeプロジェクトの新しいCLI構造への移行方法について説明します。

## 移行の背景

プロジェクトの開発が進むにつれて、複数のCLIエントリポイントが存在するようになり、コマンド実行が複雑化してきました。この問題を解決するため、すべてのコマンドを統合した単一のエントリポイント `cli.ts` を導入しました。

## 主な変更点

1. **統合されたエントリポイント**
   - すべてのコマンドは `/home/nixos/scheme/src/interface/cli.ts` から実行可能になりました
   - 以前の個別のコマンドはラッパーコマンドとして統合されています

2. **統一された引数処理**
   - すべてのコマンドで一貫した引数パターンを使用
   - ヘルプメッセージが標準化されました

3. **実行権限の設定**
   - CLI実行には適切な権限設定が必要です
   - 実行権限が不足している場合は以下のコマンドで設定してください：
     ```bash
     chmod +x /home/nixos/scheme/src/interface/cli.ts
     ```

## 旧コマンドから新コマンドへの対応

| 旧コマンド | 新コマンド |
|------------|------------|
| `./src/interface/cliController.ts register [args]` | `./src/interface/cli.ts register [args]` |
| `./src/interface/cliController.ts generate [args]` | `./src/interface/cli.ts generate [args]` |
| `./src/interface/cliController.ts validate [args]` | `./src/interface/cli.ts validate [args]` |
| `./src/interface/cliController.ts diagnose [args]` | `./src/interface/cli.ts diagnose [args]` |
| `./src/interface/cliController.ts list` | `./src/interface/cli.ts list` |
| `./src/interface/cliController.ts deps [args]` | `./src/interface/cli.ts deps [args]` |
| `./src/interface/cliController.ts req-deps [args]` | `./src/interface/cli.ts req-deps [args]` |
| `./src/interface/cliController.ts req-to-function [args]` | `./src/interface/cli.ts req-to-function [args]` |
| `./src/interface/requirements-generator.ts [args]` | `./src/interface/cli.ts req-gen [args]` |
| `./src/interface/generate-types-from-requirements.ts [args]` | `./src/interface/cli.ts generate-types [args]` |

## 移行手順

1. **実行権限の付与**
   ```bash
   chmod +x /home/nixos/scheme/src/interface/cli.ts
   ```

2. **コマンド実行の確認**
   ```bash
   ./src/interface/cli.ts --help
   ```

3. **スクリプトやビルド設定の更新**
   - 既存のスクリプトやビルド設定を新しいコマンド形式に更新します
   - ドキュメントやREADMEファイルの例を更新します

## 移行期間中の注意事項

- 移行期間中（2025年4月末まで）は、旧形式のコマンドも引き続きサポートされます
- 新規の開発では、新しいCLI形式を使用してください
- 2025年5月以降は、旧コマンド形式のサポートが終了する予定です

## トラブルシューティング

### 実行権限エラー
```
error: unable to execute './src/interface/cli.ts': Permission denied
```

**解決策**: ファイルに実行権限を付与します
```bash
chmod +x /home/nixos/scheme/src/interface/cli.ts
```

### コマンドが見つからない
```
未知のコマンド: [コマンド名]
```

**解決策**: 正しいコマンド名を確認し、必要に応じて`--help`オプションでヘルプを表示します
```bash
./src/interface/cli.ts --help
```

### ファイルが見つからない
```
Error: ファイル '[パス]' が見つかりません
```

**解決策**: 正しいファイルパスを指定しているか確認してください。パスは相対パスではなく絶対パスで指定することをお勧めします。
