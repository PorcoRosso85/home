#!/usr/bin/env node
/**
 * 企業リード収集スクレイパー（最小構成）
 * 要件: データの抽出精度は60%でよい。まずリストを溜めるスピードを優先
 */

import { getConfig, type ScraperConfig } from './variables.js'
import { createBrowserManager } from './infrastructure/browser.js'
import { ScraperFactory } from './domain/scraper-factory.js'
import type { ScrapedResult, ScrapeConfig } from './domain/types.js'

// ========== 1. 設定 ==========
// Configuration is now loaded from variables.ts with environment variable support
const config: ScraperConfig = getConfig()

// Convert config to domain-specific config
const scrapeConfig: ScrapeConfig = {
  maxTitleLength: config.extraction.maxTitleLength,
  timeout: config.browser.timeout,
  waitTime: config.browser.waitTime,
  userAgent: config.browser.userAgent
}

// ========== 2. メイン処理 ==========
async function main(): Promise<void> {
  console.log('🚀 Starting Lead Scraper (No DB version)')
  console.log('==================================================')
  
  const browserManager = createBrowserManager(config.browser)
  
  try {
    // ブラウザ起動
    const browser = await browserManager.launch()
    
    // スクレイピング実行
    const allResults: ScrapedResult[] = []
    const scraper = ScraperFactory.createPRTimesScraper(scrapeConfig)
    
    for (const keyword of config.searchKeywords) {
      const results = await scraper.scrape(browser, keyword)
      allResults.push(...results)
    }
    
    // 結果をJSON形式で出力（後でDB保存する際に使える）
    console.log('\n📊 Results:')
    console.log('==================================================')
    console.log(JSON.stringify(allResults, null, 2))
    
    // サマリー
    console.log('\n==================================================')
    console.log(`📈 Total: ${allResults.length} articles found`)
    
    // 企業名抽出の成功率を表示
    const withCompany = allResults.filter(r => r.company_name).length
    const successRate = Math.round((withCompany / allResults.length) * 100)
    console.log(`🏢 Company extraction rate: ${successRate}% (${withCompany}/${allResults.length})`)
    
  } catch (error: any) {
    console.error('💥 Fatal error:', error.message)
    process.exit(1)
  } finally {
    await browserManager.close()
  }
}

// 実行
main().catch((error: any) => {
  console.error('💥 Unhandled error:', error)
  process.exit(1)
})