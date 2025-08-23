/**
 * PR Times scraper implementation using functional composition
 * scraper-coreの関数を合成してPR Times固有の機能を実現
 */

import { type Browser, type Page } from 'playwright-core'
import { 
  createPageFactory, 
  createNavigator, 
  withRetry,
  type IScraper 
} from '../../scraper-core/src/mod.js'
import type { ScrapedResult, BrowserConfig } from '../../scraper-core/src/mod.js'
import { parsePRTimesArticles, extractCompanyName, type ArticleData } from './parser.js'
import { PRTIMES_CONFIG, DEFAULT_MAX_TITLE_LENGTH } from './constants.js'

/**
 * PR Times用のURL構築関数
 */
const buildPRTimesUrl = (keyword: string): string => {
  return `${PRTIMES_CONFIG.BASE_URL}${encodeURIComponent(keyword)}`
}

/**
 * ArticleDataからScrapedResultへの変換関数
 */
const articleToScrapedResult = (source: string) => 
  (article: ArticleData): ScrapedResult => ({
    source,
    company_name: extractCompanyName(article.companyText),
    title: article.title,
    url: article.url,
    scraped_at: new Date().toISOString()
  })

/**
 * PR Times固有のデータ抽出関数
 * Page.evaluateを使ってブラウザ内でパース関数を実行
 */
const extractPRTimesData = (maxTitleLength: number = DEFAULT_MAX_TITLE_LENGTH) => 
  async (page: Page, source: string): Promise<ScrapedResult[]> => {
    try {
      // ブラウザ内で実行される関数（parse関数を文字列として渡す）
      const articles = await page.evaluate((maxTitleLength): ArticleData[] => {
        // パース関数をブラウザ内で再定義（必要な部分のみ）
        const ARTICLE_SELECTORS = [
          'article.list-article',
          '.article-box', 
          'a[href*="/main/html/rd/p/"]',
          '.release-list a',
          'h3 a[href*="prtimes.jp"]'
        ]
        
        const TITLE_SELECTORS = ['h3', '.list-article__title', '.title', 'h2']
        const COMPANY_SELECTORS = ['.company-name', '.list-article__company', '.company', 'time']
        const PRTIMES_LINK_PATTERN = 'a[href*="prtimes.jp/main/html/rd/p/"]'
        const MIN_TITLE_LENGTH = 10

        const extractTitle = (element: Element): string => {
          for (const selector of TITLE_SELECTORS) {
            const titleEl = element.querySelector(selector) || 
                           (element.tagName === selector.toUpperCase() ? element : null)
            if (titleEl?.textContent?.trim()) {
              return titleEl.textContent.trim()
            }
          }
          const link = element.tagName === 'A' ? element : element.querySelector('a')
          return link?.textContent?.trim() || ''
        }

        const extractCompany = (element: Element): string => {
          for (const selector of COMPANY_SELECTORS) {
            const companyEl = element.querySelector(selector)
            if (companyEl?.textContent?.trim()) {
              return companyEl.textContent.trim()
            }
          }
          return ''
        }

        const extractUrl = (element: Element): string => {
          const link = element.tagName === 'A' ? element : element.querySelector('a')
          return (link as HTMLAnchorElement)?.href || ''
        }

        const extractArticleFromElement = (element: Element): ArticleData | null => {
          const title = extractTitle(element)
          const url = extractUrl(element)
          const companyText = extractCompany(element)
          
          if (!title || !url) return null
          
          return { title, url, companyText }
        }

        // メイン抽出ロジック
        const doc = document
        
        // 複数セレクターを優先順位で試行
        for (const selector of ARTICLE_SELECTORS) {
          const elements = Array.from(doc.querySelectorAll(selector))
          if (elements.length > 0) {
            console.log(`Found ${elements.length} items with selector: ${selector}`)
            
            const articles = elements
              .map(extractArticleFromElement)
              .filter((article): article is ArticleData => article !== null)
              .map(article => ({
                ...article,
                title: article.title.substring(0, maxTitleLength)
              }))
            
            if (articles.length > 0) return articles
          }
        }
        
        // フォールバック
        console.log('Using fallback extraction method')
        const elements = Array.from(doc.querySelectorAll(PRTIMES_LINK_PATTERN))
        
        return elements
          .map(link => link.textContent?.trim() || '')
          .filter(title => title.length > MIN_TITLE_LENGTH)
          .map(title => ({
            title: title.substring(0, maxTitleLength),
            url: (elements.find(el => el.textContent?.trim() === title) as HTMLAnchorElement)?.href || '',
            companyText: ''
          }))
          .filter(article => article.url)
      }, maxTitleLength)

      // ArticleDataをScrapedResultに変換
      const converter = articleToScrapedResult(source)
      return articles.map(converter)
      
    } catch (error) {
      console.error('⚠️  PR Times data extraction failed:', error)
      return []
    }
  }

/**
 * PR Times専用スクレイパー作成関数
 */
export const createPRTimesScraper = (
  config: BrowserConfig,
  maxTitleLength: number = DEFAULT_MAX_TITLE_LENGTH
): IScraper => {
  const createPage = createPageFactory(config)
  const navigate = createNavigator(config.waitTime)
  const extractData = extractPRTimesData(maxTitleLength)

  const baseScraper: IScraper = {
    scrape: async (browser: Browser, keyword: string): Promise<ScrapedResult[]> => {
      const page = await createPage(browser)
      if (!page) {
        return []
      }

      try {
        const url = buildPRTimesUrl(keyword)
        const navigated = await navigate(page, url)
        
        if (!navigated) {
          await page.close()
          return []
        }

        const results = await extractData(page, PRTIMES_CONFIG.SOURCE_NAME)
        await page.close()
        
        console.log(`✅ PR Times scraping completed: ${results.length} articles found`)
        return results
      } catch (error) {
        console.error(`⚠️  PR Times scraping failed for keyword "${keyword}":`, error)
        
        try {
          await page.close()
        } catch (closeError) {
          console.error('⚠️  Failed to close page:', closeError)
        }
        
        return []
      }
    },

    getName: (): string => {
      return 'PRTimesScraper'
    }
  }

  // リトライ機能を追加して返す
  return withRetry(baseScraper, 3)
}

/**
 * デフォルト設定でPR Timesスクレイパーを作成
 */
export const createDefaultPRTimesScraper = (config: BrowserConfig): IScraper => {
  return createPRTimesScraper(config, DEFAULT_MAX_TITLE_LENGTH)
}