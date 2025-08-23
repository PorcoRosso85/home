/**
 * Scraper client - 依存性注入層
 * 新パッケージからスクレイパーを取得する責務
 */

// 外部パッケージから読み込み（flake.nixで管理）
import { createPRTimesScraper } from '../../../scrape_ts/scraper-prtimes/src/mod.js'
import type { IScraper, BrowserConfig, ScrapeConfig } from '../../../scrape_ts/scraper-core/src/mod.js'

/**
 * ScrapeConfigをBrowserConfigに変換する
 */
function convertToBrowserConfig(config: ScrapeConfig): BrowserConfig {
  return {
    userAgent: config.userAgent,
    timeout: config.timeout,
    waitTime: config.waitTime,
    launchArgs: ['--no-sandbox', '--disable-setuid-sandbox']
  }
}

/**
 * PR Timesスクレイパーを作成する
 */
export function createPRTimesScraperClient(config: ScrapeConfig): IScraper {
  const browserConfig = convertToBrowserConfig(config)
  return createPRTimesScraper(browserConfig, config.maxTitleLength)
}