/**
 * scraper-core エントリーポイント
 * すべての機能を関数型スタイルでエクスポート
 */

// Types
export type {
  BrowserConfig,
  ScrapedResult,
  IScraper,
  BrowserManager,
  ScrapeConfig
} from './types.js'

export {
  DEFAULT_BROWSER_CONFIG
} from './types.js'

// Browser management (functional approach)
export {
  getChromiumPath,
  createBrowserLauncher,
  createBrowserManager,
  withBrowser,
  createMockBrowser
} from './browser/manager.js'

// Scraper base functions
export {
  createPageFactory,
  createNavigator,
  extractBasicData,
  createBaseScraper,
  withKeywords,
  withRetry,
  createMockScraper
} from './scraper/base.js'