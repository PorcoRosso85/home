#!/usr/bin/env node
/**
 * Migration test for switchover capability
 * 
 * This test verifies that the USE_LEGACY environment variable works correctly
 * and that both implementations produce compatible output formats.
 */

import { test, describe } from 'node:test'
import { strict as assert } from 'node:assert'
import { spawn } from 'child_process'
import { join } from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = join(__dirname, '..')
const switchoverScript = join(projectRoot, 'scripts/switchover.mjs')

interface ScrapedResult {
  source: string
  company_name: string | null
  title: string
  url: string
  scraped_at: string
}

/**
 * Run the switchover script and capture output
 */
async function runSwitchover(useLegacy: boolean, timeout: number = 60000): Promise<{
  code: number
  stdout: string
  stderr: string
}> {
  return new Promise((resolve, reject) => {
    const env = {
      ...process.env,
      ...(useLegacy ? { USE_LEGACY: 'true' } : {})
    }

    const child = spawn('node', [switchoverScript], {
      cwd: projectRoot,
      env,
      timeout
    })

    let stdout = ''
    let stderr = ''

    child.stdout?.on('data', (data) => {
      stdout += data.toString()
    })

    child.stderr?.on('data', (data) => {
      stderr += data.toString()
    })

    child.on('close', (code) => {
      resolve({ code: code ?? 0, stdout, stderr })
    })

    child.on('error', (error) => {
      reject(error)
    })

    // Handle timeout
    setTimeout(() => {
      child.kill('SIGTERM')
      reject(new Error(`Process timed out after ${timeout}ms`))
    }, timeout)
  })
}

/**
 * Extract JSON results from stdout
 */
function extractJsonResults(stdout: string): ScrapedResult[] | null {
  try {
    // Look for JSON array in the output
    const lines = stdout.split('\n')
    let jsonStart = -1
    let jsonEnd = -1
    
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().startsWith('[')) {
        jsonStart = i
      }
      if (jsonStart !== -1 && lines[i].trim().endsWith(']')) {
        jsonEnd = i
        break
      }
    }

    if (jsonStart === -1 || jsonEnd === -1) {
      return null
    }

    const jsonText = lines.slice(jsonStart, jsonEnd + 1).join('\n')
    return JSON.parse(jsonText) as ScrapedResult[]
  } catch (error) {
    return null
  }
}

describe('Migration Switchover Tests', () => {
  test('switchover script exists and is executable', async () => {
    const result = await runSwitchover(false, 5000)
    
    // Should not fail immediately (process should start)
    assert.notEqual(result.code, 127, 'Switchover script should be found and executable')
  })

  test('USE_LEGACY=true uses legacy implementation', async () => {
    const result = await runSwitchover(true, 10000)
    
    // Check that output indicates legacy implementation
    assert.ok(
      result.stdout.includes('Legacy (scrape.mjs)') || 
      result.stderr.includes('Legacy (scrape.mjs)'),
      'Output should indicate legacy implementation is being used'
    )
  })

  test('default (no USE_LEGACY) uses TypeScript implementation', async () => {
    const result = await runSwitchover(false, 10000)
    
    // Check that output indicates TypeScript implementation
    assert.ok(
      result.stdout.includes('TypeScript (src/main.ts)') || 
      result.stderr.includes('TypeScript (src/main.ts)'),
      'Output should indicate TypeScript implementation is being used'
    )
  })

  test('both implementations should produce valid JSON output format', async (t) => {
    // This test is more comprehensive but has longer timeout
    t.timeout = 120000 // 2 minutes

    // Skip if we don't have network access or want fast tests
    if (process.env.SKIP_NETWORK_TESTS === 'true') {
      t.skip('Skipping network tests')
      return
    }

    // Test legacy implementation
    console.log('🧪 Testing legacy implementation...')
    const legacyResult = await runSwitchover(true, 90000)
    const legacyJson = extractJsonResults(legacyResult.stdout)

    // Test TypeScript implementation  
    console.log('🧪 Testing TypeScript implementation...')
    const tsResult = await runSwitchover(false, 90000)
    const tsJson = extractJsonResults(tsResult.stdout)

    // Both should produce valid JSON
    if (legacyJson) {
      assert.ok(Array.isArray(legacyJson), 'Legacy implementation should produce JSON array')
      if (legacyJson.length > 0) {
        assert.ok('source' in legacyJson[0], 'Legacy results should have source field')
        assert.ok('title' in legacyJson[0], 'Legacy results should have title field')
        assert.ok('url' in legacyJson[0], 'Legacy results should have url field')
        assert.ok('scraped_at' in legacyJson[0], 'Legacy results should have scraped_at field')
      }
    }

    if (tsJson) {
      assert.ok(Array.isArray(tsJson), 'TypeScript implementation should produce JSON array')
      if (tsJson.length > 0) {
        assert.ok('source' in tsJson[0], 'TypeScript results should have source field')
        assert.ok('title' in tsJson[0], 'TypeScript results should have title field')
        assert.ok('url' in tsJson[0], 'TypeScript results should have url field')
        assert.ok('scraped_at' in tsJson[0], 'TypeScript results should have scraped_at field')
      }
    }

    // If both succeeded, compare structure
    if (legacyJson && tsJson && legacyJson.length > 0 && tsJson.length > 0) {
      const legacyKeys = Object.keys(legacyJson[0]).sort()
      const tsKeys = Object.keys(tsJson[0]).sort()
      
      assert.deepEqual(
        legacyKeys,
        tsKeys,
        'Both implementations should produce the same JSON structure'
      )
    }
  })

  test('environment variable propagation works correctly', async () => {
    // Test that custom environment variables are passed through
    const result = await runSwitchover(true, 5000)
    
    // Should show USE_LEGACY=true in the output
    assert.ok(
      result.stdout.includes('USE_LEGACY=true') || 
      result.stderr.includes('USE_LEGACY=true'),
      'Environment variable should be visible in output'
    )
  })
})

// Run the tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🧪 Running migration tests...')
  console.log('   Set SKIP_NETWORK_TESTS=true to skip network-dependent tests')
  console.log('==================================================')
}