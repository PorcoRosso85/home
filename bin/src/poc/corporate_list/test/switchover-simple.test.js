#!/usr/bin/env node
/**
 * Simple switchover test that doesn't require network access
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

/**
 * Run a command and capture its initial output
 */
async function runCommandBriefly(command, args, env = {}, timeout = 3000) {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd: projectRoot,
      env: { ...process.env, ...env }
    })

    let stdout = ''
    let stderr = ''

    child.stdout?.on('data', (data) => {
      stdout += data.toString()
    })

    child.stderr?.on('data', (data) => {
      stderr += data.toString()
    })

    // Kill the process after timeout
    const timer = setTimeout(() => {
      child.kill('SIGTERM')
    }, timeout)

    child.on('close', (code) => {
      clearTimeout(timer)
      resolve({ code, stdout, stderr })
    })

    child.on('error', (error) => {
      clearTimeout(timer)
      resolve({ code: -1, stdout, stderr: error.message })
    })
  })
}

describe('Simple Switchover Tests', () => {
  test('switchover script shows TypeScript implementation by default', async () => {
    const result = await runCommandBriefly('node', ['scripts/switchover.mjs'], {})
    
    const output = result.stdout + result.stderr
    assert.ok(
      output.includes('TypeScript (src/main.ts)'),
      'Should indicate TypeScript implementation by default'
    )
    assert.ok(
      output.includes('USE_LEGACY=undefined'),
      'Should show USE_LEGACY as undefined when not set'
    )
  })

  test('switchover script shows Legacy implementation when USE_LEGACY=true', async () => {
    const result = await runCommandBriefly('node', ['scripts/switchover.mjs'], { USE_LEGACY: 'true' })
    
    const output = result.stdout + result.stderr
    assert.ok(
      output.includes('Legacy (scrape.mjs)'),
      'Should indicate legacy implementation when USE_LEGACY=true'
    )
    assert.ok(
      output.includes('USE_LEGACY=true'),
      'Should show USE_LEGACY=true in output'
    )
  })

  test('npm run scrape uses switchover script', async () => {
    // This test just checks that npm run scrape starts the switchover
    const result = await runCommandBriefly('npm', ['run', 'scrape'], {})
    
    const output = result.stdout + result.stderr
    assert.ok(
      output.includes('Corporate List Scraper Switchover') || output.includes('Starting Lead Scraper'),
      'Should start the switchover script or the actual scraper'
    )
  })

  test('npm scripts exist for both implementations', async () => {
    // Check package.json has the required scripts
    const packageJson = await import(join(projectRoot, 'package.json'), { with: { type: 'json' } })
    const scripts = packageJson.default.scripts

    assert.ok('scrape' in scripts, 'Should have scrape script')
    assert.ok('scrape:legacy' in scripts, 'Should have scrape:legacy script')
    assert.ok('scrape:ts' in scripts, 'Should have scrape:ts script')
    assert.ok('test:migration' in scripts, 'Should have test:migration script')
    
    // Verify the scrape script points to switchover
    assert.ok(scripts.scrape.includes('switchover.mjs'), 'scrape script should use switchover.mjs')
  })
})

// Run the tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🧪 Running simple switchover tests...')
}