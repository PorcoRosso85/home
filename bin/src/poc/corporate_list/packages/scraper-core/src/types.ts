/**
 * Core type definitions for scraper-core package
 * 既存の型との互換性を維持しながら関数型スタイルで実装
 */

import { type Browser } from 'playwright-core'

/** Browser configuration type - 既存のScraperConfig['browser']と互換 */
export type BrowserConfig = {
  /** User agent string for HTTP requests */
  userAgent: string
  /** Page load timeout in milliseconds */
  timeout: number
  /** Wait time after page load in milliseconds */
  waitTime: number
  /** Browser launch arguments */
  launchArgs: string[]
}

/** スクレイピング結果の型 - 既存の型と完全互換 */
export type ScrapedResult = {
  source: string
  company_name: string | null
  title: string
  url: string
  scraped_at: string
}

/** スクレイパーインターフェース（関数型） */
export type IScraper = {
  scrape: (browser: Browser, keyword: string) => Promise<ScrapedResult[]>
  getName: () => string
}

/** Browser管理の関数型インターフェース */
export type BrowserManager = {
  launch: () => Promise<Browser>
  close: () => Promise<void>
  isLaunched: () => boolean
}

/** スクレイピング設定の型（既存の型互換） */
export type ScrapeConfig = {
  maxTitleLength: number
  timeout: number
  waitTime: number
  userAgent: string
}

/** Browser設定のデフォルト値 */
export const DEFAULT_BROWSER_CONFIG: BrowserConfig = {
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  timeout: 30000,
  waitTime: 3000,
  launchArgs: ['--no-sandbox', '--disable-setuid-sandbox']
}