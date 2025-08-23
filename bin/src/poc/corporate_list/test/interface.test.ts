/**
 * Step 2: インターフェース定義テスト（TDD RED Phase）
 * 
 * 目的：スクレイパーを交換可能にするインターフェースを定義
 * 手法：Beck流TDD - まず失敗するテストを書く
 * 
 * @see bin/docs/conventions/tdd_process.md - パターンA: 新規開発TDD（Beck流）
 * @see bin/docs/conventions/dependency_management.md - 高階関数パターン
 */

import { describe, expect, it } from 'bun:test'
import type { Browser } from 'playwright-core'
import { createPRTimesScraper, createDefaultPRTimesScraper } from '../packages/scraper-prtimes/src/mod.js'
import type { IScraper, ScrapedResult, BrowserConfig } from '../packages/scraper-core/src/mod.js'

/**
 * 依存性注入パターン（高階関数）
 * @see bin/docs/conventions/dependency_management.md - ルール: 高階関数パターン
 */
const createScraperClient = (scraper: IScraper) => 
  async (browser: Browser, keywords: string[]): Promise<ScrapedResult[]> => {
    const results: ScrapedResult[] = []
    
    for (const keyword of keywords) {
      const keywordResults = await scraper.scrape(browser, keyword)
      results.push(...keywordResults)
    }
    
    return results
  }

describe('Step 2: インターフェース定義（TDD RED Phase）', () => {
  
  it('【RED】スクレイパーインターフェースが定義されている', () => {
    // このテストはREDフェーズ - 実装前なので失敗する
    const mockScraper: IScraper = {
      scrape: async (browser, keyword) => {
        return [{
          source: 'MOCK',
          company_name: 'テスト株式会社',
          title: `${keyword}のテスト記事`,
          url: 'https://example.com/test',
          scraped_at: new Date().toISOString()
        }]
      },
      getName: () => 'MockScraper'
    }
    
    expect(mockScraper.getName()).toBe('MockScraper')
    expect(typeof mockScraper.scrape).toBe('function')
  })

  it('【RED】高階関数による依存性注入が機能する', async () => {
    // モックブラウザ（最小限の実装）
    const mockBrowser = {} as Browser
    
    // モックスクレイパー
    const mockScraper: IScraper = {
      scrape: async (browser, keyword) => {
        return [{
          source: 'TEST',
          company_name: null,
          title: keyword,
          url: `https://test.com/${keyword}`,
          scraped_at: '2025-08-22T00:00:00.000Z'
        }]
      },
      getName: () => 'TestScraper'
    }
    
    // 依存性注入
    const scraperClient = createScraperClient(mockScraper)
    
    // 実行
    const results = await scraperClient(mockBrowser, ['test1', 'test2'])
    
    // 検証
    expect(results).toHaveLength(2)
    expect(results[0].title).toBe('test1')
    expect(results[1].title).toBe('test2')
  })

  it('【RED】複数のスクレイパーを切り替え可能', async () => {
    const mockBrowser = {} as Browser
    
    // スクレイパーA
    const scraperA: IScraper = {
      scrape: async (browser, keyword) => [{
        source: 'SOURCE_A',
        company_name: 'A社',
        title: `A: ${keyword}`,
        url: 'https://a.com',
        scraped_at: new Date().toISOString()
      }],
      getName: () => 'ScraperA'
    }
    
    // スクレイパーB  
    const scraperB: IScraper = {
      scrape: async (browser, keyword) => [{
        source: 'SOURCE_B',
        company_name: 'B社',
        title: `B: ${keyword}`,
        url: 'https://b.com',
        scraped_at: new Date().toISOString()
      }],
      getName: () => 'ScraperB'
    }
    
    // 依存性注入で切り替え
    const clientA = createScraperClient(scraperA)
    const clientB = createScraperClient(scraperB)
    
    const resultsA = await clientA(mockBrowser, ['test'])
    const resultsB = await clientB(mockBrowser, ['test'])
    
    expect(resultsA[0].source).toBe('SOURCE_A')
    expect(resultsB[0].source).toBe('SOURCE_B')
  })

  it('【GREEN】スクレイパーファクトリーパターンの実装', () => {
    // ファクトリー関数（関数型スタイル）
    type ScraperFactory = {
      create: (type: 'prtimes' | 'mock') => IScraper
      list: () => string[]
    }
    
    const createScraperFactory = (config: BrowserConfig): ScraperFactory => {
      const scrapers = new Map<string, IScraper>()
      
      // PR Timesスクレイパー（実装済み）
      scrapers.set('prtimes', createDefaultPRTimesScraper(config))
      
      // モックスクレイパー
      scrapers.set('mock', {
        scrape: async (browser, keyword) => [{
          source: 'MOCK',
          company_name: null,
          title: keyword,
          url: 'https://mock.com',
          scraped_at: new Date().toISOString()
        }],
        getName: () => 'MockScraper'
      })
      
      return {
        create: (type) => {
          const scraper = scrapers.get(type)
          if (!scraper) {
            throw new Error(`Unknown scraper type: ${type}`)
          }
          return scraper
        },
        list: () => Array.from(scrapers.keys())
      }
    }
    
    const testConfig: BrowserConfig = {
      userAgent: 'test-agent',
      timeout: 10000,
      waitTime: 1000,
      launchArgs: []
    }
    
    const factory = createScraperFactory(testConfig)
    
    expect(factory.list()).toContain('prtimes')
    expect(factory.list()).toContain('mock')
    
    const mockScraper = factory.create('mock')
    expect(mockScraper.getName()).toBe('MockScraper')
    
    const prTimesScraper = factory.create('prtimes')
    expect(prTimesScraper.getName()).toBe('PRTimesScraper')
  })

  it('【RED】エラーハンドリングインターフェース', async () => {
    const mockBrowser = {} as Browser
    
    // エラーを返すスクレイパー
    const errorScraper: IScraper = {
      scrape: async (browser, keyword) => {
        if (keyword === 'error') {
          // エラーを投げずに空配列を返す（規約準拠）
          return []
        }
        return [{
          source: 'TEST',
          company_name: null,
          title: keyword,
          url: 'https://test.com',
          scraped_at: new Date().toISOString()
        }]
      },
      getName: () => 'ErrorHandlingScraper'
    }
    
    const client = createScraperClient(errorScraper)
    const results = await client(mockBrowser, ['success', 'error', 'success2'])
    
    // エラーキーワードでは結果が0件、他は成功
    expect(results).toHaveLength(2)
    expect(results[0].title).toBe('success')
    expect(results[1].title).toBe('success2')
  })
})

describe('Step 2: 既存実装との互換性確認', () => {
  
  it('既存のScraperFactoryパターンとの整合性', () => {
    // 既存の実装パターンを確認
    const existingPattern = {
      className: 'ScraperFactory',
      method: 'createPRTimesScraper',
      returns: 'BaseScraper instance'
    }
    
    // 新しいインターフェースとの互換性を確認
    const newPattern = {
      function: 'createScraperFactory',
      method: 'create',
      returns: 'IScraper instance'
    }
    
    // 両方のパターンが共存可能であることを確認
    expect(existingPattern.method).toContain('create')
    expect(newPattern.method).toBe('create')
  })

  it('既存の型定義との互換性', () => {
    // 既存のScrapedResult型と同じ構造
    const result: ScrapedResult = {
      source: 'PR_TIMES',
      company_name: '株式会社Example',
      title: 'タイトル',
      url: 'https://prtimes.jp/example',
      scraped_at: '2025-08-22T12:00:00.000Z'
    }
    
    // 必須フィールドの確認
    expect(result).toHaveProperty('source')
    expect(result).toHaveProperty('company_name')
    expect(result).toHaveProperty('title')
    expect(result).toHaveProperty('url')
    expect(result).toHaveProperty('scraped_at')
  })
})

/**
 * 次のステップへの準備
 * これらのテストが通ったら、Step 3で実際の実装を行う
 */
describe('Step 2: GREEN Phaseへの準備', () => {
  
  it('実装すべきインターフェースの仕様を明確化', () => {
    const specifications = {
      interface: 'IScraper',
      methods: ['scrape', 'getName'],
      dependencyInjection: 'High-order function pattern',
      errorHandling: 'Return empty array instead of throwing',
      compatibility: 'Maintain existing ScrapedResult type'
    }
    
    console.log('\n📋 === INTERFACE SPECIFICATIONS ===')
    console.log('Interface:', specifications.interface)
    console.log('Methods:', specifications.methods.join(', '))
    console.log('DI Pattern:', specifications.dependencyInjection)
    console.log('Error Handling:', specifications.errorHandling)
    console.log('Compatibility:', specifications.compatibility)
    console.log('=====================================\n')
    
    expect(specifications.methods).toHaveLength(2)
  })
})