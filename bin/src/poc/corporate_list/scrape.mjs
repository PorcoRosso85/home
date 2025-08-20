#!/usr/bin/env node
/**
 * 企業リード収集スクレイパー（最小構成）
 * 要件: データの抽出精度は60%でよい。まずリストを溜めるスピードを優先
 */

import { chromium } from 'playwright-core'
import { execSync } from 'child_process'

// ========== 1. 設定 ==========
const SEARCH_KEYWORDS = [
  "シリーズA",
  "資金調達",
  "事業提携"
]

// PR TIMESの検索URL形式
const TARGET_SITES = {
  PR_TIMES: 'https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word='
}

// ========== 2. ヘルパー関数 ==========
function getChromiumPath() {
  try {
    const path = execSync('which chromium', { encoding: 'utf-8' }).trim()
    console.log('🔧 Using chromium at:', path)
    return path
  } catch (error) {
    console.error('❌ Could not find chromium. Run in nix shell.')
    process.exit(1)
  }
}

// 簡易的な企業名抽出（精度60%で十分）
function extractCompanyName(text) {
  const patterns = [
    /株式会社[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+/,
    /[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+株式会社/,
  ]
  
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) return match[0]
  }
  
  return null // 抽出できなければ空欄でOK
}

// ========== 3. スクレイピング関数 ==========
async function scrapePRTimes(browser, keyword) {
  const results = []
  const page = await browser.newPage()
  
  try {
    const searchUrl = `${TARGET_SITES.PR_TIMES}${encodeURIComponent(keyword)}`
    console.log(`📰 Searching PR TIMES: ${keyword}`)
    console.log(`   URL: ${searchUrl}`)
    
    // ユーザーエージェント設定（より自然なアクセスに）
    await page.setExtraHTTPHeaders({
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 })
    
    // ページが完全に読み込まれるまで少し待つ
    await page.waitForTimeout(3000)
    
    // 記事リストを取得（PR TIMESの実際の構造に合わせて修正）
    const articles = await page.evaluate(() => {
      const items = []
      
      // 複数のセレクターパターンを試す
      const selectors = [
        'article.list-article',
        '.article-box',
        'a[href*="/main/html/rd/p/"]',
        '.release-list a',
        'h3 a[href*="prtimes.jp"]'
      ]
      
      for (const selector of selectors) {
        const elements = document.querySelectorAll(selector)
        if (elements.length > 0) {
          console.log(`Found ${elements.length} items with selector: ${selector}`)
          
          elements.forEach(el => {
            // リンク要素の取得
            const link = el.tagName === 'A' ? el : el.querySelector('a')
            if (!link) return
            
            // タイトルの取得（複数パターン）
            let title = ''
            const titleSelectors = ['h3', '.list-article__title', '.title', 'h2']
            for (const ts of titleSelectors) {
              const titleEl = el.querySelector(ts) || (el.tagName === 'H3' ? el : null)
              if (titleEl) {
                title = titleEl.textContent.trim()
                break
              }
            }
            
            // タイトルがリンクのテキストから取得
            if (!title && link) {
              title = link.textContent.trim()
            }
            
            // 会社名の取得（複数パターン）
            let company = ''
            const companySelectors = ['.company-name', '.list-article__company', '.company', 'time']
            for (const cs of companySelectors) {
              const companyEl = el.querySelector(cs)
              if (companyEl) {
                company = companyEl.textContent.trim()
                break
              }
            }
            
            if (title && link.href) {
              items.push({
                title: title.substring(0, 200), // タイトルを200文字に制限
                url: link.href,
                companyText: company
              })
            }
          })
          
          if (items.length > 0) break // 結果が見つかったら終了
        }
      }
      
      // 結果が見つからない場合、ページ全体のリンクを収集
      if (items.length === 0) {
        document.querySelectorAll('a[href*="prtimes.jp/main/html/rd/p/"]').forEach(link => {
          const title = link.textContent.trim()
          if (title && title.length > 10) { // 短すぎるテキストは除外
            items.push({
              title: title.substring(0, 200),
              url: link.href,
              companyText: ''
            })
          }
        })
      }
      
      return items
    })
    
    // データ整形
    const now = new Date().toISOString()
    for (const article of articles) {
      results.push({
        source: 'PR_TIMES',
        company_name: extractCompanyName(article.companyText || article.title),
        title: article.title,
        url: article.url,
        scraped_at: now
      })
    }
    
    console.log(`   ✅ Found ${results.length} articles`)
    
  } catch (error) {
    console.error(`   ❌ Error scraping PR TIMES: ${error.message}`)
  } finally {
    await page.close()
  }
  
  return results
}

// ========== 4. メイン処理 ==========
async function main() {
  console.log('🚀 Starting Lead Scraper (No DB version)')
  console.log('==================================================')
  
  let browser = null
  
  try {
    // ブラウザ起動
    const chromiumPath = getChromiumPath()
    browser = await chromium.launch({
      executablePath: chromiumPath,
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    })
    console.log('✅ Browser launched')
    
    // スクレイピング実行
    const allResults = []
    
    for (const keyword of SEARCH_KEYWORDS) {
      const results = await scrapePRTimes(browser, keyword)
      allResults.push(...results)
    }
    
    // 結果をJSON形式で出力（後でDB保存する際に使える）
    console.log('\n📊 Results:')
    console.log('==================================================')
    console.log(JSON.stringify(allResults, null, 2))
    
    // サマリー
    console.log('\n==================================================')
    console.log(`📈 Total: ${allResults.length} articles found`)
    
    // 企業名抽出の成功率を表示
    const withCompany = allResults.filter(r => r.company_name).length
    const successRate = Math.round((withCompany / allResults.length) * 100)
    console.log(`🏢 Company extraction rate: ${successRate}% (${withCompany}/${allResults.length})`)
    
  } catch (error) {
    console.error('💥 Fatal error:', error.message)
    process.exit(1)
  } finally {
    if (browser) await browser.close()
  }
}

// 実行
main().catch(error => {
  console.error('💥 Unhandled error:', error)
  process.exit(1)
})