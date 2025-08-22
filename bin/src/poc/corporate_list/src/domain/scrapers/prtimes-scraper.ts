/**
 * PR Times specific scraper implementation
 */

import { Page } from 'playwright-core'
import { BaseScraper } from '../scraper.js'
import type { Article, ScrapeConfig } from '../types.js'

export class PRTimesScraper extends BaseScraper {
  constructor(config: ScrapeConfig) {
    super(
      'PR_TIMES',
      'https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word=',
      config
    )
  }

  protected buildSearchUrl(keyword: string): string {
    return `${this.baseUrl}${encodeURIComponent(keyword)}`
  }

  protected async extractArticles(page: Page): Promise<Article[]> {
    const maxTitleLength = this.config.maxTitleLength
    
    return await page.evaluate((maxTitleLength): Article[] => {
      // Browser context - using any to bypass TypeScript DOM type checks
      const doc = (globalThis as any).document;
      const consoleLog = (globalThis as any).console.log;
      
      const items: Article[] = []
      
      // Multiple selector patterns to try
      const selectors = [
        'article.list-article',
        '.article-box',
        'a[href*="/main/html/rd/p/"]',
        '.release-list a',
        'h3 a[href*="prtimes.jp"]'
      ]
      
      for (const selector of selectors) {
        const elements = doc.querySelectorAll(selector)
        if (elements.length > 0) {
          consoleLog(`Found ${elements.length} items with selector: ${selector}`)
          
          elements.forEach((el: any) => {
            // Get link element
            const link = el.tagName === 'A' ? el : el.querySelector('a')
            if (!link) return
            
            // Get title (multiple patterns)
            let title = ''
            const titleSelectors = ['h3', '.list-article__title', '.title', 'h2']
            for (const ts of titleSelectors) {
              const titleEl = el.querySelector(ts) || (el.tagName === 'H3' ? el : null)
              if (titleEl) {
                title = titleEl.textContent?.trim() || ''
                break
              }
            }
            
            // Fallback to link text
            if (!title && link) {
              title = link.textContent?.trim() || ''
            }
            
            // Get company name (multiple patterns)
            let company = ''
            const companySelectors = ['.company-name', '.list-article__company', '.company', 'time']
            for (const cs of companySelectors) {
              const companyEl = el.querySelector(cs)
              if (companyEl) {
                company = companyEl.textContent?.trim() || ''
                break
              }
            }
            
            if (title && link.href) {
              items.push({
                title: title.substring(0, maxTitleLength), // Title length limit
                url: link.href,
                companyText: company
              })
            }
          })
          
          if (items.length > 0) break // Stop if results found
        }
      }
      
      // Fallback: collect all PR Times links if no results
      if (items.length === 0) {
        doc.querySelectorAll('a[href*="prtimes.jp/main/html/rd/p/"]').forEach((link: any) => {
          const anchor = link
          const title = anchor.textContent?.trim() || ''
          if (title && title.length > 10) { // Exclude too short text
            items.push({
              title: title.substring(0, maxTitleLength),
              url: anchor.href,
              companyText: ''
            })
          }
        })
      }
      
      return items
    }, maxTitleLength)
  }
}