/**
 * PR Times scraper package entry point
 * 関数型スタイルでPR Times固有のスクレイピング機能を提供
 */

// Constants
export { 
  PRTIMES_CONFIG,
  ARTICLE_SELECTORS,
  TITLE_SELECTORS,
  COMPANY_SELECTORS,
  PRTIMES_LINK_PATTERN,
  MIN_TITLE_LENGTH,
  DEFAULT_MAX_TITLE_LENGTH
} from './constants.js'

// Parser functions
export {
  parsePRTimesArticles,
  extractCompanyName,
  cleanTitle,
  type ArticleData
} from './parser.js'

// Scraper implementations
export {
  createPRTimesScraper,
  createDefaultPRTimesScraper
} from './scraper.js'

// Re-export core types for convenience
export type {
  IScraper,
  ScrapedResult,
  BrowserConfig
} from '@corporate-list/scraper-core'