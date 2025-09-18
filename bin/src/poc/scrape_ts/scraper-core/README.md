# @corporate-list/scraper-core

スクレイパー分離プロジェクトのStep 3で作成されたコア機能パッケージ。

## 特徴

- **関数型スタイル**: クラスベースOOPを排除し、関数型プログラミングで実装
- **高階関数パターン**: 依存性注入を高階関数で実現
- **エラーハンドリング**: throwせず、空配列やnullを返すアプローチ
- **テスト駆動**: Beck流TDDでStep 2のインターフェース仕様を実装

## 主要機能

### Browser管理（関数型）

```typescript
import { createBrowserManager, DEFAULT_BROWSER_CONFIG } from '@corporate-list/scraper-core'

const manager = createBrowserManager(DEFAULT_BROWSER_CONFIG)
const browser = await manager.launch()
// 使用後
await manager.close()
```

### 基本スクレイパー作成

```typescript
import { createBaseScraper } from '@corporate-list/scraper-core'

const scraper = createBaseScraper(
  DEFAULT_BROWSER_CONFIG,
  'PR_TIMES',
  (keyword) => `https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word=${keyword}`
)

const results = await scraper.scrape(browser, '資金調達')
```

### 高階関数コンポーザー

```typescript
import { withKeywords, withRetry, withBrowser } from '@corporate-list/scraper-core'

// 複数キーワード対応
const multiScraper = withKeywords(scraper)

// リトライ機能付き
const reliableScraper = withRetry(scraper, 3)

// Browser管理統合
const operation = withBrowser(manager, (browser) => 
  multiScraper(browser, ['シリーズA', '資金調達'])
)
```

## 設計原則

### 1. 関数型スタイル
- クラス定義は禁止
- 高階関数による依存性注入
- イミュータブルなデータ操作

### 2. エラーハンドリング
- 例外を投げず、安全な値を返す
- `null` または空配列でエラー状態を表現
- ログ出力で詳細情報を提供

### 3. 再利用性
- 関数の組み合わせで機能を構築
- 設定の外部化
- インターフェースの統一

## テスト

```bash
# 全テスト実行
bun test

# ウォッチモード
bun test:watch

# 型チェック
bun run type-check
```

## 次のステップ

Step 4では、このコア機能を使用してPR Timesスクレイパーの具体的実装を行います。

## ディレクトリ構造

```
packages/scraper-core/
├── src/
│   ├── browser/
│   │   └── manager.ts     # Browser管理（関数型）
│   ├── scraper/
│   │   └── base.ts        # 基本スクレイパー（関数型）
│   ├── types.ts           # 型定義
│   └── mod.ts             # エントリーポイント
├── test/
│   └── browser.test.ts    # 統合テスト
├── package.json
├── tsconfig.json
└── README.md
```