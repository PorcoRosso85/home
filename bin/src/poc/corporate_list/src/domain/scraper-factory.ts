/**
 * Factory for creating scrapers based on configuration
 */

import type { BaseScraper } from './scraper.js'
import type { ScrapeConfig } from './types.js'
import { PRTimesScraper } from './scrapers/prtimes-scraper.js'

export class ScraperFactory {
  /**
   * Create a PR Times scraper
   */
  static createPRTimesScraper(config: ScrapeConfig): BaseScraper {
    return new PRTimesScraper(config)
  }
  
  /**
   * Get all available scrapers
   * @param config - Scrape configuration
   * @returns Array of all available scrapers
   */
  static getAllScrapers(config: ScrapeConfig): BaseScraper[] {
    return [
      ScraperFactory.createPRTimesScraper(config)
    ]
  }
}