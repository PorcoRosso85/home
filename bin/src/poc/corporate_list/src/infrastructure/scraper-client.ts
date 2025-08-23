/**
 * Scraper client - 依存性注入層
 * 新パッケージからスクレイパーを取得する責務
 */

import { createPRTimesScraper } from '../../packages/scraper-prtimes/src/mod.js'
import type { IScraper, BrowserConfig, ScrapeConfig } from '../../packages/scraper-core/src/mod.js'

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