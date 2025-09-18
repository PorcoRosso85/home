/**
 * 企業リード収集スクレイパー設定ファイル
 * Configuration and constants for the corporate lead scraper
 */

// ========== Configuration Types ==========

/** Target sites configuration */
interface TargetSitesConfig {
  /** PR TIMES search URL format */
  PR_TIMES: string;
}

/** Scraper configuration options */
interface ScraperConfig {
  /** Keywords to search for */
  searchKeywords: string[];
  /** Target site URLs */
  targetSites: TargetSitesConfig;
  /** Browser configuration */
  browser: {
    /** User agent string for HTTP requests */
    userAgent: string;
    /** Page load timeout in milliseconds */
    timeout: number;
    /** Wait time after page load in milliseconds */
    waitTime: number;
    /** Browser launch arguments */
    launchArgs: string[];
  };
  /** Data extraction configuration */
  extraction: {
    /** Maximum title length */
    maxTitleLength: number;
    /** Company name regex patterns */
    companyPatterns: RegExp[];
  };
}

// ========== Default Configuration Values ==========

/** Default search keywords for corporate news */
export const SEARCH_KEYWORDS: string[] = [
  "シリーズA",
  "資金調達", 
  "事業提携"
];

/** Target site URLs and patterns */
export const TARGET_SITES: TargetSitesConfig = {
  PR_TIMES: 'https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word='
};

/** Default browser configuration */
export const BROWSER_CONFIG = {
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  timeout: 30000,
  waitTime: 3000,
  launchArgs: ['--no-sandbox', '--disable-setuid-sandbox']
};

/** Data extraction patterns and limits */
export const EXTRACTION_CONFIG = {
  maxTitleLength: 200,
  companyPatterns: [
    /株式会社[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+/,
    /[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+株式会社/,
  ]
};

// ========== Environment Variable Support ==========

/**
 * Get configuration from environment variables with fallbacks to defaults
 * @returns Complete scraper configuration
 */
export function getConfig(): ScraperConfig {
  // Parse search keywords from environment or use defaults
  const envKeywords = process.env.SCRAPER_KEYWORDS;
  const searchKeywords = envKeywords 
    ? envKeywords.split(',').map(k => k.trim()).filter(k => k.length > 0)
    : SEARCH_KEYWORDS;

  // Parse browser timeout from environment or use default
  const envTimeout = process.env.SCRAPER_TIMEOUT;
  const timeout = envTimeout && !isNaN(parseInt(envTimeout)) 
    ? parseInt(envTimeout) 
    : BROWSER_CONFIG.timeout;

  // Parse browser wait time from environment or use default
  const envWaitTime = process.env.SCRAPER_WAIT_TIME;
  const waitTime = envWaitTime && !isNaN(parseInt(envWaitTime))
    ? parseInt(envWaitTime)
    : BROWSER_CONFIG.waitTime;

  // Parse max title length from environment or use default
  const envMaxTitleLength = process.env.SCRAPER_MAX_TITLE_LENGTH;
  const maxTitleLength = envMaxTitleLength && !isNaN(parseInt(envMaxTitleLength))
    ? parseInt(envMaxTitleLength)
    : EXTRACTION_CONFIG.maxTitleLength;

  // Custom user agent from environment or use default
  const userAgent = process.env.SCRAPER_USER_AGENT || BROWSER_CONFIG.userAgent;

  // Custom PR TIMES URL from environment or use default
  const prTimesUrl = process.env.SCRAPER_PRTIMES_URL || TARGET_SITES.PR_TIMES;

  return {
    searchKeywords,
    targetSites: {
      PR_TIMES: prTimesUrl
    },
    browser: {
      userAgent,
      timeout,
      waitTime,
      launchArgs: BROWSER_CONFIG.launchArgs
    },
    extraction: {
      maxTitleLength,
      companyPatterns: EXTRACTION_CONFIG.companyPatterns
    }
  };
}

// ========== Export Types ==========
export type { TargetSitesConfig, ScraperConfig };