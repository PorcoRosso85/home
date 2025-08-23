/**
 * 基本スクレイパー実装（関数型）
 * 関数コンポジションで再利用可能なスクレイピング機能を提供
 * 
 * @see bin/docs/conventions/dependency_management.md - 関数コンポジション
 * @see bin/docs/conventions/tdd_process.md - 関数型スタイル
 */

import { type Browser, type Page } from 'playwright-core'
import { type IScraper, type ScrapedResult, type BrowserConfig } from '../types.js'

/**
 * ページ作成の高階関数
 * Browser設定を受け取り、ページを作成する関数を返す
 */
export const createPageFactory = (config: BrowserConfig) => 
  async (browser: Browser): Promise<Page | null> => {
    try {
      const page = await browser.newPage({
        userAgent: config.userAgent
      })
      
      // タイムアウト設定
      page.setDefaultTimeout(config.timeout)
      
      return page
    } catch (error) {
      console.error('⚠️  Failed to create page:', error)
      return null
    }
  }

/**
 * URLナビゲーションの高階関数
 * ページを受け取り、指定URLに移動する関数を返す
 */
export const createNavigator = (waitTime: number = 3000) => 
  async (page: Page, url: string): Promise<boolean> => {
    try {
      await page.goto(url, { waitUntil: 'networkidle' })
      
      // 指定時間待機
      await page.waitForTimeout(waitTime)
      
      console.log(`✅ Navigated to: ${url}`)
      return true
    } catch (error) {
      console.error(`⚠️  Failed to navigate to ${url}:`, error)
      return false
    }
  }

/**
 * データ抽出の基本関数
 * ページから基本的な情報を抽出する
 */
export const extractBasicData = async (
  page: Page, 
  source: string, 
  keyword: string
): Promise<ScrapedResult[]> => {
  try {
    // タイトル取得
    const title = await page.title()
    
    // 現在のURL取得
    const url = page.url()
    
    // 会社名抽出（基本的なパターンマッチング）
    const bodyText = await page.textContent('body') || ''
    const companyMatch = bodyText.match(/株式会社[\\u4e00-\\u9faf\\u3040-\\u309f\\u30a0-\\u30ff]+/)
    const company_name = companyMatch ? companyMatch[0] : null
    
    return [{
      source,
      company_name,
      title: title.slice(0, 200), // 最大200文字
      url,
      scraped_at: new Date().toISOString()
    }]
  } catch (error) {
    console.error('⚠️  Data extraction failed:', error)
    // エラー時は空配列を返す（規約準拠）
    return []
  }
}

/**
 * スクレイパー作成の高階関数
 * Browser設定とソース名を受け取り、スクレイパーを作成する
 */
export const createBaseScraper = (
  config: BrowserConfig,
  sourceName: string,
  urlBuilder: (keyword: string) => string
): IScraper => {
  const createPage = createPageFactory(config)
  const navigate = createNavigator(config.waitTime)

  return {
    scrape: async (browser: Browser, keyword: string): Promise<ScrapedResult[]> => {
      const page = await createPage(browser)
      if (!page) {
        return []
      }

      try {
        const url = urlBuilder(keyword)
        const navigated = await navigate(page, url)
        
        if (!navigated) {
          await page.close()
          return []
        }

        const results = await extractBasicData(page, sourceName, keyword)
        await page.close()
        
        return results
      } catch (error) {
        console.error(`⚠️  Scraping failed for keyword "${keyword}":`, error)
        
        try {
          await page.close()
        } catch (closeError) {
          console.error('⚠️  Failed to close page:', closeError)
        }
        
        // エラー時は空配列を返す（規約準拠）
        return []
      }
    },

    getName: (): string => {
      return `${sourceName}Scraper`
    }
  }
}

/**
 * スクレイパー操作の高階関数コンポーザー
 * 複数キーワードでのスクレイピングを並列実行
 */
export const withKeywords = (scraper: IScraper) => 
  async (browser: Browser, keywords: string[]): Promise<ScrapedResult[]> => {
    const results: ScrapedResult[] = []
    
    // 並列実行でパフォーマンス向上
    const promises = keywords.map(keyword => scraper.scrape(browser, keyword))
    const keywordResults = await Promise.all(promises)
    
    // 結果をフラット化
    keywordResults.forEach(keywordResult => {
      results.push(...keywordResult)
    })
    
    return results
  }

/**
 * エラーハンドリング付きスクレイパーラッパー
 * 失敗時の再試行機能を提供
 */
export const withRetry = (scraper: IScraper, maxRetries: number = 3) => ({
  ...scraper,
  scrape: async (browser: Browser, keyword: string): Promise<ScrapedResult[]> => {
    let lastError: Error | null = null
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const results = await scraper.scrape(browser, keyword)
        
        // 成功時は即座に結果を返す
        if (results.length > 0) {
          return results
        }
        
        // 結果が0件の場合も成功として扱う（エラーではない）
        if (attempt === maxRetries) {
          return []
        }
        
        console.log(`⏳ Retry attempt ${attempt}/${maxRetries} for keyword: ${keyword}`)
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))
        console.error(`⚠️  Attempt ${attempt}/${maxRetries} failed:`, lastError.message)
        
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
        }
      }
    }
    
    console.error(`❌ All ${maxRetries} attempts failed for keyword: ${keyword}`)
    return []
  }
})

/**
 * デバッグ用のモックスクレイパー作成関数
 */
export const createMockScraper = (sourceName: string = 'MOCK'): IScraper => ({
  scrape: async (browser: Browser, keyword: string): Promise<ScrapedResult[]> => {
    // モック結果を返す
    return [{
      source: sourceName,
      company_name: 'テスト株式会社',
      title: `${keyword}のテスト記事`,
      url: 'https://example.com/test',
      scraped_at: new Date().toISOString()
    }]
  },
  getName: (): string => `${sourceName}MockScraper`
})