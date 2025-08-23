# @corporate-list/scraper-prtimes

PR Times固有のスクレイピング機能を提供する関数型パッケージ

## 概要

`@corporate-list/scraper-core`をベースに、PR Times固有のHTML解析と記事抽出機能を実装したパッケージです。関数型プログラミングのアプローチを採用し、再利用可能で組み合わせ可能な関数を提供します。

## インストール

```bash
npm install @corporate-list/scraper-prtimes
```

## 基本的な使用方法

### スクレイパーの作成と実行

```typescript
import { createBrowserManager, DEFAULT_BROWSER_CONFIG } from '@corporate-list/scraper-core'
import { createDefaultPRTimesScraper } from '@corporate-list/scraper-prtimes'

// ブラウザ管理の設定
const browserManager = createBrowserManager(DEFAULT_BROWSER_CONFIG)

// PR Timesスクレイパーの作成
const scraper = createDefaultPRTimesScraper(DEFAULT_BROWSER_CONFIG)

// スクレイピング実行
const browser = await browserManager.launch()
const results = await scraper.scrape(browser, 'AI')
await browserManager.close()

console.log(`取得した記事数: ${results.length}`)
```

### カスタム設定でのスクレイパー作成

```typescript
import { createPRTimesScraper } from '@corporate-list/scraper-prtimes'

const customScraper = createPRTimesScraper(
  {
    userAgent: 'Custom User Agent',
    timeout: 45000,
    waitTime: 5000,
    launchArgs: ['--no-sandbox']
  },
  150 // タイトル最大文字数
)
```

## API Reference

### Constants

- `PRTIMES_CONFIG`: PR Timesの基本設定
- `ARTICLE_SELECTORS`: 記事要素検索用セレクター
- `TITLE_SELECTORS`: タイトル要素検索用セレクター  
- `COMPANY_SELECTORS`: 企業名要素検索用セレクター

### Parser Functions

#### `parsePRTimesArticles(maxTitleLength: number)`

HTML documentからPR Times記事を解析する関数を返します。

```typescript
const parser = parsePRTimesArticles(100)
const articles = parser(document) // Browser contextで実行
```

#### `extractCompanyName(text: string): string | null`

テキストから企業名を抽出します。

```typescript
const company = extractCompanyName('株式会社テスト')
// => '株式会社テスト'
```

#### `cleanTitle(title: string, maxLength?: number): string`

タイトルをクリーニングし、最大文字数で切り詰めます。

```typescript
const title = cleanTitle('  長いタイトル  ', 10)
// => '長いタイト'
```

### Scraper Functions

#### `createPRTimesScraper(config: BrowserConfig, maxTitleLength?: number)`

カスタム設定でPR Timesスクレイパーを作成します。

#### `createDefaultPRTimesScraper(config: BrowserConfig)`

デフォルト設定でPR Timesスクレイパーを作成します。

## 型定義

### ArticleData

```typescript
type ArticleData = {
  title: string
  url: string
  companyText: string
}
```

## 特徴

### 関数型アプローチ

- **純粋関数**: 副作用のない予測可能な関数
- **関数合成**: `scraper-core`の関数を組み合わせて機能を構築
- **高階関数**: 設定を受け取り、特定の機能を持つ関数を返す

### ロバストな抽出ロジック

- **複数セレクター**: 優先順位付きでHTML要素を検索
- **フォールバック機能**: 主要セレクターが失敗時の代替抽出
- **エラーハンドリング**: 失敗時の適切な処理とリトライ

### テスト可能性

- **純粋関数**: 単体テストが容易
- **依存性注入**: モック化しやすい設計
- **分離された責務**: 各関数が明確な単一責任を持つ

## 実装の詳細

### HTML解析戦略

1. **優先セレクター**: `article.list-article`, `.article-box`など
2. **フォールバック**: PR Timesリンクの直接抽出
3. **データクリーニング**: タイトル長制限、企業名抽出

### エラー処理

- ページ作成失敗: 空配列を返す
- ナビゲーション失敗: ページを閉じて空配列を返す  
- 抽出エラー: ログ出力後、空配列を返す

## 依存関係

- `@corporate-list/scraper-core`: 基本スクレイピング機能
- `playwright-core`: ブラウザ操作

## ライセンス

MIT