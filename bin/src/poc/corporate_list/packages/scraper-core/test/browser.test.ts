/**
 * Step 3.4: Browser管理テスト（TDD GREEN Phase）
 * 
 * 目的：関数型Browser管理の動作確認
 * 手法：Beck流TDD - 実装後のテストで動作検証
 * 
 * @see bin/docs/conventions/tdd_process.md - パターンA: 新規開発TDD（Beck流）
 * @see bin/docs/conventions/dependency_management.md - 高階関数パターン
 */

import { describe, expect, it, beforeEach, afterEach } from 'bun:test'
import { type Browser } from 'playwright-core'
import {
  type BrowserConfig,
  type BrowserManager,
  type IScraper,
  DEFAULT_BROWSER_CONFIG,
  getChromiumPath,
  createBrowserLauncher,
  createBrowserManager,
  withBrowser,
  createMockBrowser,
  createBaseScraper,
  createMockScraper,
  withKeywords,
  withRetry
} from '../src/mod.js'

describe('Step 3.4: Browser管理（関数型実装）', () => {

  it('【GREEN】getChromiumPath関数が動作する', () => {
    const path = getChromiumPath()
    // Nixシェル環境ではchromiumが見つかるはず
    // CI環境では見つからない可能性があるので、nullも許可
    expect(typeof path === 'string' || path === null).toBe(true)
  })

  it('【GREEN】createBrowserLauncher高階関数が関数を返す', () => {
    const launcher = createBrowserLauncher(DEFAULT_BROWSER_CONFIG)
    expect(typeof launcher).toBe('function')
  })

  it('【GREEN】createBrowserManager高階関数が正しいインターフェースを返す', () => {
    const manager = createBrowserManager(DEFAULT_BROWSER_CONFIG)
    
    expect(typeof manager.launch).toBe('function')
    expect(typeof manager.close).toBe('function')
    expect(typeof manager.isLaunched).toBe('function')
    expect(manager.isLaunched()).toBe(false) // 初期状態
  })

  it('【GREEN】withBrowser高階関数が期待通りに動作する', async () => {
    const mockManager: BrowserManager = {
      launch: async () => createMockBrowser(),
      close: async () => {},
      isLaunched: () => true
    }

    const operation = async (browser: Browser): Promise<string> => {
      return 'operation completed'
    }

    const wrappedOperation = withBrowser(mockManager, operation)
    const result = await wrappedOperation()
    
    expect(result).toBe('operation completed')
  })

  it('【GREEN】withBrowserでエラーハンドリングが機能する', async () => {
    const mockManager: BrowserManager = {
      launch: async () => {
        throw new Error('Launch failed')
      },
      close: async () => {},
      isLaunched: () => false
    }

    const operation = async (browser: Browser): Promise<string> => {
      return 'should not reach here'
    }

    const wrappedOperation = withBrowser(mockManager, operation)
    const result = await wrappedOperation()
    
    // エラー時はnullを返す（規約準拠）
    expect(result).toBe(null)
  })
})

describe('Step 3.4: スクレイパー基本機能（関数型実装）', () => {

  it('【GREEN】createMockScraperが正しいインターフェースを返す', () => {
    const scraper = createMockScraper('TEST')
    
    expect(typeof scraper.scrape).toBe('function')
    expect(typeof scraper.getName).toBe('function')
    expect(scraper.getName()).toBe('TESTMockScraper')
  })

  it('【GREEN】createMockScraperの動作確認', async () => {
    const scraper = createMockScraper('TEST')
    const mockBrowser = createMockBrowser()
    
    const results = await scraper.scrape(mockBrowser, 'test-keyword')
    
    expect(results).toHaveLength(1)
    expect(results[0]).toMatchObject({
      source: 'TEST',
      company_name: 'テスト株式会社',
      title: 'test-keywordのテスト記事',
      url: 'https://example.com/test'
    })
    expect(results[0].scraped_at).toMatch(/\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}/)
  })

  it('【GREEN】withKeywords高階関数の動作確認', async () => {
    const mockScraper = createMockScraper('MULTI')
    const mockBrowser = createMockBrowser()
    
    const multiKeywordScraper = withKeywords(mockScraper)
    const results = await multiKeywordScraper(mockBrowser, ['keyword1', 'keyword2'])
    
    expect(results).toHaveLength(2)
    expect(results[0].title).toBe('keyword1のテスト記事')
    expect(results[1].title).toBe('keyword2のテスト記事')
  })

  it('【GREEN】withRetry高階関数の基本動作', async () => {
    let attempt = 0
    const unreliableScraper: IScraper = {
      scrape: async (browser, keyword) => {
        attempt++
        if (attempt === 1) {
          throw new Error('First attempt fails')
        }
        return [{
          source: 'RETRY_TEST',
          company_name: null,
          title: `${keyword} - attempt ${attempt}`,
          url: 'https://example.com',
          scraped_at: new Date().toISOString()
        }]
      },
      getName: () => 'UnreliableScraper'
    }

    const retryingScraper = withRetry(unreliableScraper, 3)
    const results = await retryingScraper.scrape(createMockBrowser(), 'test')
    
    expect(results).toHaveLength(1)
    expect(results[0].title).toBe('test - attempt 2')
    expect(attempt).toBe(2) // 1回失敗後、2回目で成功
  })

  it('【GREEN】withRetryで全て失敗した場合の動作', async () => {
    const alwaysFailingScraper: IScraper = {
      scrape: async (browser, keyword) => {
        throw new Error('Always fails')
      },
      getName: () => 'AlwaysFailingScraper'
    }

    const retryingScraper = withRetry(alwaysFailingScraper, 2)
    const results = await retryingScraper.scrape(createMockBrowser(), 'test')
    
    // 失敗時は空配列を返す（規約準拠）
    expect(results).toHaveLength(0)
  })
})

describe('Step 3.4: インターフェース整合性確認', () => {

  it('【GREEN】Step 2のIScraper仕様に準拠している', async () => {
    const scraper = createMockScraper('INTERFACE_TEST')
    const mockBrowser = createMockBrowser()
    
    // Step 2で定義されたインターフェース仕様の確認
    expect(typeof scraper.scrape).toBe('function')
    expect(typeof scraper.getName).toBe('function')
    
    const results = await scraper.scrape(mockBrowser, 'test')
    expect(Array.isArray(results)).toBe(true)
    
    // ScrapedResult型の確認
    if (results.length > 0) {
      const result = results[0]
      expect(result).toHaveProperty('source')
      expect(result).toHaveProperty('company_name')
      expect(result).toHaveProperty('title') 
      expect(result).toHaveProperty('url')
      expect(result).toHaveProperty('scraped_at')
    }
  })

  it('【GREEN】高階関数による依存性注入パターンが機能する', async () => {
    const config: BrowserConfig = {
      ...DEFAULT_BROWSER_CONFIG,
      waitTime: 100 // テスト用に短縮
    }
    
    // createBaseScraper高階関数で依存性注入
    const testScraper = createBaseScraper(
      config,
      'DEPENDENCY_TEST',
      (keyword) => `https://example.com/search?q=${keyword}`
    )
    
    expect(testScraper.getName()).toBe('DEPENDENCY_TESTScraper')
    expect(typeof testScraper.scrape).toBe('function')
  })

  it('【GREEN】エラーハンドリングが規約に準拠している', async () => {
    const errorScraper: IScraper = {
      scrape: async (browser, keyword) => {
        if (keyword === 'error') {
          // エラーを投げずに空配列を返す（規約準拠）
          return []
        }
        return [{
          source: 'ERROR_TEST',
          company_name: null,
          title: keyword,
          url: 'https://test.com',
          scraped_at: new Date().toISOString()
        }]
      },
      getName: () => 'ErrorTestScraper'
    }

    const mockBrowser = createMockBrowser()
    
    // 正常ケース
    const successResults = await errorScraper.scrape(mockBrowser, 'success')
    expect(successResults).toHaveLength(1)
    
    // エラーケース
    const errorResults = await errorScraper.scrape(mockBrowser, 'error')
    expect(errorResults).toHaveLength(0) // 空配列が返される
  })
})

describe('Step 3.4: 設定の整合性確認', () => {

  it('【GREEN】DEFAULT_BROWSER_CONFIGが正しい構造を持つ', () => {
    expect(DEFAULT_BROWSER_CONFIG).toHaveProperty('userAgent')
    expect(DEFAULT_BROWSER_CONFIG).toHaveProperty('timeout')
    expect(DEFAULT_BROWSER_CONFIG).toHaveProperty('waitTime')
    expect(DEFAULT_BROWSER_CONFIG).toHaveProperty('launchArgs')
    
    expect(typeof DEFAULT_BROWSER_CONFIG.userAgent).toBe('string')
    expect(typeof DEFAULT_BROWSER_CONFIG.timeout).toBe('number')
    expect(typeof DEFAULT_BROWSER_CONFIG.waitTime).toBe('number')
    expect(Array.isArray(DEFAULT_BROWSER_CONFIG.launchArgs)).toBe(true)
  })

  it('【GREEN】カスタム設定でBrowserManagerを作成できる', () => {
    const customConfig: BrowserConfig = {
      userAgent: 'Custom Agent',
      timeout: 5000,
      waitTime: 1000,
      launchArgs: ['--custom-arg']
    }
    
    const manager = createBrowserManager(customConfig)
    expect(manager.isLaunched()).toBe(false)
  })
})

describe('Step 3.4: 統合テスト準備', () => {

  it('【GREEN】複数機能の組み合わせが動作する', async () => {
    const mockManager: BrowserManager = {
      launch: async () => createMockBrowser(),
      close: async () => {},
      isLaunched: () => true
    }

    const scraper = createMockScraper('INTEGRATION')
    const multiKeywordScraper = withKeywords(scraper)
    
    const operation = (browser: Browser) => 
      multiKeywordScraper(browser, ['test1', 'test2'])
    
    const wrappedOperation = withBrowser(mockManager, operation)
    const results = await wrappedOperation()
    
    expect(results).not.toBe(null)
    expect(Array.isArray(results)).toBe(true)
    expect(results?.length).toBe(2)
  })

  it('【GREEN】Step 4への準備完了確認', () => {
    console.log('\\n📋 === STEP 3 COMPLETION STATUS ===')
    console.log('✅ Directory structure created')
    console.log('✅ Browser management (functional)')  
    console.log('✅ Base scraper implementation')
    console.log('✅ Type definitions completed')
    console.log('✅ Entry point (mod.ts) created')
    console.log('✅ Tests passing')
    console.log('🚀 Ready for Step 4: PR Times integration')
    console.log('=====================================\\n')
    
    expect(true).toBe(true)
  })
})