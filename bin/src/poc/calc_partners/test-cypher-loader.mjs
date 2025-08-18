#!/usr/bin/env node
/**
 * Cypherローダーテスト
 * cypherLoader.jsの動作確認
 */

import { chromium } from 'playwright-core'
import { spawn, execSync } from 'child_process'
import { promisify } from 'util'

const delay = promisify(setTimeout)

let viteProcess = null
let browser = null

/**
 * Get Chromium path for NixOS
 */
function getChromiumPath() {
  try {
    const chromiumPath = execSync('which chromium', { encoding: 'utf-8' }).trim()
    return chromiumPath
  } catch (error) {
    console.error('❌ Could not find chromium. Make sure to run in nix develop shell.')
    process.exit(1)
  }
}

/**
 * Start Vite dev server
 */
async function startViteServer() {
  console.log('🚀 Starting Vite dev server...')
  
  return new Promise((resolve, reject) => {
    viteProcess = spawn('npm', ['run', 'dev'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: process.cwd()
    })
    
    let serverReady = false
    const timeout = setTimeout(() => {
      if (!serverReady) {
        reject(new Error('Vite server failed to start within timeout'))
      }
    }, 15000)
    
    viteProcess.stdout.on('data', (data) => {
      const output = data.toString()
      console.log('📦 Vite:', output.trim())
      
      const localMatch = output.match(/Local:\s+http:\/\/localhost:(\d+)/)
      if (localMatch && !serverReady) {
        const port = localMatch[1]
        const url = `http://localhost:${port}`
        console.log(`🔗 Server URL: ${url}`)
        serverReady = true
        clearTimeout(timeout)
        resolve(url)
      }
    })
    
    viteProcess.stderr.on('data', (data) => {
      console.error('❌ Vite error:', data.toString().trim())
    })
  })
}

/**
 * Run loader test
 */
async function runLoaderTest() {
  console.log('🧪 Testing Cypher Loader')
  console.log('=' .repeat(50))
  
  try {
    // Start Vite
    const url = await startViteServer()
    await delay(3000)
    
    // Launch browser
    console.log('🌐 Launching browser...')
    const chromiumPath = getChromiumPath()
    
    browser = await chromium.launch({
      executablePath: chromiumPath,
      headless: true
    })
    
    const page = await browser.newPage()
    
    // Enable console logging
    page.on('console', (msg) => {
      const text = msg.text()
      if (text.includes('cypherLoader')) {
        console.log('🖥️  Loader:', text)
      }
    })
    
    // Create test page with loader usage
    await page.goto(url)
    
    // Test the loader directly in browser context
    const result = await page.evaluate(async () => {
      // Import and test the loader
      const { loadQuery, getCacheInfo } = await import('/infrastructure/cypherLoader.js')
      
      // Test 1: Load ping query
      console.log('Test 1: Loading ping.cypher')
      const pingResult = await loadQuery('dql', 'ping')
      
      // Test 2: Check cache hit
      console.log('Test 2: Loading again (should hit cache)')
      const pingResult2 = await loadQuery('dql', 'ping')
      
      // Test 3: Get cache info
      const cacheInfo = getCacheInfo()
      
      return {
        firstLoad: pingResult,
        secondLoad: pingResult2,
        cacheInfo: cacheInfo
      }
    })
    
    // Verify results
    console.log('\n📊 Test Results:')
    console.log('First load success:', result.firstLoad.success)
    console.log('Query content:', result.firstLoad.data?.substring(0, 50) + '...')
    console.log('Second load success:', result.secondLoad.success)
    console.log('Cache size:', result.cacheInfo.size)
    console.log('Cached keys:', result.cacheInfo.keys)
    
    if (result.firstLoad.success && result.secondLoad.success) {
      console.log('✅ Cypher loader test PASSED!')
      return true
    } else {
      console.log('❌ Cypher loader test FAILED!')
      return false
    }
    
  } catch (error) {
    console.error('💥 Test error:', error.message)
    return false
  }
}

/**
 * Cleanup
 */
async function cleanup() {
  if (browser) {
    await browser.close()
  }
  if (viteProcess) {
    viteProcess.kill('SIGTERM')
  }
  await delay(1000)
}

/**
 * Main
 */
async function main() {
  let success = false
  
  process.on('SIGINT', async () => {
    await cleanup()
    process.exit(1)
  })
  
  try {
    success = await runLoaderTest()
  } finally {
    await cleanup()
  }
  
  process.exit(success ? 0 : 1)
}

main().catch(console.error)