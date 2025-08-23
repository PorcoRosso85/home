/**
 * PR Times specific parsing functions
 * 既存実装から抽出した解析ロジックを関数型で再実装
 */

import { ARTICLE_SELECTORS, TITLE_SELECTORS, COMPANY_SELECTORS, PRTIMES_LINK_PATTERN, MIN_TITLE_LENGTH } from './constants.js'

/** 解析対象の記事データ型 */
export type ArticleData = {
  title: string
  url: string
  companyText: string
}

/** HTML要素から記事データを抽出する関数 */
type ElementExtractor = (element: Element) => ArticleData | null

/** セレクターからHTML要素を取得する */
const getElementsBySelector = (doc: Document) => (selector: string): Element[] => {
  return Array.from(doc.querySelectorAll(selector))
}

/** 要素からタイトルを抽出 */
const extractTitle = (element: Element): string => {
  // 複数のセレクターパターンを試行
  for (const selector of TITLE_SELECTORS) {
    const titleEl = element.querySelector(selector) || 
                   (element.tagName === selector.toUpperCase() ? element : null)
    if (titleEl?.textContent?.trim()) {
      return titleEl.textContent.trim()
    }
  }
  
  // リンク要素のテキストをフォールバック
  const link = element.tagName === 'A' ? element : element.querySelector('a')
  return link?.textContent?.trim() || ''
}

/** 要素から企業名を抽出 */
const extractCompany = (element: Element): string => {
  for (const selector of COMPANY_SELECTORS) {
    const companyEl = element.querySelector(selector)
    if (companyEl?.textContent?.trim()) {
      return companyEl.textContent.trim()
    }
  }
  return ''
}

/** 要素からURLを抽出 */
const extractUrl = (element: Element): string => {
  const link = element.tagName === 'A' ? element : element.querySelector('a')
  return (link as HTMLAnchorElement)?.href || ''
}

/** 単一要素から記事データを抽出 */
const extractArticleFromElement: ElementExtractor = (element: Element): ArticleData | null => {
  const title = extractTitle(element)
  const url = extractUrl(element)
  const companyText = extractCompany(element)
  
  if (!title || !url) return null
  
  return {
    title,
    url,
    companyText
  }
}

/** 指定セレクターで要素群から記事データを抽出 */
const extractArticlesWithSelector = (doc: Document, maxTitleLength: number) => 
  (selector: string): ArticleData[] => {
    const elements = getElementsBySelector(doc)(selector)
    if (elements.length === 0) return []
    
    console.log(`Found ${elements.length} items with selector: ${selector}`)
    
    return elements
      .map(extractArticleFromElement)
      .filter((article): article is ArticleData => article !== null)
      .map(article => ({
        ...article,
        title: article.title.substring(0, maxTitleLength)
      }))
  }

/** フォールバック: PR Timesリンクを直接収集 */
const extractFallbackArticles = (doc: Document, maxTitleLength: number): ArticleData[] => {
  const elements = getElementsBySelector(doc)(PRTIMES_LINK_PATTERN)
  
  return elements
    .map(link => link.textContent?.trim() || '')
    .filter(title => title.length > MIN_TITLE_LENGTH)
    .map(title => ({
      title: title.substring(0, maxTitleLength),
      url: (elements.find(el => el.textContent?.trim() === title) as HTMLAnchorElement)?.href || '',
      companyText: ''
    }))
    .filter(article => article.url)
}

/** 
 * PR Times固有のHTML解析関数
 * Page.evaluate内で実行される純粋関数
 */
export const parsePRTimesArticles = (maxTitleLength: number) => 
  (doc: Document): ArticleData[] => {
    const extractWithSelector = extractArticlesWithSelector(doc, maxTitleLength)
    
    // 複数セレクターを優先順位で試行
    for (const selector of ARTICLE_SELECTORS) {
      const articles = extractWithSelector(selector)
      if (articles.length > 0) {
        return articles
      }
    }
    
    // フォールバック実行
    console.log('Using fallback extraction method')
    return extractFallbackArticles(doc, maxTitleLength)
  }

/** 
 * 企業名抽出関数（将来の拡張用）
 * PR Times固有の企業名抽出ロジックを実装
 */
export const extractCompanyName = (text: string): string | null => {
  if (!text?.trim()) return null
  
  // 基本的なクリーニング
  const cleaned = text.trim()
  
  // 空文字や短すぎる場合は無効
  if (cleaned.length < 2) return null
  
  return cleaned
}

/** 
 * タイトルクリーニング関数
 * PR Times固有のタイトル整形ロジック
 */
export const cleanTitle = (title: string, maxLength: number = 100): string => {
  if (!title?.trim()) return ''
  
  const cleaned = title.trim()
  
  // 最大長でカット
  return cleaned.substring(0, maxLength)
}