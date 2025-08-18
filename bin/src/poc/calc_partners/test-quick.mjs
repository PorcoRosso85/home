#!/usr/bin/env node
/**
 * Quick test to verify refactored modules work
 */

import puppeteer from 'puppeteer'

async function quickTest() {
  console.log('🧪 Quick Test: Starting...')
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  })
  
  const page = await browser.newPage()
  
  // Navigate to local server (assuming it's running)
  await page.goto('http://localhost:3000', { 
    waitUntil: 'networkidle0',
    timeout: 10000 
  })
  
  // Wait for status update
  await page.waitForFunction(
    () => {
      const status = document.querySelector('p')?.textContent || ''
      return status.includes('ping確認OK') || status.includes('エラー')
    },
    { timeout: 10000 }
  )
  
  // Get the status
  const status = await page.$eval('p', el => el.textContent)
  console.log('📊 Status:', status)
  
  if (status.includes('[{"response":"pong","status":1}]')) {
    console.log('✅ Test PASSED!')
  } else {
    console.log('❌ Test FAILED!')
    console.log('Expected: [{"response":"pong","status":1}]')
  }
  
  await browser.close()
}

quickTest().catch(console.error)