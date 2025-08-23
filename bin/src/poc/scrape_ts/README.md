# Scraper Packages - 汎用スクレイピングツール群

## 概要

企業データ収集のための汎用スクレイピングパッケージ群。
Nix Flakeとして提供され、他プロジェクトから簡単に利用可能。

## パッケージ構成

- **scraper-core**: 汎用スクレイピング基盤
  - Browser管理（Playwright）
  - 基本スクレイパー機能
  - 高階関数による拡張可能な設計

- **scraper-prtimes**: PR Times固有実装
  - PR Times記事の解析
  - 企業名抽出ロジック
  - 120記事取得の実績

## 使用方法

### 他のFlakeから利用

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    scraper.url = "path:/home/nixos/bin/src/poc/scrape_ts";
  };
  
  outputs = { self, nixpkgs, scraper }:
    let
      scraperCore = scraper.packages.${system}.scraper-core;
      scraperPrtimes = scraper.packages.${system}.scraper-prtimes;
    in
    {
      # 使用例
      devShells.default = pkgs.mkShell {
        buildInputs = [ scraperCore scraperPrtimes ];
      };
    };
}
```

### TypeScript/JavaScriptから利用

```typescript
// scraper-coreの利用
import { createBrowserManager, createScraper } from 'scraper-core';

const browserManager = createBrowserManager(config);
const browser = await browserManager.launch();

// scraper-prtimesの利用
import { createPRTimesScraper } from 'scraper-prtimes';

const scraper = createPRTimesScraper(browserConfig, maxTitleLength);
const results = await scraper.scrape(browser, 'キーワード');
```

## アーキテクチャ

### 関数型設計
- クラスベースOOP禁止
- 高階関数による依存性注入
- 純粋関数の組み合わせ

### エラーハンドリング
- 例外を投げない（throwしない）
- 空配列やnullを返す
- 呼び出し側で適切に処理

## 開発

```bash
# 開発環境に入る
nix develop

# テスト実行
nix run .#test

# パッケージビルド
nix build .#scraper-core
nix build .#scraper-prtimes
```

## ライセンス

MIT