/**
 * Abstract base scraper class for domain-driven scraping
 */

import { Browser, Page } from 'playwright-core'
import type { Article, ScrapedResult, ScrapeConfig } from './types.js'
import { extractCompanyName } from './extractor.js'

export abstract class BaseScraper {
  protected readonly sourceName: string
  protected readonly baseUrl: string
  protected readonly config: ScrapeConfig

  constructor(sourceName: string, baseUrl: string, config: ScrapeConfig) {
    this.sourceName = sourceName
    this.baseUrl = baseUrl
    this.config = config
  }

  /**
   * Main scraping method - template method pattern
   */
  async scrape(browser: Browser, keyword: string): Promise<ScrapedResult[]> {
    const results: ScrapedResult[] = []
    const page = await browser.newPage()
    
    try {
      const searchUrl = this.buildSearchUrl(keyword)
      console.log(`📰 Searching ${this.sourceName}: ${keyword}`)
      console.log(`   URL: ${searchUrl}`)
      
      await this.setupPage(page)
      await page.goto(searchUrl, { 
        waitUntil: 'domcontentloaded', 
        timeout: this.config.timeout 
      })
      
      await page.waitForTimeout(this.config.waitTime)
      
      const articles = await this.extractArticles(page)
      
      const now = new Date().toISOString()
      for (const article of articles) {
        results.push({
          source: this.sourceName,
          company_name: extractCompanyName(article.companyText || article.title),
          title: article.title,
          url: article.url,
          scraped_at: now
        })
      }
      
      console.log(`   ✅ Found ${results.length} articles`)
      
    } catch (error: any) {
      console.error(`   ❌ Error scraping ${this.sourceName}: ${error.message}`)
    } finally {
      await page.close()
    }
    
    return results
  }

  /**
   * Abstract methods to be implemented by concrete scrapers
   */
  protected abstract buildSearchUrl(keyword: string): string
  protected abstract extractArticles(page: Page): Promise<Article[]>

  /**
   * Default page setup - can be overridden
   */
  protected async setupPage(page: Page): Promise<void> {
    await page.setExtraHTTPHeaders({
      'User-Agent': this.config.userAgent
    })
  }
}