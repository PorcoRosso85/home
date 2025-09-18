# URL Crawler POC

URLからリンクを抽出するクローラーツール。sitefetchのクロール部分を抽出してDeno実装。

## 規約遵守

- **TDD**: モックを使わず実際のHTTPサーバーでテスト
- **命名規則**: `*.test.ts` for TypeScript
- **Linter/Formatter**: Deno fmt/lint

## 使用方法

```bash
# CLI実行
nix run . -- https://example.com

# 開発環境
nix develop

# コマンド
nix run .#format    # コード整形
nix run .#lint      # Lint実行
nix run .#test      # テスト実行
```

## テスト

統合テスト（`crawl_integration.test.ts`）では実際のHTTPサーバーを起動してテスト。モックは使用しない。