/**
 * Integration Test - 外部パッケージ統合確認
 */

import { describe, expect, it } from 'bun:test'
import { createPRTimesScraperClient } from '../src/infrastructure/scraper-client.js'
import type { ScrapeConfig } from '../../../scrape_ts/scraper-core/src/mod.js'

describe('External Package Integration', () => {
  it('PR Timesスクレイパーがインスタンス化できる', () => {
    const config: ScrapeConfig = {
      maxTitleLength: 100,
      timeout: 30000,
      waitTime: 2000,
      userAgent: 'Test Agent'
    }
    
    const scraper = createPRTimesScraperClient(config)
    
    // スクレイパーが正しいインターフェースを持つことを確認
    expect(scraper).toBeDefined()
    expect(scraper.scrape).toBeDefined()
    expect(scraper.getName).toBeDefined()
    expect(typeof scraper.scrape).toBe('function')
    expect(typeof scraper.getName).toBe('function')
    expect(scraper.getName()).toBe('PRTimesScraper')
  })
  
  it('変換関数が正しく動作する', () => {
    const config: ScrapeConfig = {
      maxTitleLength: 50,
      timeout: 10000,
      waitTime: 1000,
      userAgent: 'Mozilla/5.0'
    }
    
    // 複数のインスタンスを作成してもエラーにならない
    const scraper1 = createPRTimesScraperClient(config)
    const scraper2 = createPRTimesScraperClient(config)
    
    expect(scraper1).not.toBe(scraper2) // 別インスタンス
    expect(scraper1.getName()).toBe(scraper2.getName()) // 同じ名前
  })
})