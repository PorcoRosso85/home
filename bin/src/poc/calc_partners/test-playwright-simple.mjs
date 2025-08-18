#!/usr/bin/env node
/**
 * Simplified Playwright E2E Test for NixOS
 * Tests Kuzu WASM ping.cypher execution
 */

import { chromium } from 'playwright-core'
import { spawn, execSync } from 'child_process'

const TEST_CONFIG = {
  url: 'http://localhost:3000',
  expectedResponse: '[{"response":"pong","status":1}]'
}

let viteProcess = null
let browser = null

/**
 * Get chromium path for NixOS
 */
function getChromiumPath() {
  try {
    const path = execSync('which chromium', { encoding: 'utf-8' }).trim()
    console.log('🔧 Using chromium at:', path)
    return path
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
    viteProcess = spawn('pnpm', ['run', 'dev'], {
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
      
      if (output.includes('Local:') && output.includes('localhost:')) {
        serverReady = true
        clearTimeout(timeout)
        setTimeout(resolve, 2000) // Wait 2 seconds for server to fully initialize
      }
    })
    
    viteProcess.stderr.on('data', (data) => {
      console.error('❌ Vite error:', data.toString().trim())
    })
  })
}

/**
 * Run the test
 */
async function runTest() {
  console.log('🧪 Starting Kuzu WASM E2E Test (Playwright - Simplified)')
  console.log('==================================================')
  
  try {
    // Start Vite server
    await startViteServer()
    
    // Launch browser
    console.log('🌐 Launching browser with NixOS chromium...')
    const chromiumPath = getChromiumPath()
    
    browser = await chromium.launch({
      executablePath: chromiumPath,
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    })
    
    const page = await browser.newPage()
    
    // Listen to console for debugging
    page.on('console', msg => {
      console.log('🖥️  Browser:', msg.text())
    })
    
    // Navigate to app
    console.log(`🔗 Navigating to ${TEST_CONFIG.url}...`)
    await page.goto(TEST_CONFIG.url, { waitUntil: 'networkidle' })
    
    // Wait for React app
    console.log('⚛️  Waiting for React app...')
    await page.waitForSelector('h1', { timeout: 10000 })
    
    // Wait for Kuzu to initialize
    console.log('⏳ Waiting for Kuzu initialization...')
    await page.waitForTimeout(5000) // Give Kuzu time to initialize
    
    // Get the status text
    const statusText = await page.textContent('p:first-of-type')
    console.log('📊 Status text:', statusText)
    
    // Check if ping succeeded
    if (statusText && statusText.includes(TEST_CONFIG.expectedResponse)) {
      console.log('==================================================')
      console.log('🎉 Test PASSED!')
      console.log(`✅ Kuzu WASM successfully executed ping.cypher`)
      console.log(`✅ Response: ${TEST_CONFIG.expectedResponse}`)
      process.exit(0)
    } else {
      console.log('==================================================')
      console.log('❌ Test FAILED!')
      console.log(`Expected: ${TEST_CONFIG.expectedResponse}`)
      console.log(`Got: ${statusText}`)
      process.exit(1)
    }
    
  } catch (error) {
    console.error('💥 Test error:', error.message)
    process.exit(1)
  } finally {
    // Cleanup
    if (browser) await browser.close()
    if (viteProcess) viteProcess.kill('SIGTERM')
  }
}

// Run the test
runTest().catch(error => {
  console.error('💥 Unhandled error:', error)
  if (browser) browser.close()
  if (viteProcess) viteProcess.kill('SIGTERM')
  process.exit(1)
})