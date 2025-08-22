/**
 * Domain types for the corporate list scraper
 */

export interface Article {
  title: string;
  url: string;
  companyText: string;
}

export interface ScrapedResult {
  source: string;
  company_name: string | null;
  title: string;
  url: string;
  scraped_at: string;
}

export interface ScrapeConfig {
  maxTitleLength: number;
  timeout: number;
  waitTime: number;
  userAgent: string;
}