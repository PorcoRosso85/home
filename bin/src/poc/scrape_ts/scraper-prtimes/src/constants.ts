/**
 * PR Times scraper constants
 * 既存実装から定数を分離し、関数型アプローチで利用
 */

/** PR Timesのベースサイト情報 */
export const PRTIMES_CONFIG = {
  SOURCE_NAME: 'PR_TIMES',
  BASE_URL: 'https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word=',
  SITE_URL: 'https://prtimes.jp'
} as const

/** Article要素を検索するためのセレクター（優先順位順） */
export const ARTICLE_SELECTORS = [
  'article.list-article',
  '.article-box', 
  'a[href*="/main/html/rd/p/"]',
  '.release-list a',
  'h3 a[href*="prtimes.jp"]'
] as const

/** タイトル要素を検索するためのセレクター */
export const TITLE_SELECTORS = [
  'h3',
  '.list-article__title',
  '.title', 
  'h2'
] as const

/** 企業名要素を検索するためのセレクター */
export const COMPANY_SELECTORS = [
  '.company-name',
  '.list-article__company', 
  '.company',
  'time'
] as const

/** PR Timesリンクパターン（フォールバック用） */
export const PRTIMES_LINK_PATTERN = 'a[href*="prtimes.jp/main/html/rd/p/"]'

/** 最小タイトル長（短すぎるテキストの除外用） */
export const MIN_TITLE_LENGTH = 10

/** デフォルトのタイトル最大長 */
export const DEFAULT_MAX_TITLE_LENGTH = 100