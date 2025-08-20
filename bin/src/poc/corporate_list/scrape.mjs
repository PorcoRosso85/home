#!/usr/bin/env node
/**
 * 企業リード収集スクレイパー（最小構成）
 * 要件: データの抽出精度は60%でよい。まずリストを溜めるスピードを優先
 */

import { chromium } from 'playwright-core'
import { execSync } from 'child_process'

// ========== 1. 設定 ==========
const SEARCH_KEYWORDS = [
  "シリーズA 資金調達",
  "事業開発 アライアンス"
]

const TARGET_SITES = {
  PR_TIMES: 'https://prtimes.jp/main/html/searchrlp/company_id/0/keyword/'
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
    
    await page.goto(searchUrl, { waitUntil: 'networkidle', timeout: 30000 })
    
    // 検索結果を待つ
    await page.waitForSelector('.list-article', { timeout: 10000 }).catch(() => {
      console.log('   ⚠️ No results found')
    })
    
    // 記事リストを取得
    const articles = await page.evaluate(() => {
      const items = []
      document.querySelectorAll('.list-article__link').forEach(link => {
        const titleEl = link.querySelector('.list-article__title')
        const companyEl = link.querySelector('.list-article__company-name')
        
        if (titleEl) {
          items.push({
            title: titleEl.textContent.trim(),
            url: link.href,
            companyText: companyEl ? companyEl.textContent.trim() : ''
          })
        }
      })
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