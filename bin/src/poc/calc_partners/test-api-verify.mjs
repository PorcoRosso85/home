#!/usr/bin/env node
/**
 * Kuzu WASM API検証テスト
 * 実際のAPIがどちらなのかを確認
 */

import { chromium } from 'playwright-core'
import { spawn, execSync } from 'child_process'

let viteProcess = null
let browser = null

// Chromium取得
function getChromiumPath() {
  try {
    return execSync('which chromium', { encoding: 'utf-8' }).trim()
  } catch (error) {
    console.error('❌ Chromium not found')
    process.exit(1)
  }
}

// Vite起動
async function startVite() {
  return new Promise((resolve) => {
    viteProcess = spawn('npm', ['run', 'dev'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: process.cwd()
    })
    
    viteProcess.stdout.on('data', (data) => {
      const output = data.toString()
      const match = output.match(/http:\/\/localhost:(\d+)/)
      if (match) {
        resolve(`http://localhost:${match[1]}`)
      }
    })
  })
}

// APIテスト
async function testAPI() {
  console.log('🔍 Kuzu WASM API Verification Test')
  console.log('=' .repeat(40))
  
  try {
    const url = await startVite()
    await new Promise(r => setTimeout(r, 3000))
    
    browser = await chromium.launch({
      executablePath: getChromiumPath(),
      headless: true // ヘッドレスモード
    })
    
    const page = await browser.newPage()
    
    // コンソールログ収集
    const logs = []
    page.on('console', msg => {
      const text = msg.text()
      console.log('📝', text)
      logs.push(text)
    })
    
    await page.goto(url)
    
    // APIテスト実行（既存のインフラストラクチャを使用）
    const apiTest = await page.evaluate(async () => {
      const results = {}
      
      try {
        // 既存のinitializeKuzuを使用
        const { initializeKuzu, executeQuery } = await import('/infrastructure.ts')
        const kuzuConnection = await initializeKuzu()
        const conn = kuzuConnection.conn
        
        // テストクエリ実行
        const result = await conn.execute("RETURN 'test' AS message, 123 AS number")
        
        // API検証
        results.hasTable = 'table' in result
        results.hasGetAll = typeof result.getAll === 'function'
        results.hasGetAllRows = typeof result.getAllRows === 'function'
        results.hasGetAllObjects = typeof result.getAllObjects === 'function'
        results.hasToString = typeof result.toString === 'function'
        
        // 各メソッドを試行
        if (results.hasTable) {
          try {
            results.tableToString = result.table.toString()
            results.tableWorks = true
          } catch (e) {
            results.tableError = e.message
            results.tableWorks = false
          }
        }
        
        if (results.hasGetAllRows) {
          try {
            results.getAllRowsResult = await result.getAllRows()
            results.getAllRowsWorks = true
          } catch (e) {
            results.getAllRowsError = e.message
            results.getAllRowsWorks = false
          }
        }
        
        if (results.hasGetAllObjects) {
          try {
            results.getAllObjectsResult = await result.getAllObjects()
            results.getAllObjectsWorks = true
          } catch (e) {
            results.getAllObjectsError = e.message
            results.getAllObjectsWorks = false
          }
        }
        
        if (results.hasToString) {
          try {
            results.toStringResult = await result.toString()
            results.toStringWorks = true
          } catch (e) {
            results.toStringError = e.message
            results.toStringWorks = false
          }
        }
        
        await result.close()
        await conn.close()
        await kuzuConnection.db.close()
        
      } catch (error) {
        results.error = error.message
      }
      
      return results
    })
    
    console.log('\n📊 API Test Results:')
    console.log(JSON.stringify(apiTest, null, 2))
    
    // 結論
    console.log('\n✅ 結論:')
    if (apiTest.tableWorks) {
      console.log('- result.table.toString() が動作します（NPM README通り）')
    }
    if (apiTest.getAllRowsWorks) {
      console.log('- result.getAllRows() が動作します（APIドキュメント通り）')
    }
    if (apiTest.getAllObjectsWorks) {
      console.log('- result.getAllObjects() が動作します（APIドキュメント通り）')
    }
    if (apiTest.toStringWorks) {
      console.log('- result.toString() が動作します（APIドキュメント通り）')
    }
    
    return apiTest
    
  } catch (error) {
    console.error('💥 Error:', error.message)
    return null
  }
}

// クリーンアップ
async function cleanup() {
  if (browser) await browser.close()
  if (viteProcess) viteProcess.kill()
}

// 実行
async function main() {
  process.on('SIGINT', async () => {
    await cleanup()
    process.exit(1)
  })
  
  try {
    const result = await testAPI()
    console.log('\n🏁 Test completed')
  } finally {
    await cleanup()
  }
}

main().catch(console.error)