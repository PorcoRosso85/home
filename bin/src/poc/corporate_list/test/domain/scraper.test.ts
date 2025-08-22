/**
 * Tests for the domain scraper layer
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { BaseScraper } from '../../src/domain/scraper.js'
import { PRTimesScraper } from '../../src/domain/scrapers/prtimes-scraper.js'
import { ScraperFactory } from '../../src/domain/scraper-factory.js'
import type { Article, ScrapeConfig } from '../../src/domain/types.js'
import { Page } from 'playwright-core'

// Mock configuration
const mockConfig: ScrapeConfig = {
  maxTitleLength: 100,
  timeout: 5000,
  waitTime: 1000,
  userAgent: 'test-agent'
}

// Mock concrete scraper for testing abstract base class
class MockScraper extends BaseScraper {
  constructor() {
    super('MOCK_SOURCE', 'https://example.com/search?q=', mockConfig)
  }

  protected buildSearchUrl(keyword: string): string {
    return `${this.baseUrl}${encodeURIComponent(keyword)}`
  }

  protected async extractArticles(page: Page): Promise<Article[]> {
    // Mock implementation
    return [
      {
        title: 'Test Article 1',
        url: 'https://example.com/article1',
        companyText: '株式会社テスト企業'
      },
      {
        title: 'Test Article 2',
        url: 'https://example.com/article2', 
        companyText: 'サンプル企業株式会社'
      }
    ]
  }
}

test('Domain Scraper Layer', async (t) => {
  await t.test('BaseScraper', async (t) => {
    await t.test('should construct with correct properties', () => {
      const scraper = new MockScraper()
      assert.strictEqual(scraper['sourceName'], 'MOCK_SOURCE')
      assert.strictEqual(scraper['baseUrl'], 'https://example.com/search?q=')
      assert.deepStrictEqual(scraper['config'], mockConfig)
    })

    await t.test('should build search URL correctly', () => {
      const scraper = new MockScraper()
      const url = scraper['buildSearchUrl']('テスト')
      assert.strictEqual(url, 'https://example.com/search?q=%E3%83%86%E3%82%B9%E3%83%88')
    })
  })

  await t.test('PRTimesScraper', async (t) => {
    await t.test('should construct with PR Times configuration', () => {
      const scraper = new PRTimesScraper(mockConfig)
      assert.strictEqual(scraper['sourceName'], 'PR_TIMES')
      assert.strictEqual(scraper['baseUrl'], 'https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word=')
    })

    await t.test('should build PR Times search URL correctly', () => {
      const scraper = new PRTimesScraper(mockConfig)
      const url = scraper['buildSearchUrl']('資金調達')
      assert.strictEqual(url, 'https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word=%E8%B3%87%E9%87%91%E8%AA%BF%E9%81%94')
    })
  })

  await t.test('ScraperFactory', async (t) => {
    await t.test('should create PR Times scraper', () => {
      const scraper = ScraperFactory.createPRTimesScraper(mockConfig)
      assert.ok(scraper instanceof PRTimesScraper)
      assert.strictEqual(scraper['sourceName'], 'PR_TIMES')
    })

    await t.test('should return all available scrapers', () => {
      const scrapers = ScraperFactory.getAllScrapers(mockConfig)
      assert.strictEqual(scrapers.length, 1)
      assert.ok(scrapers[0] instanceof PRTimesScraper)
    })
  })
})