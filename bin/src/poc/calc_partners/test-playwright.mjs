#!/usr/bin/env node
/**
 * Kuzu WASM End-to-End Test with Playwright Core
 * 
 * Tests:
 * 1. Vite dev server startup
 * 2. Kuzu WASM initialization 
 * 3. Ping query execution
 * 4. Expected response verification
 * 
 * Expected result: [{"response":"pong","status":1}]
 */

import { chromium } from 'playwright-core'
import { spawn, execSync } from 'child_process'
import { promisify } from 'util'

const delay = promisify(setTimeout)

// Test configuration
const TEST_CONFIG = {
  url: null, // Will be set dynamically based on Vite output
  timeout: 30000, // 30 seconds for Kuzu initialization
  serverStartDelay: 3000, // 3 seconds to let Vite server start
  expectedResponse: '[{"response":"pong","status":1}]'
}

let viteProcess = null
let browser = null

/**
 * Get Chromium executable path for NixOS
 */
function getChromiumPath() {
  // For NixOS, use the absolute path from which command
  // This ensures we use the Nix store version
  try {
    const chromiumPath = execSync('which chromium', { encoding: 'utf-8' }).trim()
    return chromiumPath
  } catch (error) {
    // Fallback to just 'chromium' if which command fails
    console.warn('Could not find chromium path, using fallback:', error.message)
    return 'chromium'
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
    }, 15000) // 15 second timeout for server start
    
    viteProcess.stdout.on('data', (data) => {
      const output = data.toString()
      console.log('📦 Vite:', output.trim())
      
      // Check for server ready indicators - extract port dynamically
      const localMatch = output.match(/Local:\s+http:\/\/localhost:(\d+)/)
      if (localMatch && !serverReady) {
        const port = localMatch[1]
        TEST_CONFIG.url = `http://localhost:${port}`
        console.log(`🔗 Detected server URL: ${TEST_CONFIG.url}`)
        serverReady = true
        clearTimeout(timeout)
        resolve()
      }
    })
    
    viteProcess.stderr.on('data', (data) => {
      console.error('❌ Vite error:', data.toString().trim())
    })
    
    viteProcess.on('exit', (code) => {
      console.log(`📦 Vite server exited with code ${code}`)
      if (!serverReady) {
        reject(new Error(`Vite server exited with code ${code}`))
      }
    })
  })
}

/**
 * Stop Vite dev server
 */
function stopViteServer() {
  if (viteProcess) {
    console.log('🛑 Stopping Vite dev server...')
    viteProcess.kill('SIGTERM')
    viteProcess = null
  }
}

/**
 * Wait for element with text to appear
 */
async function waitForTextContent(page, selector, expectedText, timeout = 30000) {
  console.log(`⏳ Waiting for text "${expectedText}" in ${selector}...`)
  
  try {
    await page.waitForFunction(
      ({selector, expectedText}) => {
        const element = document.querySelector(selector)
        return element && element.textContent.includes(expectedText)
      },
      {selector, expectedText},
      { timeout }
    )
    console.log('✅ Expected text found!')
    return true
  } catch (error) {
    console.error(`❌ Text not found within ${timeout}ms:`, error.message)
    return false
  }
}

/**
 * Run the end-to-end test
 */
async function runE2ETest() {
  console.log('🧪 Starting Kuzu WASM E2E Test (Playwright)')
  console.log('=' .repeat(50))
  
  try {
    // Step 1: Start Vite server
    await startViteServer()
    await delay(TEST_CONFIG.serverStartDelay)
    
    // Step 2: Launch browser with NixOS chromium
    console.log('🌐 Launching browser with NixOS chromium...')
    
    const chromiumPath = getChromiumPath()
    console.log(`🔧 Using chromium at: ${chromiumPath}`)
    
    browser = await chromium.launch({
      executablePath: chromiumPath,
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security', // For WASM loading
        '--disable-features=VizDisplayCompositor'
      ]
    })
    
    const page = await browser.newPage()
    
    // Enable console logging from the page
    page.on('console', (msg) => {
      const type = msg.type()
      const text = msg.text()
      if (type === 'error') {
        console.error('🖥️  Browser error:', text)
      } else if (text.includes('[Kuzu]')) {
        console.log('🖥️  Browser:', text)
      }
    })
    
    // Handle page errors
    page.on('pageerror', (error) => {
      console.error('❌ Page error:', error.message)
    })
    
    // Step 3: Navigate to application
    console.log(`🔗 Navigating to ${TEST_CONFIG.url}...`)
    await page.goto(TEST_CONFIG.url, { 
      waitUntil: 'networkidle',
      timeout: 10000 
    })
    
    // Step 4: Wait for React app to render
    console.log('⚛️  Waiting for React app to render...')
    await page.waitForSelector('h1', { timeout: 10000 })
    
    // Step 5: Wait for Kuzu initialization and ping response
    console.log('🔍 Waiting for Kuzu ping response...')
    
    // Check current page content
    const currentContent = await page.textContent('body')
    console.log('📄 Current page content preview:', currentContent.substring(0, 200) + '...')
    
    // Wait for the expected ping response to appear
    const success = await waitForTextContent(
      page, 
      'p', // Look in paragraph elements where status is displayed
      TEST_CONFIG.expectedResponse,
      TEST_CONFIG.timeout
    )
    
    if (success) {
      // Get the final status text for verification
      const statusElement = await page.locator('p').first()
      const statusText = await statusElement.textContent()
      console.log('📊 Final status:', statusText)
      
      console.log('🎉 Test PASSED!')
      console.log('✅ Kuzu WASM successfully initialized')
      console.log('✅ Ping query executed successfully')
      console.log('✅ Expected response verified:', TEST_CONFIG.expectedResponse)
      return true
    } else {
      // Get current page content for debugging
      const finalContent = await page.textContent('body')
      console.log('❌ Final page content:', finalContent)
      
      console.log('❌ Test FAILED!')
      console.log('❌ Expected response not found:', TEST_CONFIG.expectedResponse)
      return false
    }
    
  } catch (error) {
    console.error('💥 Test execution error:', error.message)
    console.error('Stack trace:', error.stack)
    return false
  }
}

/**
 * Cleanup resources
 */
async function cleanup() {
  console.log('🧹 Cleaning up...')
  
  if (browser) {
    await browser.close()
    browser = null
    console.log('🌐 Browser closed')
  }
  
  stopViteServer()
  
  // Give processes time to clean up
  await delay(1000)
}

/**
 * Main execution
 */
async function main() {
  let success = false
  
  // Handle process termination
  process.on('SIGINT', async () => {
    console.log('\n⚠️  Received SIGINT, cleaning up...')
    await cleanup()
    process.exit(1)
  })
  
  process.on('SIGTERM', async () => {
    console.log('\n⚠️  Received SIGTERM, cleaning up...')
    await cleanup()
    process.exit(1)
  })
  
  try {
    success = await runE2ETest()
  } catch (error) {
    console.error('💥 Unhandled error:', error)
  } finally {
    await cleanup()
  }
  
  // Exit with appropriate code
  console.log('=' .repeat(50))
  if (success) {
    console.log('🎉 E2E Test completed successfully!')
    process.exit(0)
  } else {
    console.log('❌ E2E Test failed!')
    process.exit(1)
  }
}

// Only run if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('💥 Fatal error:', error)
    process.exit(1)
  })
}

export { runE2ETest, TEST_CONFIG }