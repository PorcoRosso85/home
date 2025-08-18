#!/usr/bin/env node
/**
 * Node.js direct test (no browser)
 * Tests the modularized code directly
 */

import { executePingUseCase } from './application.js'

async function testDirect() {
  console.log('🧪 Direct Node.js Test')
  console.log('====================')
  
  try {
    const result = await executePingUseCase()
    console.log('Result:', result)
    
    if (result.success && result.message.includes('[{"response":"pong","status":1}]')) {
      console.log('✅ Test PASSED!')
      process.exit(0)
    } else {
      console.log('❌ Test FAILED!')
      console.log('Expected: [{"response":"pong","status":1}]')
      process.exit(1)
    }
  } catch (error) {
    console.error('💥 Test error:', error)
    process.exit(1)
  }
}

testDirect()