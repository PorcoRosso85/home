# Email Archive POC - Wrangler Only Edition

## 概要

Node.js/Deno依存を完全に排除し、Wranglerのみで動作するEmail Archive POCです。

## 変更点

1. **flake.nix**: Node.js/Denoを削除、Wranglerのみ使用
2. **src/index.ts**: TypeScriptで実装、外部依存なし（インメモリストレージ）
3. **wrangler.toml**: TypeScriptエントリポイントに変更
4. **package.json**: 不要（Wranglerが直接TypeScriptを実行）

## 使用方法

```bash
# 開発環境に入る
nix develop

# 開発サーバー起動
nix run .#wrangler-dev

# テスト実行
nix run .#wrangler-test

# アーキテクチャ確認
nix run .#demo
```

## テストエンドポイント

- `/__health` - ヘルスチェック
- `/__email` - メール送信テスト（POST）
- `/__storage` - ストレージ内容確認（GET）

## 特徴

- **Zero Dependencies**: npm/node_modules不要
- **Pure TypeScript**: Wranglerのネイティブサポート活用
- **In-Memory Storage**: テスト用のシンプルな実装
- **Nix Integration**: 再現可能な開発環境

## 今後の拡張

実際のS3統合が必要な場合は、Cloudflare WorkersのR2やDurable Objectsの使用を検討してください。