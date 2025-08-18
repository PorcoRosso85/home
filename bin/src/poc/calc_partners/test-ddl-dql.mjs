#!/usr/bin/env node
/**
 * DDL+DQL最小テスト（KISS原則）
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
    viteProcess = spawn('pnpm', ['dev'], {
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

// メインテスト
async function test() {
  console.log('🧪 DDL+DQL Test (KISS+YAGNI)')
  console.log('=' .repeat(40))
  
  try {
    // Vite起動
    const url = await startVite()
    await new Promise(r => setTimeout(r, 3000))
    
    // ブラウザ起動
    browser = await chromium.launch({
      executablePath: getChromiumPath(),
      headless: true
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
    
    // testDQLQuery実行
    const result = await page.evaluate(async () => {
      const { testDQLQuery } = await import('/application.ts')
      return await testDQLQuery()
    })
    
    console.log('\n📊 Result:')
    console.log('Success:', result.success)
    console.log('Message:', result.message)
    console.log('Data:', result.data)
    
    // 成功判定（KISS: 空配列が返ればOK）
    if (result.success && Array.isArray(result.data)) {
      console.log('✅ Test PASSED - DDL executed, DQL returned empty array')
      return true
    } else {
      console.log('❌ Test FAILED')
      return false
    }
    
  } catch (error) {
    console.error('💥 Error:', error.message)
    return false
  }
}

// クリーンアップ
async function cleanup() {
  if (browser) await browser.close()
  if (viteProcess) viteProcess.kill()
}

// 実行
async function main() {
  let success = false
  
  process.on('SIGINT', async () => {
    await cleanup()
    process.exit(1)
  })
  
  try {
    success = await test()
  } finally {
    await cleanup()
  }
  
  process.exit(success ? 0 : 1)
}

main().catch(console.error)